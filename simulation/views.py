from common.menus import SIMULATION_SIDEBAR_MENU
from common.views import menu_placeholder
from django.shortcuts import get_object_or_404, redirect, render

from simulation.models import SimulationRun


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
    from input.models import DefaultCurrentProforma

    if request.method == "POST":
        # Simulation 생성 로직
        proforma_id = request.POST.get("proforma_id")
        description = request.POST.get("description", "")

        try:
            proforma = DefaultCurrentProforma.objects.get(id=proforma_id)
            sim = SimulationRun.objects.create(
                created_by=request.user,
                description=description,
                status="PENDING",
            )
            # TODO: Celery 비동기 작업 실행
            return redirect("simulation:simulation_list")
        except DefaultCurrentProforma.DoesNotExist:
            return render(
                request,
                "simulation/simulation_create.html",
                {
                    "current_top_menu": "simulation",
                    "sidebar_menu": SIMULATION_SIDEBAR_MENU,
                    "current_sidebar_menu": "simulation_creation",
                    "proformas": DefaultCurrentProforma.objects.select_related(
                        "trade", "lane"
                    ),
                    "error": "Invalid proforma selected",
                },
            )

    proformas = DefaultCurrentProforma.objects.select_related("trade", "lane").all()
    return render(
        request,
        "simulation/simulation_create.html",
        {
            "current_top_menu": "simulation",
            "sidebar_menu": SIMULATION_SIDEBAR_MENU,
            "current_sidebar_menu": "simulation_creation",
            "proformas": proformas,
        },
    )


def pfs_creation(request):
    return menu_placeholder(
        request,
        "PFS Creation",
        "PFS Creation is not implemented yet.",
        sidebar_title="Simulation",
    )


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