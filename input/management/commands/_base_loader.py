"""
공통 CSV → Django Model 로더 베이스 클래스.

init_default_data 커맨드가 이 클래스를 상속한다.
파일명이 '_'로 시작하므로 Django management command로 인식되지 않는다.
"""

import csv
import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dateutil import parser as date_parser
from tqdm import tqdm  # 진행 표시용

from common import messages as msg


class DefaultDataLoader(BaseCommand):
    """CSV 파일을 Django 모델에 로드하는 공통 기능을 제공하는 베이스 클래스"""

    # 서브클래스에서 재정의
    help = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fk_cache = {}

    def _get_fk_object(self, related_model, pk_val):
        """FK 참조 객체를 캐시에서 조회하거나, 없으면 단건 로드 후 캐시 (Lazy Loading)"""
        cache_key = related_model._meta.label
        pk_str = str(pk_val)

        # 1. 모델용 캐시 딕셔너리가 없으면 초기화
        if cache_key not in self._fk_cache:
            self._fk_cache[cache_key] = {}

        # 2. 캐시에 해당 PK가 없으면 DB에서 조회 후 캐싱
        if pk_str not in self._fk_cache[cache_key]:
            try:
                obj = related_model.objects.get(pk=pk_val)
                self._fk_cache[cache_key][pk_str] = obj
            except related_model.DoesNotExist:
                # DB에도 없으면 None을 캐싱하여 다음번 중복 조회 방지
                self._fk_cache[cache_key][pk_str] = None

        return self._fk_cache[cache_key][pk_str]

    def get_default_data_dir(self):
        """CSV 파일 기본 디렉토리 반환"""
        return os.path.join(settings.BASE_DIR, "data", "default_data")

    def delete_models(self, models_to_delete):
        """주어진 모델 목록의 데이터를 삭제한다."""
        for m in models_to_delete:
            count, _ = m.objects.all().delete()
            if count:
                self.stdout.write(
                    self.style.WARNING(
                        f"  -> Cleared {count} row(s) from {m._meta.db_table}"
                    )
                )

    def load_models(self, models_to_load, base_data_dir):
        """모델 목록을 순회하며 CSV 데이터를 로드한다."""
        for model in models_to_load:
            table_name = model._meta.db_table
            file_name = f"{table_name}.csv"
            file_path = os.path.join(base_data_dir, file_name)

            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(
                        msg.FILE_NOT_FOUND.format(table=table_name, file=file_name)
                    )
                )
                continue

            self.load_data(model, file_path)

    @transaction.atomic
    def load_data(self, model, file_path):
        """CSV 파일을 읽어 모델에 Bulk Insert"""
        table_name = model._meta.db_table
        self.stdout.write(
            self.style.MIGRATE_HEADING(msg.START_LOADING.format(table=table_name))
        )

        data_list = []
        total_count = 0

        # base_bunker_consumption_sea는 배치 크기를 5000으로 설정
        batch_size = 5000 if table_name == "base_bunker_consumption_sea" else 1000
        

        try:
            with open(file_path, encoding="utf-8-sig") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)  # 전체 행을 리스트로 변환하여 tqdm에 사용
                for i, row in enumerate(tqdm(rows, desc=table_name, unit="row")):
                    try:
                        cleaned_row = self.clean_row(model, row)
                        data_list.append(model(**cleaned_row))
                    except Exception as e:
                        error_message = msg.ROW_ERROR.format(
                            table=table_name, error=str(e)
                        )
                        detailed_message = f"{error_message} | ROW #{i + 1} DATA: {row}"
                        self.stdout.write(self.style.ERROR(detailed_message))

                    # 배치 크기에 도달하면 bulk_create
                    if len(data_list) >= batch_size:
                        model.objects.bulk_create(data_list)
                        total_count += len(data_list)
                        data_list = []

            # 남은 데이터 bulk_create
            if data_list:
                model.objects.bulk_create(data_list)
                total_count += len(data_list)

            if total_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        msg.DONE_LOADING.format(table=table_name, count=total_count)
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(msg.EMPTY_CSV.format(table=table_name))
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(msg.LOAD_FAIL.format(table=table_name, error=str(e)))
            )

    def clean_row(self, model, row):
        """CSV 값을 필드 타입에 맞춰 변환"""
        cleaned = {}
        for key, value in row.items():
            # 필드 찾기: 소문자로 변환하여 매칭 시도
            field = self._find_field_case_insensitive(model, key)
            
            if not field:
                # 불명확한 필드는 무시 (warning 출력하지 않음)
                continue

            val = value.strip() if isinstance(value, str) else value
            internal_type = field.get_internal_type()

            # FK 필드 처리
            if field.is_relation:
                related_model = field.related_model
                if val == "":
                    cleaned[field.name] = None
                else:
                    ref_obj = self._get_fk_object(related_model, val)
                    if ref_obj:
                        cleaned[field.name] = ref_obj
                    elif field.null:
                        cleaned[field.name] = None
                    else:
                        raise ValueError(
                            f"FK '{key}' references {related_model.__name__} "
                            f"with pk='{val}', but not found"
                        )
                continue

            # 빈 값 처리
            if val == "":
                if internal_type in [
                    "IntegerField",
                    "DecimalField",
                    "FloatField",
                    "BigIntegerField",
                ]:
                    cleaned[field.name] = None if field.null else 0
                else:
                    cleaned[field.name] = None if field.null else ""

            # 값이 있는 경우 - 타입별 변환
            else:
                try:
                    if internal_type in ["IntegerField", "BigIntegerField"]:
                        cleaned[field.name] = int(str(val).replace(",", ""))

                    elif internal_type == "DecimalField":
                        cleaned[field.name] = Decimal(str(val).replace(",", ""))

                    elif internal_type == "FloatField":
                        cleaned[field.name] = float(str(val).replace(",", ""))

                    elif internal_type in ["DateTimeField", "DateField"]:
                        dt = date_parser.parse(str(val))
                        cleaned[field.name] = (
                            timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                        )
                    else:
                        cleaned[field.name] = val
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        msg.INVALID_DATA_FORMAT.format(
                            column=key, internal_type=internal_type, value=val
                        )
                    ) from e

        return cleaned

    def _find_fk_field_by_column(self, model, column_name):
        """CSV 컬럼명(예: 'lane_code')으로 FK 필드를 찾는다."""
        for field in model._meta.get_fields():
            if hasattr(field, "attname") and field.attname == column_name:
                if field.is_relation:
                    return field
            if hasattr(field, "column") and field.column == column_name:
                if field.is_relation:
                    return field
        return None

    def _find_field_case_insensitive(self, model, column_name):
        """대소문자를 무시하고 모델의 필드를 찾는다."""
        column_lower = column_name.lower()
        
        # 1. 정확한 필드명 매칭 시도
        try:
            return model._meta.get_field(column_name)
        except Exception:
            pass
        
        # 2. 소문자로 비교하여 매칭 시도
        for field in model._meta.get_fields():
            if field.name.lower() == column_lower:
                return field
            # FK 필드의 경우 column 이름도 확인
            if hasattr(field, 'column') and field.column and field.column.lower() == column_lower:
                return field
            # attname도 확인 (e.g., 'trade_id' for ForeignKey)
            if hasattr(field, 'attname') and field.attname.lower() == column_lower:
                return field
        
        return None
