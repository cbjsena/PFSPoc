"""
Django tests for simulation models
Corresponds to test scenarios: SIM_NUM_GEN_*, and model-level validations
"""

from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date

from simulation.models import SimulationRun, SimulationProforma
from input.models import MasterTrade, MasterLane


class SimulationRunModelTests(TestCase):
    """SimulationRun 모델 테스트"""
    
    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(username='test_user', password='pass123')
    
    # SIM_NUM_GEN_001: Simulation Number 형식 검증
    def test_sim_num_gen_001_simulation_number_format(self):
        """simulation_number 필드가 YYYYMMDD_NN-XX 형식으로 저장되는지 검증"""
        sim = SimulationRun.objects.create(
            simulation_number='20260630_01-01',
            status='PENDING',
            created_by=self.user
        )
        
        self.assertEqual(sim.simulation_number, '20260630_01-01')
        # 형식 검증
        import re
        pattern = r'^\d{8}_\d{2}-\d{2}$'
        self.assertIsNotNone(re.match(pattern, sim.simulation_number))
    
    # SIM_NUM_GEN_002: simulation_number 고유성
    def test_sim_num_gen_002_simulation_number_uniqueness(self):
        """simulation_number 필드의 unique 제약 검증"""
        SimulationRun.objects.create(
            simulation_number='20260630_01-01',
            status='PENDING',
            created_by=self.user
        )
        
        # 동일한 simulation_number로 생성 시 에러 발생
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SimulationRun.objects.create(
                simulation_number='20260630_01-01',
                status='PENDING',
                created_by=self.user
            )
    
    def test_base_simulation_number_self_referential(self):
        """base_simulation_number 자기 참조 테스트"""
        # 최상위 시뮬레이션
        parent_sim = SimulationRun.objects.create(
            simulation_number='20260630_01-01',
            status='PENDING',
            base_simulation_number=None,
            created_by=self.user
        )
        
        # 하위 시뮬레이션
        child_sim = SimulationRun.objects.create(
            simulation_number='20260630_01-02',
            status='PENDING',
            base_simulation_number=parent_sim,
            created_by=self.user
        )
        
        self.assertEqual(child_sim.base_simulation_number, parent_sim)
        self.assertIsNone(parent_sim.base_simulation_number)
    
    def test_simulation_status_choices(self):
        """시뮬레이션 상태 선택지 검증"""
        valid_statuses = ['PENDING', 'RUNNING', 'SUCCESS', 'FAILED']
        
        for status in valid_statuses:
            sim = SimulationRun.objects.create(
                simulation_number=f'20260630_{valid_statuses.index(status)+1:02d}-01',
                status=status,
                created_by=self.user
            )
            self.assertEqual(sim.status, status)
    
    def test_simulation_properties(self):
        """SimulationRun 프로퍼티 메서드 검증"""
        # is_running 프로퍼티
        running_sim = SimulationRun.objects.create(
            simulation_number='20260630_01-01',
            status='RUNNING',
            created_by=self.user
        )
        self.assertTrue(running_sim.is_running)
        
        # is_success 프로퍼티
        success_sim = SimulationRun.objects.create(
            simulation_number='20260630_02-01',
            status='SUCCESS',
            created_by=self.user
        )
        self.assertTrue(success_sim.is_success)
        
        # is_processing 프로퍼티
        pending_sim = SimulationRun.objects.create(
            simulation_number='20260630_03-01',
            status='PENDING',
            created_by=self.user
        )
        self.assertTrue(pending_sim.is_processing)


class SimulationProformaModelTests(TestCase):
    """SimulationProforma 모델 테스트"""
    
    def setUp(self):
        """테스트 데이터 설정"""
        self.user = User.objects.create_user(username='test_user', password='pass123')
        self.sim = SimulationRun.objects.create(
            simulation_number='20260630_01-01',
            status='PENDING',
            created_by=self.user
        )
        
        # Master 데이터 생성
        self.trade = MasterTrade.objects.create(
            trade_code='A1',
            trade_name='Asia Export'
        )
        self.lane = MasterLane.objects.create(
            lane_code='AE01',
            lane_name='Asia-Europe 01'
        )
    
    def test_simulation_proforma_creation(self):
        """SimulationProforma 생성"""
        proforma = SimulationProforma.objects.create(
            simulation=self.sim,
            trade=self.trade,
            lane=self.lane,
            capacity=1000,
            qty=500
        )
        
        self.assertEqual(proforma.simulation, self.sim)
        self.assertEqual(proforma.trade.trade_code, 'A1')
        self.assertEqual(proforma.lane.lane_code, 'AE01')
        self.assertEqual(proforma.capacity, 1000)
        self.assertEqual(proforma.qty, 500)
    
    def test_simulation_proforma_cascade_delete(self):
        """SimulationRun 삭제 시 SimulationProforma 자동 삭제"""
        SimulationProforma.objects.create(
            simulation=self.sim,
            trade=self.trade,
            lane=self.lane,
            capacity=1000,
            qty=500
        )
        
        sim_id = self.sim.id
        self.sim.delete()
        
        # SimulationProforma도 삭제되었는지 확인
        self.assertEqual(SimulationProforma.objects.filter(simulation_id=sim_id).count(), 0)
    
    def test_simulation_proforma_unique_constraint(self):
        """Simulation + Trade + Lane 고유성 제약"""
        SimulationProforma.objects.create(
            simulation=self.sim,
            trade=self.trade,
            lane=self.lane,
            capacity=1000,
            qty=500
        )
        
        # 동일한 조합으로 생성 시 에러
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SimulationProforma.objects.create(
                simulation=self.sim,
                trade=self.trade,
                lane=self.lane,
                capacity=2000,
                qty=1000
            )
    
    def test_simulation_proforma_optional_fields(self):
        """Capacity/Qty 선택사항"""
        proforma = SimulationProforma.objects.create(
            simulation=self.sim,
            trade=self.trade,
            lane=self.lane,
            capacity=None,
            qty=None
        )
        
        self.assertIsNone(proforma.capacity)
        self.assertIsNone(proforma.qty)
    
    def test_simulation_proforma_foreign_key_protect(self):
        """Trade/Lane DELETE 시 PROTECT 제약"""
        SimulationProforma.objects.create(
            simulation=self.sim,
            trade=self.trade,
            lane=self.lane,
            capacity=1000,
            qty=500
        )
        
        # Trade 삭제 시 오류 발생
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.trade.delete()


class SimulationNumberGenerationServiceTests(TestCase):
    """Simulation Number 생성 서비스 테스트"""
    
    # SIM_NUM_GEN_001: 신규 번호 생성
    def test_simulation_number_first_creation_today(self):
        """오늘 첫 번째 시뮬레이션 번호 생성"""
        from simulation.views import generate_simulation_number
        
        today = date.today().strftime("%Y%m%d")
        sim_num = generate_simulation_number()
        
        # 형식: YYYYMMDD_01-01
        self.assertTrue(sim_num.startswith(f'{today}_01'))
        self.assertTrue(sim_num.endswith('-01'))
    
    # SIM_NUM_GEN_002: 순차 번호 증가
    def test_simulation_number_sequential_increment(self):
        """같은 날짜 내 순차 번호 증가"""
        from simulation.views import generate_simulation_number
        
        user = User.objects.create_user(username='test_user', password='pass123')
        
        # 첫 번째 시뮬레이션 생성
        sim1_num = generate_simulation_number()
        sim1 = SimulationRun.objects.create(
            simulation_number=sim1_num,
            status='PENDING',
            created_by=user,
            base_simulation_number=None
        )
        
        # 두 번째 시뮬레이션 생성
        sim2_num = generate_simulation_number()
        sim2 = SimulationRun.objects.create(
            simulation_number=sim2_num,
            status='PENDING',
            created_by=user,
            base_simulation_number=None
        )
        
        today = date.today().strftime("%Y%m%d")
        
        # 형식 확인
        self.assertTrue(sim1_num.startswith(f'{today}_01'))
        self.assertTrue(sim2_num.startswith(f'{today}_02'))
    
    def test_simulation_number_top_level_only(self):
        """base_simulation_number가 None인 것만 카운트"""
        from simulation.views import generate_simulation_number
        
        user = User.objects.create_user(username='test_user', password='pass123')
        today = date.today().strftime("%Y%m%d")
        
        # 최상위 시뮬레이션
        parent = SimulationRun.objects.create(
            simulation_number=f'{today}_01-01',
            status='PENDING',
            created_by=user,
            base_simulation_number=None
        )
        
        # 하위 시뮬레이션 (카운트 안됨)
        child = SimulationRun.objects.create(
            simulation_number=f'{today}_01-02',
            status='PENDING',
            created_by=user,
            base_simulation_number=parent
        )
        
        # 다음 생성 번호는 _02-01이어야 함 (하위는 카운트 안됨)
        next_sim_num = generate_simulation_number()
        self.assertTrue(next_sim_num.startswith(f'{today}_02'))
