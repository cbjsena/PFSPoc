import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import redirect, render

from common.constants import SIMULATION_STATUS_SUCCESS
from common.menus import SIMULATION_SIDEBAR_MENU
from common.views import menu_placeholder
from input.models import MasterLane, MasterTrade
from simulation.models import (
    SimulationProforma,
    SimulationProformaDetail,
    SimulationProformaEssentialPort,
    SimulationRun,
)


def generate_simulation_number():
    """YYYYMMDD_NN-XX 형식의 simulation_number 생성.
    - YYYYMMDD: 오늘 날짜
    - NN: 오늘 날짜에 생성된 시뮬레이션의 sequence (01, 02, ...)
    - XX: 하위 sequence (항상 01로 시작)
    """
    today = date.today().strftime("%Y%m%d")

    # 오늘 날짜로 생성된 시뮬레이션 중 base_simulation_number가 없는 것의 개수 + 1
    today_count = (
        SimulationRun.objects.filter(
            simulation_number__startswith=today,
            base_simulation_number__isnull=True,  # 최상위 시뮬레이션만
        ).count()
        + 1
    )

    seq_number = str(today_count).zfill(2)
    simulation_number = f"{today}_{seq_number}-01"
    return simulation_number


def simulation_list(request):
    """시뮬레이션 전체 목록."""
    simulations = SimulationRun.objects.all()
    # created_by_id 필터링
    created_by_id = request.GET.get("created_by_id")
    if created_by_id:
        try:
            simulations = simulations.filter(created_by_id=int(created_by_id))
        except (ValueError, TypeError):
            pass

    # 필터 옵션: 모든 사용자 목록
    from django.contrib.auth import get_user_model

    User = get_user_model()
    all_users = User.objects.all().order_by("username")

    return render(
        request,
        "simulation/simulation_list.html",
        {
            "current_top_menu": "simulation",
            "sidebar_menu": SIMULATION_SIDEBAR_MENU,
            "current_sidebar_menu": "simulation_list",
            "simulations": simulations,
            "all_users": all_users,
            "selected_created_by_id": created_by_id or "",
        },
    )


def simulation_monitoring(request):
    return menu_placeholder(
        request,
        "Monitoring",
        "Simulation monitoring is not implemented yet.",
        sidebar_title="Simulation",
    )


def simulation_creation(request):
    """시뮬레이션 생성 페이지."""


def port_creation(request):
    from input.models import (DefaultCurrentProforma,DefaultProformaEssentialPort,
                              MasterLane, MasterPort, MasterTrade)

    # Simulation Number는 새로 생성하거나 GET 파라미터에서 받음
    sim_id = request.GET.get("sim_id")
    if not sim_id:
        # 새 시뮬레이션 생성
        simulation_number = generate_simulation_number()
        sim = SimulationRun.objects.create(
            created_by=request.user if request.user.is_authenticated else None,
            status=SIMULATION_STATUS_SUCCESS,
            simulation_number=simulation_number,
            base_simulation_number=None,  # 최상위 시뮬레이션
        )
        sim_id = sim.id
    else:
        try:
            sim = SimulationRun.objects.get(id=sim_id)
        except SimulationRun.DoesNotExist:
            return redirect("simulation:simulation_list")

    if request.method == "POST":
        # POST된 행 데이터를 저장하고 백그라운드 작업 실행
        description = request.POST.get("description", "")
        sim.description = description
        sim.save()
        # TODO: 실제 행 데이터 저장 로직
        return redirect("simulation:simulation_list")

    # 💡 핵심 변경 사항: 시뮬레이션에 저장된 데이터가 있는지 우선 확인
    # Saved SimulationProforma가 있으면 그쪽을 사용하고, 없으면 DefaultCurrentProforma를 사용합니다.
    from django.db.models import Prefetch

    saved_proformas = (
        SimulationProforma.objects.filter(simulation=sim)
        .select_related("trade", "lane")
        .prefetch_related(Prefetch("essential_ports", queryset=SimulationProformaEssentialPort.objects.select_related("port")))
    )

    if saved_proformas.exists():
        proformas = saved_proformas
    else:
        proformas = (
            DefaultCurrentProforma.objects.select_related("trade", "lane").prefetch_related("essential_ports__port").all()
        )

    # Build rows list (each row contains proforma and up to 5 essential ports) to simplify template logic
    rows = []
    for p in proformas:
        capacity = getattr(p, "capacity", "") or ""
        qty = getattr(p, "qty", "") or ""
        # collect essential port codes (may be empty)
        essentials = []
        for ep in getattr(p, "essential_ports").all():
            try:
                essentials.append(ep.port.port_code)
            except Exception:
                # fallback to string representation
                essentials.append(str(ep.port))
        # pad to 5 inputs
        while len(essentials) < 5:
            essentials.append("")
        rows.append({
            "proforma": p,
            "trade": p.trade,
            "lane": p.lane,
            "capacity": capacity,
            "qty": qty,
            "essentials": essentials,
        })

    trades = MasterTrade.objects.all().order_by("trade_name")
    lanes = MasterLane.objects.all().order_by("lane_name")
    # Load all master port codes (used for datalist). Note: for large datasets consider switching to server-side autocomplete.
    master_ports = list(MasterPort.objects.all().order_by('port_code').values_list('port_code', flat=True))

    return render(
        request,
        "simulation/port_creation.html",
        {
            "current_top_menu": "simulation",
            "sidebar_menu": SIMULATION_SIDEBAR_MENU,
            "current_sidebar_menu": "port_creation",
            "simulation_number": sim.simulation_number,
            "rows": rows,
            "trades": trades,
            "lanes": lanes,
            "master_ports": master_ports,
        },
    )


def generate_calling_ports(request):
    """Port Creation 화면의 데이터를 저장하고 PFS Creation 화면으로 리다이렉트.
    현재는 엔진 없이 데이터 저장 후 바로 PFS Creation으로 이동한다.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        sim_id = data.get("simulation_id")
        rows = data.get("rows", [])

        # sim_id가 simulation_number일 수 있으므로 두 가지로 조회
        try:
            sim = SimulationRun.objects.get(id=sim_id)
        except (SimulationRun.DoesNotExist, ValueError):
            sim = SimulationRun.objects.get(simulation_number=sim_id)

        from input.models import MasterPort as MP
        from input.models import DefaultCurrentProforma, DefaultCurrentProformaDetail
        from django.db import transaction

        # Port Creation 데이터 저장
        with transaction.atomic():
            SimulationProforma.objects.filter(simulation=sim).delete()

            for row in rows:
                trade_code = row.get("trade")
                lane_code = row.get("lane")
                capacity = row.get("capacity")
                qty = row.get("qty")
                essentials = row.get("essentials", [])

                try:
                    trade = MasterTrade.objects.get(trade_code=trade_code)
                    lane = MasterLane.objects.get(lane_code=lane_code)

                    proforma = SimulationProforma.objects.create(
                        simulation=sim,
                        trade=trade,
                        lane=lane,
                        capacity=int(capacity) if capacity else None,
                        qty=int(qty) if qty else None,
                    )

                    for code in essentials:
                        if not code:
                            continue
                        try:
                            port = MP.objects.get(port_code=code)
                            SimulationProformaEssentialPort.objects.create(
                                simulation=sim,
                                proforma=proforma,
                                port=port,
                            )
                        except MP.DoesNotExist:
                            continue

                    # DefaultCurrentProformaDetail에서 default 데이터 복사
                    try:
                        default_proforma = DefaultCurrentProforma.objects.get(
                            trade=trade, lane=lane
                        )
                        default_details = DefaultCurrentProformaDetail.objects.filter(
                            current_proforma=default_proforma
                        )
                        for detail in default_details:
                            SimulationProformaDetail.objects.create(
                                simulation=sim,
                                proforma=proforma,
                                port=detail.port,
                                terminal=detail.terminal,
                                calling_port_indicator=detail.calling_port_indicator,
                                calling_port_seq=detail.calling_port_seq,
                                etb_day=detail.etb_day,
                                etb_time=detail.etb_time,
                                etd_day=detail.etd_day,
                                etd_time=detail.etd_time,
                            )
                    except DefaultCurrentProforma.DoesNotExist:
                        pass

                except (MasterTrade.DoesNotExist, MasterLane.DoesNotExist):
                    continue

        # TODO: 여기서 엔진을 호출하여 calling ports를 생성하는 로직 추가
        # 현재는 엔진 없이 바로 PFS Creation으로 이동

        from django.urls import reverse
        redirect_url = reverse("simulation:pfs_creation") + f"?sim_id={sim.id}"
        return JsonResponse({"success": True, "redirect_url": redirect_url})

    except SimulationRun.DoesNotExist:
        return JsonResponse({"error": "Simulation not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def save_port_creation(request):
    """포트 생성 화면의 행 데이터를 SimulationProforma에 저장"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        sim_id = data.get("simulation_id")
        rows = data.get("rows", [])

        sim = SimulationRun.objects.get(id=sim_id)

        # 기존 데이터 삭제 (새로 저장)
        from simulation.models import SimulationProforma, SimulationProformaEssentialPort
        from input.models import MasterPort as MP
        from django.db import transaction

        # Use transaction to ensure atomicity between proforma and essential port inserts
        with transaction.atomic():
            # 이전 proformas (and their essential ports via cascade) 삭제
            SimulationProforma.objects.filter(simulation=sim).delete()

            # 새 행 데이터 저장
            for row in rows:
                trade_code = row.get("trade")
                lane_code = row.get("lane")
                capacity = row.get("capacity")
                qty = row.get("qty")
                essentials = row.get("essentials", [])

                try:
                    trade = MasterTrade.objects.get(trade_code=trade_code)
                    lane = MasterLane.objects.get(lane_code=lane_code)

                    proforma = SimulationProforma.objects.create(
                        simulation=sim,
                        trade=trade,
                        lane=lane,
                        capacity=int(capacity) if capacity else None,
                        qty=int(qty) if qty else None,
                    )

                    # Save essential ports (if any)
                    for code in essentials:
                        if not code:
                            continue
                        try:
                            port = MP.objects.get(port_code=code)
                            SimulationProformaEssentialPort.objects.create(
                                simulation=sim,
                                proforma=proforma,
                                port=port,
                            )
                        except MP.DoesNotExist:
                            # ignore unknown port codes
                            continue

                except (MasterTrade.DoesNotExist, MasterLane.DoesNotExist):
                    # skip invalid rows
                    continue

        return JsonResponse({"success": True, "message": "Data saved successfully"})

    except SimulationRun.DoesNotExist:
        return JsonResponse({"error": "Simulation not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def pfs_creation(request):
    """PFS Creation 화면. Port Creation과 유사하지만 Calling Ports 20개 컬럼."""
    from input.models import MasterPort
    from django.db.models import Prefetch

    sim_id = request.GET.get("sim_id")
    if not sim_id:
        return redirect("simulation:port_creation")

    try:
        sim = SimulationRun.objects.get(id=sim_id)
    except SimulationRun.DoesNotExist:
        return redirect("simulation:simulation_list")

    # 저장된 SimulationProforma 로드 (details를 calling_port_seq 순으로 prefetch)
    proformas = (
        SimulationProforma.objects.filter(simulation=sim)
        .select_related("trade", "lane")
        .prefetch_related(
            Prefetch(
                "details",
                queryset=SimulationProformaDetail.objects.select_related("port")
                .order_by("calling_port_seq"),
            )
        )
    )

    if not proformas.exists():
        return redirect("simulation:port_creation")

    max_calling_ports = 20
    rows = []
    for p in proformas:
        capacity = getattr(p, "capacity", "") or ""
        qty = getattr(p, "qty", "") or ""

        # SimulationProformaDetail에서 calling_port_seq 순서로 port_code 추출
        calling_ports = []
        for detail in p.details.all():
            calling_ports.append(detail.port.port_code)

        # 20개까지 패딩
        while len(calling_ports) < max_calling_ports:
            calling_ports.append("")

        rows.append({
            "proforma": p,
            "trade": p.trade,
            "lane": p.lane,
            "capacity": capacity,
            "qty": qty,
            "calling_ports": calling_ports,
        })

    master_ports = list(
        MasterPort.objects.all().order_by("port_code").values_list("port_code", flat=True)
    )

    return render(
        request,
        "simulation/pfs_creation.html",
        {
            "current_top_menu": "simulation",
            "sidebar_menu": SIMULATION_SIDEBAR_MENU,
            "current_sidebar_menu": "pfs_creation",
            "simulation_number": sim.simulation_number,
            "sim_id": sim.id,
            "rows": rows,
            "master_ports": master_ports,
            "max_calling_ports": max_calling_ports,
            "calling_port_range": range(max_calling_ports),
        },
    )


def generate_pfs_ports(request):
    """PFS Creation 화면에서 PFS Creation 버튼 클릭 시 실행.
    DefaultCurrentProformaDetail 전체를 SimulationProformaDetail에 복사하고
    Created Result 화면으로 리다이렉트한다.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
        sim_id = data.get("simulation_id")

        try:
            sim = SimulationRun.objects.get(id=sim_id)
        except (SimulationRun.DoesNotExist, ValueError):
            sim = SimulationRun.objects.get(simulation_number=sim_id)

        from django.db import transaction
        from input.models import DefaultCurrentProformaDetail
        from simulation.models import SimulationProformaDetail

        with transaction.atomic():
            # 기존 detail 삭제
            SimulationProformaDetail.objects.filter(simulation=sim).delete()

            # 시뮬레이션 proforma를 (trade, lane) 키로 매핑
            sim_proformas = list(
                SimulationProforma.objects.filter(simulation=sim).select_related("trade", "lane")
            )
            sim_pf_map = {(pf.trade_id, pf.lane_id): pf for pf in sim_proformas}

            # DefaultCurrentProformaDetail 전체 조회 후 매핑 가능한 건만 복사
            default_details = DefaultCurrentProformaDetail.objects.select_related(
                "current_proforma",
                "port",
                "current_proforma__trade",
                "current_proforma__lane",
            )

            to_create = []
            for dd in default_details:
                key = (dd.current_proforma.trade_id, dd.current_proforma.lane_id)
                sim_pf = sim_pf_map.get(key)
                if not sim_pf:
                    continue

                to_create.append(
                    SimulationProformaDetail(
                        simulation=sim,
                        proforma=sim_pf,
                        port=dd.port,
                        terminal=dd.terminal,
                        calling_port_indicator=dd.calling_port_indicator,
                        calling_port_seq=dd.calling_port_seq,
                        etb_day=dd.etb_day,
                        etb_time=dd.etb_time,
                        etd_day=dd.etd_day,
                        etd_time=dd.etd_time,
                    )
                )

            if to_create:
                SimulationProformaDetail.objects.bulk_create(to_create, batch_size=1000)

        from django.urls import reverse
        redirect_url = reverse("simulation:created_result") + f"?sim_id={sim.id}"
        return JsonResponse({"success": True, "redirect_url": redirect_url})

    except SimulationRun.DoesNotExist:
        return JsonResponse({"error": "Simulation not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def delete_simulation(request, sim_id):
    """시뮬레이션 삭제"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        sim = SimulationRun.objects.get(id=sim_id)
        # 권한 확인 (선택): 생성자만 삭제 가능
        # if sim.created_by != request.user:
        #     return JsonResponse({'error': 'Permission denied'}, status=403)

        sim.delete()
        return JsonResponse({"success": True})
    except SimulationRun.DoesNotExist:
        return JsonResponse({"error": "Simulation not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def created_result(request):
    """Created Result 화면. Current Proforma와 동일한 형식으로 시뮬레이션 결과 표시."""
    from simulation.models import SimulationProformaDetail

    sim_id = request.GET.get("sim_id")
    if not sim_id:
        return redirect("simulation:simulation_list")

    try:
        sim = SimulationRun.objects.get(id=sim_id)
    except SimulationRun.DoesNotExist:
        return redirect("simulation:simulation_list")

    DAY_ORDER = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}

    def _format_time(time_str):
        if not time_str:
            return ""
        time_str = time_str.strip()
        if ":" not in time_str:
            try:
                val = int(time_str)
                return f"{val // 60:02d}:{val % 60:02d}"
            except ValueError:
                return time_str
        parts = time_str.split(":")
        return f"{parts[0]}:{parts[1]}"

    def _parse_time_minutes(time_str):
        if not time_str:
            return None
        time_str = time_str.strip()
        if ":" not in time_str:
            try:
                return int(time_str)
            except ValueError:
                return None
        parts = time_str.split(":")
        try:
            return int(parts[0]) * 60 + (int(parts[1]) if len(parts) > 1 else 0)
        except ValueError:
            return None

    def _calc_duration(detail):
        etb_day = (detail.etb_day or "").strip().upper()
        etb_time = (detail.etb_time or "").strip()
        etd_day = (detail.etd_day or "").strip().upper()
        etd_time = (detail.etd_time or "").strip()
        if not all([etb_day, etb_time, etd_day, etd_time]):
            return ""
        try:
            etb_d = DAY_ORDER.get(etb_day, -1)
            etd_d = DAY_ORDER.get(etd_day, -1)
            if etb_d < 0 or etd_d < 0:
                return ""
            etb_minutes = _parse_time_minutes(etb_time)
            etd_minutes = _parse_time_minutes(etd_time)
            if etb_minutes is None or etd_minutes is None:
                return ""
            etb_total = etb_d * 24 * 60 + etb_minutes
            etd_total = etd_d * 24 * 60 + etd_minutes
            if etd_total <= etb_total:
                etd_total += 7 * 24 * 60
            diff = etd_total - etb_total
            hours = diff // 60
            minutes = diff % 60
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        except (ValueError, IndexError, TypeError):
            return ""

    # Load proformas with details
    proformas = (
        SimulationProforma.objects.filter(simulation=sim)
        .select_related("trade", "lane")
        .prefetch_related("details__port")
    )

    schedules = []
    max_ports = 0
    total_details = 0

    for pf in proformas:
        details = list(pf.details.all())
        total_details += len(details)
        ports = []
        for d in details:
            ports.append({
                "port": d.port.port_code,
                "terminal": d.terminal or "",
                "etb_day": d.etb_day or "",
                "etb_time_display": _format_time(d.etb_time),
                "etd_day": d.etd_day or "",
                "etd_time_display": _format_time(d.etd_time),
                "duration": _calc_duration(d),
            })
        port_count = len(ports)
        max_ports = max(max_ports, port_count)
        schedules.append({
            "trade": pf.trade.trade_code,
            "lane": pf.lane.lane_code,
            "capacity": pf.capacity or "",
            "qty": pf.qty or "",
            "ports": ports,
            "port_count": port_count,
        })

    for s in schedules:
        s["empty_cells"] = [None] * (max_ports - s["port_count"])

    return render(
        request,
        "simulation/created_result.html",
        {
            "current_top_menu": "simulation",
            "sidebar_menu": SIMULATION_SIDEBAR_MENU,
            "current_sidebar_menu": "created_result",
            "simulation_number": sim.simulation_number,
            "sim_id": sim.id,
            "loaded": True,
            "schedules": schedules,
            "max_ports": max_ports,
            "schedule_count": len(schedules),
            "detail_count": total_details,
        },
    )


def berth_windows_adjustment(request):
    return menu_placeholder(
        request,
        "Berth Windows Adjustment",
        "Berth Windows Adjustment is not implemented yet.",
        sidebar_title="Simulation",
    )


def created_result_adjustment(request):
    return menu_placeholder(
        request,
        "Created Result Adjustment",
        "Created Result Adjustment is not implemented yet.",
        sidebar_title="Simulation",
    )
