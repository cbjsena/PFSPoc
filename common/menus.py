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
    {
        "key": "rdr",
        "name": "RDR",
        "url_name": "input:rdr",
        "icon": "bi-list-ul",
    },
    {
        "key": "current_proforma",
        "name": "Current Proforma",
        "url_name": "input:current_proforma",
        "icon": "bi-list-ul",
    },
    {
        "key": "berth_window_status",
        "name": "Berth Window Status",
        "url_name": "input:berth_window_status",
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
        "key": "port_creation",
        "name": "Port Creation",
        "url_name": "simulation:port_creation",
        "icon": "bi-list-ul",
    },
    {
        "key": "pfs_creation",
        "name": "PFS Creation",
        "url_name": "simulation:pfs_creation",
        "icon": "bi-list-ul",
    },
    {
        "key": "created_result",
        "name": "Created Results",
        "url_name": "simulation:created_result",
        "icon": "bi-list-ul",
    },
    {
        "key": "berth_windows_adjustment",
        "name": "Berth Windows Adjustment",
        "url_name": "simulation:berth_windows_adjustment",
        "icon": "bi-list-ul",
    },
    {
        "key": "created_result_adjustment",
        "name": "Created Result Adjustment",
        "url_name": "simulation:created_result_adjustment",
        "icon": "bi-list-ul",
    }
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
    {
        "key": "result_detail",
        "name": "Result Detail",
        "url_name": "result:result_detail",
        "icon": "bi-trophy",
    },
]
