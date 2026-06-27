from common.views import menu_placeholder


def result_list(request):
    return menu_placeholder(
        request,
        "Result List",
        "Result screens will be added here.",
        sidebar_title="Result",
    )


def result_cost_calculation(request):
    return menu_placeholder(
        request,
        "Leaderboard",
        "Result leaderboard is not implemented yet.",
        sidebar_title="Result",
    )
