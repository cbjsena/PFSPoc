# common/context_processors.py
"""항목 C: 모든 템플릿에 메뉴 구조를 자동 전달"""

from common.menus import (
    INPUT_SIDEBAR_MENU,
    RESULT_SIDEBAR_MENU,
    SIMULATION_SIDEBAR_MENU,
    TOP_MENU_ITEMS,
)


def global_menus(request):
    resolver_match = getattr(request, "resolver_match", None)
    app_name = getattr(resolver_match, "app_name", None)
    url_name = getattr(resolver_match, "url_name", None)

    sidebar_menu = []
    if app_name == "input":
        sidebar_menu = INPUT_SIDEBAR_MENU
    elif app_name == "simulation":
        sidebar_menu = SIMULATION_SIDEBAR_MENU
    elif app_name == "result":
        sidebar_menu = RESULT_SIDEBAR_MENU

    return {
        "top_menu_items": TOP_MENU_ITEMS,
        "current_top_menu": app_name,
        "sidebar_menu": sidebar_menu,
        "current_sidebar_menu": url_name,
    }
