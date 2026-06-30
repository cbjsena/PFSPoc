# common/utils/date_utils.py
from datetime import datetime


def now_str(fmt="%Y%m%d_%H%M%S"):
    """현재 시각을 문자열로 반환 (outputs 폴더명 생성용)."""
    return datetime.now().strftime(fmt)


def parse_datetime_folder(folder_name):
    """'20260615_143022' 형태의 폴더명을 datetime 객체로 변환."""
    try:
        return datetime.strptime(folder_name, "%Y%m%d_%H%M%S")
    except ValueError:
        return None
