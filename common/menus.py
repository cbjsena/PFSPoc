# common/menus.py
"""
메뉴 구조 정의 (항목 C)

3개 대메뉴: Input, Simulation, Result
- 우측 상단에 고정 표시
- 클릭 시 좌측 사이드바에 하위 메뉴 표시
"""


class TopMenu:
    INPUT = "input"
    SIMULATION = "simulation"
    RESULT = "result"


# 상단 고정 메뉴 (우측 상단)
TOP_MENU_ITEMS = [
    {
        "name": "Input",
        "key": TopMenu.INPUT,
        "url_name": "input:input_list",
        "icon": "bi-database",
    },
    {
        "name": "Simulation",
        "key": TopMenu.SIMULATION,
        "url_name": "simulation:simulation_list",
        "icon": "bi-play-circle",
    },
    {
        "name": "Result",
        "key": TopMenu.RESULT,
        "url_name": "result:result_list",
        "icon": "bi-bar-chart-line",
    },
]


# Input 하위 메뉴 (좌측 사이드바)
INPUT_SIDEBAR_MENU = [
    # {
    #     "key": "current_proforma_schedules",
    #     "name": "Current Proforma Schedules",
    #     "url_name": "input:current_proforma_schedules",
    #     "icon": "bi-list-ul",
    # },
    {
        "key": "proforma_schedules",
        "name": "Proforma Schedules",
        "url_name": "input:proforma_schedules",
        "icon": "bi-list-ul",
    },
    {
        "key": "berth_window_status",
        "name": "Berth Window Status",
        "url_name": "input:berth_window_status",
        "icon": "bi-list-ul",
    },
    {
        "key": "rdr",
        "name": "RDR",
        "url_name": "input:rdr",
        "icon": "bi-list-ul",
    },
]


# Simulation 하위 메뉴 (좌측 사이드바)
SIMULATION_SIDEBAR_MENU = [
    {
        "key": "simulation_list",
        "name": "Simulation List",
        "url_name": "simulation:simulation_list",
        "icon": "bi-list-ul",
    },
    {
        "key": "simulation_create",
        "name": "Create Simulation",
        "url_name": "simulation:simulation_create",
        "icon": "bi-plus-circle",
    },
    {
        "key": "simulation_monitoring",
        "name": "Monitoring",
        "url_name": "simulation:simulation_monitoring",
        "icon": "bi-broadcast-pin",
    },
]


# Result 하위 메뉴 (좌측 사이드바)
RESULT_SIDEBAR_MENU = [
    {
        "key": "result_list",
        "name": "Result List",
        "url_name": "result:result_list",
        "icon": "bi-list-ul",
    },
    {
        "key": "result_cost_calculation",
        "name": "Cost Calculation",
        "url_name": "result:result_cost_calculation",
        "icon": "bi-trophy",
    },
]
