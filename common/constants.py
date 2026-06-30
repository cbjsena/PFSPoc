# common/constants.py

# ==========================================
# Simulation Status
# ==========================================
SIMULATION_STATUS_PENDING = "PENDING"
SIMULATION_STATUS_RUNNING = "RUNNING"
SIMULATION_STATUS_SUCCESS = "SUCCESS"
SIMULATION_STATUS_FAILED = "FAILED"
SIMULATION_STATUS_CANCELED = "CANCELED"

SIMULATION_STATUS_CHOICES = [
    (SIMULATION_STATUS_PENDING, "Pending"),
    (SIMULATION_STATUS_RUNNING, "Running"),
    (SIMULATION_STATUS_SUCCESS, "Success"),
    (SIMULATION_STATUS_FAILED, "Failed"),
    (SIMULATION_STATUS_CANCELED, "Canceled"),
]

# ==========================================
# Mock Engine Configuration
# ==========================================
MOCK_ENGINE_STEP_INTERVAL_SEC = 6  # 각 단계 간격 (초)
MOCK_ENGINE_STEP_INCREMENT = 10  # 단계당 진행률 증가분 (%)
MOCK_ENGINE_TOTAL_STEPS = 10  # 총 단계 수 (10 × 10% = 100%)

# ==========================================
# Instance / Algorithm / Output Paths
# ==========================================
METADATA_FILENAME = "metadata.csv"
SOLVER_FILENAME = "solver.py"
SOLVER_FUNCTION_NAME = "algorithm"
INSTANCE_SEPARATOR = "~"  # 하위 폴더 구분자 (toy_v2~000_base)

# ==========================================
# Default Data Loader 테이블 순서 정의
# 숫자가 작을수록 먼저 실행됨 (의존성 관리)
# ==========================================
# 1) 삭제 순서 (자식 테이블 -> 부모 테이블)
DEFAULT_DELETE_ORDER = {
    "default_current_proforma_detail": 1,
    "default_proforma_essential_port": 1,  # 새로 추가된 Child 모델
    "default_berth_window_status": 2,
    "default_rdr_demand": 2,
    "default_current_proforma": 3,  # 가장 부모 모델이므로 마지막에 삭제
}

MASTER_DELETE_ORDER = {
    "master_lane": 1,
    "master_trade": 2,
    "master_port": 3,
}

# 2) 생성(Load) 순서 (부모 테이블 -> 자식 테이블)
MASTER_LOAD_ORDER = {
    "master_port": 1,
    "master_trade": 2,
    "master_lane": 3,
}

DEFAULT_LOAD_ORDER = {
    "default_current_proforma": 1,  # 가장 부모 모델이므로 먼저 생성
    "default_proforma_essential_port": 2,  # 새로 추가된 Child 모델
    "default_berth_window_status": 2,
    "default_rdr_demand": 2,
    "default_current_proforma_detail": 3,
}
