import pytest
from django.http import Http404

def test_format_time():
    # Scenario: IN_PF_SVC_003 (_format_time 다양한 입력 포맷 처리)
    from input import views
    assert views._format_time("900") == "15:00"
    assert views._format_time("09:30:00") == "09:30"
    assert views._format_time("") == ""


def test_parse_time_minutes():
    # Scenario: IN_PF_SVC_004 (_parse_time_minutes 정상/잘못된 입력)
    from input import views
    assert views._parse_time_minutes("09:30") == 9 * 60 + 30
    assert views._parse_time_minutes("90") == 90
    assert views._parse_time_minutes("bad") is None


def test_calc_duration_normal_and_week_wrap():
    # Scenario: IN_PF_SVC_005 (_calc_duration 정상 및 주 경계 처리)
    from input import views
    detail = {"etb_day": "MON", "etb_time": "09:00", "etd_day": "TUE", "etd_time": "12:30"}
    assert views._calc_duration(detail) == "27h 30m"
    detail2 = {"etb_day": "FRI", "etb_time": "10:00", "etd_day": "THU", "etd_time": "09:00"}
    assert views._calc_duration(detail2) != ""


def test_read_csv_rows_raises_404_when_missing(tmp_path):
    # Scenario: IN_PF_SVC_002 (_read_csv_rows 파일 없음 처리)
    from input import views
    missing = tmp_path / "data" / "missing.csv"
    missing.parent.mkdir()
    with pytest.raises(Http404):
        views._read_csv_rows(missing)
