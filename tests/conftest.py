from datetime import date

import pytest
from django.contrib.auth.models import User
from django.test import Client

from input.models import DefaultCurrentProforma, MasterLane, MasterPort, MasterTrade
from simulation.models import SimulationProforma, SimulationRun


@pytest.fixture
def base_data_dir(tmp_path, settings):
    """Fixture that sets BASE_DIR to a temporary path and returns it."""
    settings.BASE_DIR = tmp_path
    return tmp_path


# ===== User Fixtures =====


@pytest.fixture
def test_user(db):
    """기본 테스트 사용자 생성"""
    return User.objects.create_user(
        username="test_user", email="test@example.com", password="pass123"
    )


@pytest.fixture
def user_a(db):
    """테스트 사용자 A"""
    return User.objects.create_user(
        username="user_a", email="user_a@example.com", password="pass123"
    )


@pytest.fixture
def user_b(db):
    """테스트 사용자 B"""
    return User.objects.create_user(
        username="user_b", email="user_b@example.com", password="pass123"
    )


# ===== Master Data Fixtures =====


@pytest.fixture
def master_trade(db):
    """마스터 Trade 데이터"""
    return MasterTrade.objects.create(trade_code="A1", trade_name="Asia Export")


@pytest.fixture
def master_lane(db):
    """마스터 Lane 데이터"""
    return MasterLane.objects.create(lane_code="AE01", lane_name="Asia-Europe 01")


@pytest.fixture
def master_trades(db):
    """여러 마스터 Trade 데이터"""
    trades = []
    for i in range(1, 4):
        trades.append(MasterTrade.objects.create(trade_code=f"T{i}", trade_name=f"Trade {i}"))
    return trades


@pytest.fixture
def master_lanes(db):
    """여러 마스터 Lane 데이터"""
    lanes = []
    for i in range(1, 4):
        lanes.append(MasterLane.objects.create(lane_code=f"L{i:02d}", lane_name=f"Lane {i}"))
    return lanes


@pytest.fixture
def master_ports(db):
    """마스터 Port 데이터"""
    ports = []
    for i in range(1, 11):
        ports.append(MasterPort.objects.create(port_code=f"P{i:03d}", port_name=f"Port {i}"))
    return ports


# ===== DefaultCurrentProforma Fixtures =====


@pytest.fixture
def default_proforma(db, master_trade, master_lane):
    """기본 DefaultCurrentProforma 데이터"""
    return DefaultCurrentProforma.objects.create(
        trade=master_trade, lane=master_lane, capacity=1000, qty=500
    )


@pytest.fixture
def default_proformas(db, master_trades, master_lanes):
    """여러 DefaultCurrentProforma 데이터"""
    proformas = []
    for i, (trade, lane) in enumerate(zip(master_trades, master_lanes)):
        proformas.append(
            DefaultCurrentProforma.objects.create(
                trade=trade, lane=lane, capacity=(i + 1) * 1000, qty=(i + 1) * 500
            )
        )
    return proformas


# ===== SimulationRun Fixtures =====


@pytest.fixture
def simulation_run(db, test_user):
    """기본 SimulationRun 데이터"""
    today = date.today().strftime("%Y%m%d")
    return SimulationRun.objects.create(
        simulation_number=f"{today}_01-01",
        status="PENDING",
        created_by=test_user,
        base_simulation_number=None,
    )


@pytest.fixture
def simulation_run_with_status(db, test_user):
    """상태별 SimulationRun 데이터"""
    today = date.today().strftime("%Y%m%d")
    simulations = {}

    statuses = ["PENDING", "RUNNING", "SUCCESS", "FAILED"]
    for idx, status in enumerate(statuses, 1):
        simulations[status] = SimulationRun.objects.create(
            simulation_number=f"{today}_{idx:02d}-01",
            status=status,
            created_by=test_user,
            base_simulation_number=None,
        )

    return simulations


@pytest.fixture
def simulation_runs_by_user(db, user_a, user_b):
    """사용자별 SimulationRun 데이터"""
    today = date.today().strftime("%Y%m%d")

    # User A: 5개 시뮬레이션
    user_a_sims = []
    for i in range(1, 6):
        user_a_sims.append(
            SimulationRun.objects.create(
                simulation_number=f"{today}_{i:02d}-01",
                status="PENDING",
                created_by=user_a,
                base_simulation_number=None,
            )
        )

    # User B: 3개 시뮬레이션
    user_b_sims = []
    for i in range(6, 9):
        user_b_sims.append(
            SimulationRun.objects.create(
                simulation_number=f"{today}_{i:02d}-01",
                status="SUCCESS",
                created_by=user_b,
                base_simulation_number=None,
            )
        )

    return {"user_a": user_a_sims, "user_b": user_b_sims}


# ===== SimulationProforma Fixtures =====


@pytest.fixture
def simulation_proforma(db, simulation_run, master_trade, master_lane):
    """기본 SimulationProforma 데이터"""
    return SimulationProforma.objects.create(
        simulation=simulation_run, trade=master_trade, lane=master_lane, capacity=1000, qty=500
    )


@pytest.fixture
def simulation_proformas(db, simulation_run, master_trades, master_lanes):
    """여러 SimulationProforma 데이터"""
    proformas = []
    for trade, lane in zip(master_trades, master_lanes):
        proformas.append(
            SimulationProforma.objects.create(
                simulation=simulation_run, trade=trade, lane=lane, capacity=1000, qty=500
            )
        )
    return proformas


# ===== Utility Fixtures =====


@pytest.fixture
def api_client():
    """Django 테스트 Client"""
    return Client()


@pytest.fixture
def today_string():
    """오늘 날짜 YYYYMMDD 형식"""
    return date.today().strftime("%Y%m%d")


@pytest.fixture
def valid_row_data(master_trade, master_lane):
    """유효한 행 데이터 (POST 용)"""
    return {
        "trade": master_trade.trade_code,
        "lane": master_lane.lane_code,
        "capacity": 1000,
        "qty": 500,
        "essentials": ["P001", "P002", "", "", ""],
    }


@pytest.fixture
def valid_rows_data(master_trades, master_lanes):
    """여러 유효한 행 데이터"""
    rows = []
    for trade, lane in zip(master_trades, master_lanes):
        rows.append(
            {
                "trade": trade.trade_code,
                "lane": lane.lane_code,
                "capacity": 1000,
                "qty": 500,
                "essentials": ["P001", "", "", "", ""],
            }
        )
    return rows


@pytest.fixture
def invalid_row_data():
    """유효하지 않은 행 데이터"""
    return {
        "trade": "INVALID_TRADE",
        "lane": "INVALID_LANE",
        "capacity": "abc",  # 정수 아님
        "qty": None,
    }
