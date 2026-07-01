import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import redirect, render

from common.constants import SIMULATION_STATUS_SUCCESS
from common.menus import SIMULATION_SIDEBAR_MENU
from common.views import menu_placeholder
from input.models import MasterLane, MasterTrade
from simulation.models import SimulationProforma, SimulationRun, SimulationProformaEssentialPort


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

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    # trade = request.POST.get("trade")
    # lane = request.POST.get("lane")

    from input.models import MasterPort

    # TODO: Replace with real generation logic using trade/lane
    ports = list(MasterPort.objects.all().values("port_code", "port_name")[:10])

    return JsonResponse({"ports": ports})


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
    return menu_placeholder(
        request,
        "PFS Creation",
        "PFS Creation is not implemented yet.",
        sidebar_title="Simulation",
    )


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
    return menu_placeholder(
        request,
        "Created Result",
        "Created Result is not implemented yet.",
        sidebar_title="Simulation",
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
