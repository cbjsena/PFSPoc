from collections import defaultdict
import csv
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render

from common.views import menu_placeholder


DATA_DIR = Path(settings.BASE_DIR) / "data"
SCHEDULE_FILE = DATA_DIR / "current_proforma_schedule.csv"
DETAIL_FILE = DATA_DIR / "current_proforma_schedule_detail.csv"
BERTH_WINDOW_FILE = DATA_DIR / "berth_window_status.csv"
RDR_FILE = DATA_DIR / "rdr_status.csv"

TABLE_COLUMNS = [
    ("Schedule", 4),
    ("Calling Ports", 6),
]

TABLE_HEADERS = [
    "Trade",
    "Lane",
    "Capacity",
    "Qty",
    "Port",
    "Terminal",
    "ETB Day",
    "ETB Time",
    "ETD Day",
    "ETD Time",
]

BERTH_TABLE_HEADERS = [
    "Lane",
    "Country",
    "Port",
    "Berth",
    "ETB Day",
    "ETB Time",
    "ETD Day",
    "ETD Time",
    "Loading Volume",
    "Discharging Volume",
    "Productivity",
    "Berthing",
]

RDR_TABLE_HEADERS = [
    "Trade",
    "POL",
    "POD",
    "Demand Value",
]


def input_list(request):
    return redirect("input:current_proforma_schedules")


def current_proforma_schedules(request):
    loaded = request.GET.get("interface") in {"1", "true", "True", "yes", "on"}
    context = {
        "loaded": loaded,
        "table_columns": TABLE_COLUMNS,
        "table_headers": TABLE_HEADERS,
        "display_rows": [],
        "schedule_count": 0,
        "detail_count": 0,
        "row_count": 0,
    }

    if loaded:
        schedule_rows = _read_csv_rows(SCHEDULE_FILE)
        detail_rows = _read_csv_rows(DETAIL_FILE)
        display_rows = _build_display_rows(schedule_rows, detail_rows)

        context.update(
            {
                "display_rows": display_rows,
                "schedule_count": len(schedule_rows),
                "detail_count": len(detail_rows),
                "row_count": len(display_rows),
            }
        )

    return render(request, "input/current_proforma_schedules.html", context)


def berth_window_status(request):
    loaded = request.GET.get("interface") in {"1", "true", "True", "yes", "on"}
    context = {
        "loaded": loaded,
        "table_headers": BERTH_TABLE_HEADERS,
        "rows": [],
        "row_count": 0,
    }

    if loaded:
        rows = _read_csv_rows(BERTH_WINDOW_FILE)
        context.update(
            {
                "rows": rows,
                "row_count": len(rows),
            }
        )

    return render(request, "input/berth_window_status.html", context)


def rdr(request):
    loaded = request.GET.get("interface") in {"1", "true", "True", "yes", "on"}
    context = {
        "loaded": loaded,
        "table_headers": RDR_TABLE_HEADERS,
        "rows": [],
        "row_count": 0,
    }

    if loaded:
        rows = _read_csv_rows(RDR_FILE)
        context.update(
            {
                "rows": rows,
                "row_count": len(rows),
            }
        )

    return render(request, "input/rdr.html", context)


def _read_csv_rows(path):
    if not path.exists():
        raise Http404(f"Missing data file: {path.name}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def _build_display_rows(schedule_rows, detail_rows):
    detail_map = defaultdict(list)
    for row in detail_rows:
        detail_map[row["proforma_number"]].append(row)

    display_rows = []
    for schedule in schedule_rows:
        details = detail_map.get(schedule["proforma_number"], [])
        if details:
            for index, detail in enumerate(details):
                display_rows.append(
                    {
                        "schedule": schedule if index == 0 else None,
                        "detail": detail,
                    }
                )
        else:
            display_rows.append({"schedule": schedule, "detail": None})

    return display_rows
