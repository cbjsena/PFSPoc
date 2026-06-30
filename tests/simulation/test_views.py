"""
Django pytest tests for simulation views
Corresponds to test scenarios: SIM_LST_*, SIM_PRT_DIS_*, SIM_PRT_VAL_*, SIM_PRT_API_*

Test fixtures are defined in tests/conftest.py
"""

import json

import pytest
from django.urls import reverse

from simulation.models import SimulationProforma, SimulationRun


@pytest.mark.django_db
class TestSimulationListView:
    """Simulation List 화면 테스트"""

    # SIM_LST_DIS_001: Simulation List 비로딩 (데이터 없음)
    def test_sim_lst_dis_001_empty_simulation_list(self, api_client):
        """데이터 없을 때 'No simulations found' 메시지 표시"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        assert "No simulations found" in response.content.decode()

    # SIM_LST_DIS_002: Simulation List 데이터 로딩
    def test_sim_lst_dis_002_load_simulation_list(self, api_client, simulation_runs_by_user):
        """여러 시뮬레이션 데이터 로드 및 표시"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        # 5 + 3 = 8개 시뮬레이션
        assert len(response.context["simulations"]) == 8
        assert "Status" in response.content.decode()
        assert "Created At" in response.content.decode()

    # SIM_LST_DIS_003: 상태 배지 표시
    def test_sim_lst_dis_003_status_badges(self, api_client, simulation_run_with_status):
        """상태별 배지 표시 검증"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Pending" in content
        assert "Running" in content
        assert "Success" in content
        assert "Failed" in content

    # SIM_LST_DIS_004: 사용자별 필터링
    def test_sim_lst_dis_004_filter_by_user(self, api_client, simulation_runs_by_user, user_a):
        """사용자별 필터링 동작"""
        response = api_client.get(
            reverse("simulation:simulation_list"), {"created_by_id": user_a.id}
        )

        assert response.status_code == 200
        # User A는 5개 시뮬레이션만 보여야 함
        assert len(response.context["simulations"]) == 5
        for sim in response.context["simulations"]:
            assert sim.created_by == user_a

    # SIM_LST_DIS_005: View 버튼 존재 확인
    def test_sim_lst_dis_005_view_button_exists(self, api_client, simulation_run):
        """View 버튼이 화면에 표시되는지 확인"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        assert "View" in response.content.decode()

    # SIM_LST_DIS_006: Restart 버튼으로 기존 시뮬레이션 로드
    def test_sim_lst_dis_006_restart_button_with_sim_id(self, api_client, simulation_run):
        """Restart 버튼으로 기존 시뮬레이션 로드"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        assert f"sim_id={simulation_run.id}" in response.content.decode()

    # SIM_LST_DIS_007: Delete 버튼 존재 확인
    def test_sim_lst_dis_007_delete_button_exists(self, api_client, simulation_run):
        """Delete 버튼이 화면에 표시되는지 확인"""
        response = api_client.get(reverse("simulation:simulation_list"))

        assert response.status_code == 200
        assert "Delete" in response.content.decode()

    # SIM_LST_API_001: AJAX DELETE 요청
    def test_sim_lst_api_001_delete_simulation_ajax(self, api_client, simulation_run):
        """AJAX POST로 시뮬레이션 삭제"""
        sim_id = simulation_run.id

        response = api_client.post(
            reverse("simulation:delete_simulation", kwargs={"sim_id": sim_id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        # DB에서 삭제 확인
        assert not SimulationRun.objects.filter(id=sim_id).exists()

    # SIM_LST_API_002: DELETE 오류 처리 (404)
    def test_sim_lst_api_002_delete_nonexistent_simulation(self, api_client):
        """존재하지 않는 시뮬레이션 삭제 요청 (404)"""
        response = api_client.post(
            reverse("simulation:delete_simulation", kwargs={"sim_id": 9999}),
            content_type="application/json",
        )

        assert response.status_code == 404
        data = json.loads(response.content)
        assert "error" in data


@pytest.mark.django_db
class TestPortCreationView:
    """Port Creation 화면 테스트"""

    # SIM_PRT_DIS_001: 새 시뮬레이션 생성
    def test_sim_prt_dis_001_new_simulation_creation(self, api_client, today_string):
        """새 Port Creation 시작 (sim_id 없음)"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        # 새 SimulationRun이 생성되었는지 확인
        assert SimulationRun.objects.count() == 1
        sim = SimulationRun.objects.first()
        assert sim.simulation_number is not None
        # simulation_number 형식 확인 (YYYYMMDD_NN-XX)
        assert sim.simulation_number.startswith(today_string)
        assert sim.simulation_number.endswith("-01")

    # SIM_PRT_DIS_002: 기존 시뮬레이션 로드
    def test_sim_prt_dis_002_load_existing_simulation(self, api_client, simulation_run):
        """기존 시뮬레이션 수정 (sim_id 있음)"""
        response = api_client.get(
            reverse("simulation:port_creation"), {"sim_id": simulation_run.id}
        )

        assert response.status_code == 200
        assert response.context["simulation_number"] == simulation_run.simulation_number

    # SIM_PRT_DIS_003: DefaultCurrentProforma 행 표시
    def test_sim_prt_dis_003_display_default_proforma_rows(self, api_client, default_proformas):
        """DefaultCurrentProforma 데이터 초기 표시"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        assert len(response.context["proformas"]) == 3
        proforma = response.context["proformas"][0]
        assert proforma.capacity == 1000
        assert proforma.qty == 500

    # SIM_PRT_DIS_004: Trade/Lane 비선택 확인
    def test_sim_prt_dis_004_trade_lane_non_editable(self, api_client, default_proforma):
        """초기 행의 Trade/Lane은 선택 불가 (plaintext)"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # Trade/Lane이 plaintext로 표시되는지 확인
        assert "form-control-plaintext" in content

    # SIM_PRT_DIS_005: Essentials 포트 입력 가능
    def test_sim_prt_dis_005_essentials_ports_input(self, api_client, default_proforma):
        """Essentials 포트 5개 컬럼 입력 가능"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # essentials 입력 필드 확인
        assert "essentials" in content

    # SIM_PRT_DIS_006: Insert Row 버튼
    def test_sim_prt_dis_006_insert_row_button(self, api_client, default_proforma):
        """Insert Row 버튼 존재 확인"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        assert "Insert Row" in response.content.decode()

    # SIM_PRT_DIS_007: Delete Row 버튼
    def test_sim_prt_dis_007_delete_row_button(self, api_client, default_proforma):
        """Delete Row 버튼 존재 확인"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        assert "Delete Row" in response.content.decode()

    # SIM_PRT_DIS_008: Select All 체크박스
    def test_sim_prt_dis_008_select_all_checkbox(self, api_client, default_proforma):
        """Select All 체크박스 존재 확인"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        assert "selectAll" in response.content.decode()

    # SIM_PRT_DIS_009: 가로 스크롤바 고정
    def test_sim_prt_dis_009_fixed_scrollbar(self, api_client, default_proforma):
        """가로 스크롤바 고정 CSS 확인"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # scroll-container-top 클래스와 sticky 스타일 확인
        assert "scroll-container-top" in content
        assert "position: sticky" in content

    # SIM_PRT_DIS_010: 버튼 위치 (우측 정렬)
    def test_sim_prt_dis_010_button_alignment(self, api_client, default_proforma):
        """버튼이 우측 정렬되는지 확인"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # justify-content-end 클래스 확인
        assert "justify-content-end" in content

    # SIM_PRT_VAL_001: Trade+Lane 중복 검증
    def test_sim_prt_val_001_duplicate_trade_lane(self, api_client, default_proforma):
        """Trade+Lane 중복 검증 (JavaScript에서 처리)"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # checkUniquePairs 함수 확인
        assert "checkUniquePairs" in content

    # SIM_PRT_VAL_002: 필수 필드 검증
    def test_sim_prt_val_002_required_fields_validation(self, api_client, default_proforma):
        """Trade/Lane 필수 필드 검증"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # required 속성 확인
        assert "required" in content

    # SIM_PRT_VAL_003: Capacity/Qty 정수 입력
    def test_sim_prt_val_003_integer_input_validation(self, api_client, default_proforma):
        """Capacity/Qty 정수 입력 검증"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # type="number" 확인
        assert 'type="number"' in content

    # SIM_PRT_API_003: Save 버튼
    def test_sim_prt_api_003_save_button_submit(self, api_client, default_proforma):
        """Save 버튼 form submit"""
        response = api_client.get(reverse("simulation:port_creation"))

        assert response.status_code == 200
        content = response.content.decode()
        # Save 버튼 확인
        assert "Save" in content

    # SIM_PRT_API_004: Save 후 데이터 저장
    def test_sim_prt_api_004_save_port_data_to_db(
        self, api_client, simulation_run, valid_rows_data
    ):
        """Save 후 SimulationProforma 테이블 저장"""
        data = {"simulation_id": simulation_run.id, "rows": valid_rows_data}
        # 첫 번째 행의 capacity를 2000으로 변경
        data.get("rows")[0]["capacity"] = 2000
        response = api_client.post(
            reverse("simulation:save_port_creation"),
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        # SimulationProforma 생성 확인
        assert SimulationProforma.objects.filter(simulation=simulation_run).count() == len(
            valid_rows_data
        )
        # 변경된 값 확인
        assert SimulationProforma.objects.filter(simulation=simulation_run).first().capacity == 2000

    # SIM_PRT_API_005: Save 성공 응답
    def test_sim_prt_api_005_save_success_response(
        self, api_client, simulation_run, valid_row_data
    ):
        """Save 성공 후 JSON 응답"""
        data = {"simulation_id": simulation_run.id, "rows": [valid_row_data]}

        response = api_client.post(
            reverse("simulation:save_port_creation"),
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        resp_data = json.loads(response.content)
        assert resp_data.get("success") is True

    # SIM_PRT_API_006: Save 오류 처리 (마스터 데이터 미존재)
    def test_sim_prt_api_006_save_error_invalid_trade(
        self, api_client, simulation_run, invalid_row_data
    ):
        """Save 시 존재하지 않는 Trade 입력 오류 처리"""
        data = {"simulation_id": simulation_run.id, "rows": [invalid_row_data]}

        response = api_client.post(
            reverse("simulation:save_port_creation"),
            data=json.dumps(data),
            content_type="application/json",
        )

        # 오류 처리
        assert response.status_code in [200, 400, 500]
        # SimulationProforma는 저장되지 않아야 함
        assert SimulationProforma.objects.filter(simulation=simulation_run).count() == 0


@pytest.mark.django_db
class TestSimulationNumberGeneration:
    """Simulation Number 생성 테스트"""

    # SIM_NUM_GEN_001: 신규 시뮬레이션 번호 생성
    def test_sim_num_gen_001_new_simulation_number(self, api_client, today_string):
        """YYYYMMDD_NN-01 형식 생성"""
        api_client.get(reverse("simulation:port_creation"))

        sim = SimulationRun.objects.first()
        # 형식 검증
        assert sim.simulation_number.startswith(today_string)
        assert sim.simulation_number.endswith("-01")

    # TODO port_creation 이외 화면에서 시뮬레이션 실행 시 발생하는 케이스
    # SIM_NUM_GEN_002: 순차 증가
    # def test_sim_num_gen_002_sequential_number_increment(self, api_client, today_string):
    #     """같은 날짜 내 NN 순차 증가"""
    #     # 첫 번째 시뮬레이션
    #     api_client.get(reverse('simulation:port_creation'))
    #     sim1 = SimulationRun.objects.first()
    #
    #     # 두 번째 시뮬레이션
    #     api_client.get(reverse('simulation:port_creation'))
    #     sim2 = SimulationRun.objects.last()
    #
    #     # 첫 번째는 _01-01
    #     assert sim1.simulation_number.startswith(f'{today_string}_01')
    #     # 두 번째는 _02-01
    #     assert sim2.simulation_number.startswith(f'{today_string}_02')

    # SIM_NUM_GEN_003: 기존 시뮬레이션 재편집 시 번호 유지
    def test_sim_num_gen_003_existing_simulation_number_preserved(self, api_client, simulation_run):
        """기존 시뮬레이션 재편집 시 번호 유지"""
        original_sim_number = simulation_run.simulation_number

        response = api_client.get(
            reverse("simulation:port_creation"), {"sim_id": simulation_run.id}
        )

        assert response.status_code == 200
        assert response.context["simulation_number"] == original_sim_number
        # 새로운 시뮬레이션이 생성되지 않았는지 확인
        assert SimulationRun.objects.count() == 1
