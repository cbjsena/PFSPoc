# simulation/models.py
from datetime import date

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import Max

from common.constants import SIMULATION_STATUS_CHOICES, SIMULATION_STATUS_PENDING
from common.models import CommonModel
from input.models import MasterLane, MasterTrade, MasterPort


class SimulationRun(CommonModel):
    """시뮬레이션 실행 기록 (DB 관리)."""

    id = models.AutoField(primary_key=True, verbose_name="Simulation ID")
    simulation_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Simulation Number",
        help_text="Auto-generated unique (YYYYMMDD_NN-XX)",
        blank=True,
    )
    base_simulation_number = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Base Simulation Number",
        help_text="Reference Simulation Number",
    )
    # 상태 & 진행률
    status = models.CharField(
        max_length=20,
        choices=SIMULATION_STATUS_CHOICES,
        default=SIMULATION_STATUS_PENDING,
    )
    progress = models.IntegerField(default=0, help_text="진행률 (%)")
    task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Celery Task ID",
    )

    objective_value = models.FloatField(blank=True, null=True)
    execution_time = models.FloatField(blank=True, null=True, help_text="실행 시간 (초)")
    model_status = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="simulations_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "simulation_run"
        ordering = ["-created_at"]
        verbose_name = "Simulation Run"

    def __str__(self):
        return f"Sim#{self.id} - {self.status}"

    @property
    def is_running(self):
        return self.status == "RUNNING"

    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def is_processing(self):
        return self.status in ("PENDING", "RUNNING")

    @property
    def is_success(self):
        return self.status == "SUCCESS"

    @property
    def can_cancel(self):
        return self.status in ("PENDING", "RUNNING")



class SimulationBaseModel(CommonModel):
    """시나리오 테이블용 공통 모델 (FK + Audit)"""

    simulation = models.ForeignKey(
        SimulationRun,
        on_delete=models.CASCADE,
        verbose_name="Simulation ID",
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True

class SimulationBerthWindow(SimulationBaseModel):
    """
    Simulation Berth Window Status 정보 (시나리오별 스냅샷)
    DefaultBerthWindowStatus와 동일한 구조를 가지되,
    특정 SimulationRun(Scenario)에 종속.
    """

    id = models.AutoField(primary_key=True)

    # scenario 필드는 ScenarioBaseModel에서 자동으로 상속받습니다.
    # created_at, created_by, updated_at, updated_by 역시 CommonModel에서 상속됩니다.

    lane = models.ForeignKey(
        MasterLane,
        on_delete=models.PROTECT,
        to_field="lane_code",
        db_column="lane_code",
        verbose_name="Lane Code / 3 alpha",
    )
    country = models.CharField(max_length=20, null=True, blank=True, verbose_name="Country")
    port = models.CharField(max_length=20, null=True, blank=True, verbose_name="Port")
    berth = models.CharField(max_length=50, null=True, blank=True, verbose_name="Berth")

    etb_day = models.CharField(max_length=10, null=True, blank=True, verbose_name="ETB Day")
    etb_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="ETB Time")
    etd_day = models.CharField(max_length=10, null=True, blank=True, verbose_name="ETD Day")
    etd_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="ETD Time")

    loading_volume = models.IntegerField(null=True, blank=True, verbose_name="Loading Volume")
    discharging_volume = models.IntegerField(
        null=True, blank=True, verbose_name="Discharging Volume"
    )
    productivity = models.IntegerField(null=True, blank=True, verbose_name="Productivity")
    berthing = models.IntegerField(null=True, blank=True, verbose_name="Berthing")

    class Meta:
        db_table = "simulation_berth_window"
        verbose_name = "Simulation Berth Window"
        verbose_name_plural = "Simulation Berth Windows"

    def __str__(self):
        # 어떤 시뮬레이션(scenario_id)의 데이터인지 알기 쉽게 문자열 포맷을 약간 수정했습니다.
        return f"[Sim#{self.simulation.simulation_number}] {self.lane.id} - {self.port} - {self.berth}"

    @property
    def total_volume(self):
        # 값이 없으면(None) 0으로 처리하여 합산합니다.
        loading = self.loading_volume if self.loading_volume is not None else 0
        discharging = self.discharging_volume if self.discharging_volume is not None else 0
        return loading + discharging


class SimulationProforma(SimulationBaseModel):
    """
    Simulation Proforma 정보 (시나리오별 스냅샷) DefaultCurrentProforma와 동일한 구조를 가지되,
    특정 SimulationRun(Scenario)에 종속.
    """

    id = models.AutoField(primary_key=True)
    trade = models.ForeignKey(
        MasterTrade,
        on_delete=models.PROTECT,
        to_field="trade_code",
        db_column="trade_code",
        verbose_name="Trade Code",
    )
    lane = models.ForeignKey(
        MasterLane,
        on_delete=models.PROTECT,
        to_field="lane_code",
        db_column="lane_code",
        verbose_name="Lane Code / 3 alpha",
    )
    capacity = models.IntegerField(null=True, blank=True, verbose_name="Capacity")
    qty = models.IntegerField(null=True, blank=True, verbose_name="Qty")

    class Meta:
        db_table = "simulation_proforma"
        verbose_name = "Simulation Proforma"
        constraints = [
            models.UniqueConstraint(
                fields=["simulation", "trade", "lane"], name="uq_simulation_trade_lane"
            )
        ]

    def __str__(self):
        return f"[Sim#{self.simulation_id}] {self.trade} - {str(self.lane)}"


class SimulationProformaEssentialPort(SimulationBaseModel):
    """
    Simulation Proforma Essential Port 정보 (시나리오별 스냅샷)
    Proforma 생성 Lane에 포함해야 될 Port 정보로 특정 SimulationRun(Scenario)에 종속.
    """
    id = models.AutoField(primary_key=True)
    proforma = models.ForeignKey(
        SimulationProforma,
        on_delete=models.CASCADE,
        db_column="proforma_id",
        related_name="essential_ports",
        verbose_name="Simulation Proforma ID",
    )
    port = models.ForeignKey(
        MasterPort,
        on_delete=models.PROTECT,
        to_field="port_code",
        db_column="port_code",
        verbose_name="Port Code",
    )

    class Meta:
        db_table = "simulation_proforma_essential_port"
        verbose_name = "Simulation Proforma Essential Port"

    def __str__(self):
        return f"[Sim#{self.simulation_id}] {self.proforma_id} - {str(self.port)}"
    

class SimulationProformaDetail(SimulationBaseModel):
    """
    Simulation Proforma 상세 정보 (시나리오별 스냅샷)
    DefaultCurrentProformaDetail 동일한 구조를 가지되,
    특정 SimulationRun(Scenario)에 종속.
    """

    id = models.AutoField(primary_key=True)
    proforma = models.ForeignKey(
        SimulationProforma,
        on_delete=models.CASCADE,
        db_column="proforma_id",
        related_name="details",
        verbose_name="Simulation Proforma ID",
    )
    port = models.ForeignKey(
        MasterPort,
        on_delete=models.PROTECT,
        to_field="port_code",
        db_column="port_code",
        verbose_name="Port Code",
    )
    terminal = models.CharField(max_length=50, null=True, blank=True, verbose_name="Terminal")

    etb_day = models.CharField(max_length=10, null=True, blank=True, verbose_name="ETB Day")
    etb_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="ETB Time")
    etd_day = models.CharField(max_length=10, null=True, blank=True, verbose_name="ETD Day")
    etd_time = models.CharField(max_length=20, null=True, blank=True, verbose_name="ETD Time")

    class Meta:
        db_table = "simulation_proforma_detail"
        verbose_name = "Simulation Proforma Detail"
        verbose_name_plural = "Simulation Proforma Details"

    def __str__(self):
        return f"[Sim#{self.simulation_id}] {self.proforma_id} - {self.port} ({self.terminal})"