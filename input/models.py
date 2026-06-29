from django.db import models


class MasterPort(models.Model):
    """마스터 Port (Location) 정보"""
    port_code = models.CharField(
        max_length=10, primary_key=True, verbose_name="Location Code"
    )
    port_name = models.CharField(max_length=100, verbose_name="Location Name")
    continent_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Continent Code"
    )
    country_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Country Code"
    )

    class Meta:
        db_table = "master_port"
        verbose_name = "Master Port"
        verbose_name_plural = "Master Ports"

    def __str__(self):
        return f"{self.port_code} - {self.port_name}"


class MasterTrade(models.Model):
    """마스터 Trade 정보"""
    trade_code = models.CharField(
        max_length=10, primary_key=True,  verbose_name="Trade Code"
    )
    trade_name = models.CharField(max_length=100, verbose_name="Trade Name")
    from_continent_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="From Continent Code"
    )
    to_continent_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="To Continent Code"
    )

    class Meta:
        db_table = "master_trade"
        verbose_name = "Master Trade"
        verbose_name_plural = "Master Trades"

    def __str__(self):
        return f"{self.trade_code} - {self.trade_name}"



class MasterLane(models.Model):
    """마스터 Lane (Service) 정보"""
    lane_code = models.CharField(
        max_length=10, primary_key=True, verbose_name="Lane Code"
    )
    lane_name = models.CharField(max_length=100, verbose_name="Lane Name")
    vessel_service_type_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Vessel Service Type Code"
    )
    effective_from_date = models.DateField(
        null=True, blank=True, verbose_name="Effective start date of the lane."
    )
    effective_to_date = models.DateField(
        null=True, blank=True, verbose_name="Effective end date of the lane."
    )
    feeder_division_code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Feeder Division Code"
    )

    class Meta:
        db_table = "master_lane"
        verbose_name = "Master Lane"
        verbose_name_plural = "Master Lanes"

    def __str__(self):
        return f"{self.lane_code} - {self.lane_name}"

class DefaultBerthWindowStatus(models.Model):
    """Default Berth Window Status 정보"""

    id = models.AutoField(primary_key=True)
    # MasterLane, MasterPort 등의 외래키를 활용하려면 ForeignKey로 변경 가능합니다.
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
        db_table = "default_berth_window_status"
        verbose_name = "Default Berth Window Status"
        verbose_name_plural = "Default Berth Window Status"

    def __str__(self):
        return f"{self.lane} - {self.port} - {self.berth}"


class DefaultCurrentProforma(models.Model):
    """Default Proforma 스케줄 메인 정보"""

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
        db_table = "default_current_proforma"
        verbose_name = "Default Current Proforma"
        verbose_name_plural = "DefaultCurrentProforma"
        constraints = [
            models.UniqueConstraint(
                fields=["trade", "lane"], name="uq_trade_lane"
            )
        ]

    def __str__(self):
        return f"{self.trade} - {str(self.lane)}"

class DefaultCurrentProformaDetail(models.Model):
    """현재 Proforma 스케줄 상세 정보"""

    id = models.AutoField(primary_key=True)
    current_proforma = models.ForeignKey(
        DefaultCurrentProforma,
        on_delete=models.CASCADE,
        db_column="current_proforma_id",
        related_name="details",
        verbose_name="Current Proforma ID",
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
        db_table = "default_current_proforma_detail"
        verbose_name = "Default Current Proforma Detail"
        verbose_name_plural = "Default Current Proforma Details"

    def __str__(self):
        return f"{self.current_proforma} - {self.port} ({self.terminal})"

class DefaultRdrDemand(models.Model):
    """ rdr demand """

    id = models.AutoField(primary_key=True, verbose_name="RdrDemand ID")
    trade = models.ForeignKey(
        MasterTrade,
        on_delete=models.PROTECT,
        to_field="trade_code",
        db_column="trade_code",
        verbose_name="Trade Code",
    )
    pol = models.ForeignKey(
        MasterPort,
        on_delete=models.PROTECT,
        to_field="port_code",
        db_column="pol_code",
        related_name="pol_demands",
    )
    pod = models.ForeignKey(
        MasterPort,
        on_delete=models.PROTECT,
        to_field="port_code",
        db_column="pod_code",
        related_name="pod_demands",
    )
    demand_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Demand Value"
    )

    def __str__(self):
        return f"{self.trade.trade_code} : {self.pol.port_code} -> {self.pod.port_code}"

    class Meta:
        db_table = "default_rdr_demand"
        verbose_name = "Default RDR Demand"
        verbose_name_plural = "Default RDR Demands"
        ordering = ["trade", "pol", "pod"]

        constraints = [
            models.UniqueConstraint(
                fields=["trade", "pol", "pod"],
                name="uq_trade_pol_pod",
            )
        ]
