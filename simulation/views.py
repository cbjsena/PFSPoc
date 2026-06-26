from common.views import menu_placeholder


def simulation_list(request):
    return menu_placeholder(
        request,
        "Simulation List",
        "Simulation screens will be added here.",
        sidebar_title="Simulation",
    )


def simulation_create(request):
    return menu_placeholder(
        request,
        "Create Simulation",
        "Simulation creation is not implemented yet.",
        sidebar_title="Simulation",
    )


def simulation_monitoring(request):
    return menu_placeholder(
        request,
        "Monitoring",
        "Simulation monitoring is not implemented yet.",
        sidebar_title="Simulation",
    )
