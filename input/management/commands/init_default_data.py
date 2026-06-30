import os

from django.apps import apps
from django.db.models import ProtectedError

from common import messages as msg
from common.constants import (
    DEFAULT_DELETE_ORDER,
    DEFAULT_LOAD_ORDER,
    MASTER_DELETE_ORDER,
    MASTER_LOAD_ORDER,
)

from ._base_loader import DefaultDataLoader


class Command(DefaultDataLoader):
    help = "Load default table data from CSV files."

    def handle(self, *args, **kwargs):
        self._fk_cache = {}

        default_data_dir = self.get_default_data_dir()
        if not default_data_dir:
            return

        if not os.path.exists(default_data_dir):
            self.stdout.write(self.style.ERROR(msg.DIR_NOT_FOUND.format(path=default_data_dir)))
            return

        app_config = apps.get_app_config("input")

        # Master 또는 Default로 시작하는 모델 필터링
        target_models = [
            m
            for m in app_config.get_models()
            if m._meta.db_table.startswith("master_") or m._meta.db_table.startswith("default_")
        ]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "[init_default_data] Loading default tables from CSV files in {}"
            )
        )

        try:
            # 1. 기존 데이터 삭제 (역순으로 FK 의존성 고려)
            self.delete_models_with_order(target_models)

            # 2. 새로운 데이터 로드 (순서대로 FK 의존성 고려)
            self.load_models_with_order(target_models, default_data_dir)

        except ProtectedError:
            # 💡 마스터 데이터를 참조하는 시뮬레이션 데이터가 있을 때 발생하는 에러 핸들링
            self.stdout.write(
                self.style.ERROR(
                    "\n🚨 [데이터 초기화 실패] 외래키(PROTECT) 제약 조건 에러\n"
                    "원인: 마스터 데이터(MasterLane 등)를 삭제하려고 했으나, "
                    "시뮬레이션 앱(SimulationRun 등)에서 해당 마스터 데이터를 참조하고 있습니다.\n"
                    "해결방법: DBeaver에서 시뮬레이션 데이터(simulation_run 테이블)를"
                    " 먼저 모두 삭제한 뒤 다시 실행해 주세요.\n"
                )
            )

    def delete_models_with_order(self, models_to_delete):
        """FK 의존성을 고려하여 역순으로 데이터 삭제"""

        # Default 테이블 먼저 삭제
        default_models = [m for m in models_to_delete if m._meta.db_table.startswith("default_")]
        default_models.sort(key=lambda m: DEFAULT_DELETE_ORDER.get(m._meta.db_table, 999))
        self.delete_models(default_models)

        # Master 테이블 나중에 삭제
        master_models = [m for m in models_to_delete if m._meta.db_table.startswith("master_")]
        master_models.sort(key=lambda m: MASTER_DELETE_ORDER.get(m._meta.db_table, 999))
        self.delete_models(master_models)

    def load_models_with_order(self, models_to_load, base_data_dir):
        """의존성을 고려하여 모델을 순서대로 로드"""

        # Master 테이블 먼저 로드
        master_models = [m for m in models_to_load if m._meta.db_table.startswith("master_")]
        master_models.sort(key=lambda m: MASTER_LOAD_ORDER.get(m._meta.db_table, 999))

        for model in master_models:
            self.load_model_safe(model, base_data_dir)

        # Default 테이블 나중에 로드
        default_models = [m for m in models_to_load if m._meta.db_table.startswith("default_")]
        default_models.sort(key=lambda m: DEFAULT_LOAD_ORDER.get(m._meta.db_table, 999))

        for model in default_models:
            self.load_model_safe(model, base_data_dir)

    def load_model_safe(self, model, base_data_dir):
        """개별 모델을 안전하게 로드"""
        table_name = model._meta.db_table
        file_name = f"{table_name}.csv"
        file_path = os.path.join(base_data_dir, file_name)

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.WARNING(msg.FILE_NOT_FOUND.format(table=table_name, file=file_name))
            )
            return

        self.load_data(model, file_path)
