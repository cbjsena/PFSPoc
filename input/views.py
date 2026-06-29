from collections import defaultdict
import csv
from pathlib import Path

from django.conf import settings
from django.http import Http404, FileResponse
from django.shortcuts import redirect, render

from input.models import DefaultBerthWindowStatus, DefaultRdrDemand


def _data_dir():
    """Return the current data directory based on settings.BASE_DIR.
    Compute at runtime so tests can override settings.BASE_DIR during execution.
    """
    return Path(settings.BASE_DIR) / "data"


# Helper to get specific files (computed at runtime)
def _schedule_file():
    return _data_dir() / "current_proforma.csv"


def _detail_file():
    return _data_dir() / "current_proforma_detail.csv"


def _berth_window_file():
    return _data_dir() / "berth_window_status.csv"


def _rdr_file():
    return _data_dir() / "rdr_demand.csv"


def _fleet_deploy_plan_file():
    return _data_dir() / "fleet_deploy_plan.csv"

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
    "Total",
    "Productivity",
    "Berthing",
]

RDR_TABLE_HEADERS = [
    "Trade",
    "POL",
    "POD",
    "Demand Value",
]

FLEET_TABLE_HEADERS = [
    "Trade",
    "Lane",
    "Capacity",
    "Qty",
]


def input_list(request):
    return redirect("input:current_proforma")


def current_proforma(request):
    loaded = request.GET.get("interface") in {"1", "true", "True", "yes", "on"}
    schedules = []
    max_ports = 0
    total_details = 0

    if loaded:
        schedule_rows = _read_csv_rows(_schedule_file())
        detail_rows = _read_csv_rows(_detail_file())
        detail_map = defaultdict(list)
        for row in detail_rows:
            detail_map[row["proforma_number"]].append(row)

        for schedule in schedule_rows:
            details = detail_map.get(schedule["proforma_number"], [])
            total_details += len(details)
            for d in details:
                d["duration"] = _calc_duration(d)
                d["etb_time_display"] = _format_time(d.get("etb_time", ""))
                d["etd_time_display"] = _format_time(d.get("etd_time", ""))
            port_count = len(details)
            schedules.append(
                {
                    "trade": schedule["trade"],
                    "lane": schedule["lane"],
                    "capacity": schedule["Capacity"],
                    "qty": schedule["Qty"],
                    "ports": details,
                    "port_count": port_count,
                }
            )
            max_ports = max(max_ports, port_count)

        for s in schedules:
            s["empty_cells"] = [None] * (max_ports - s["port_count"])

    context = {
        "loaded": loaded,
        "schedules": schedules,
        "max_ports": max_ports,
        "total_columns": 5 + max_ports,
        "schedule_count": len(schedules),
        "detail_count": total_details,
        "row_count": len(schedules),
    }
    return render(request, "input/current_proforma.html", context)


def berth_window_status(request):
    loaded = request.GET.get("interface") in {"1", "true", "True", "yes", "on"}
    context = {
        "loaded": loaded,
        "table_headers": BERTH_TABLE_HEADERS,
        "rows": [],
        "row_count": 0,
    }

    if loaded:
        # 지정된 파일에서 가져오기
        # rows = _read_csv_rows(_berth_window_file())
        # context.update(
        #     {
        #         "rows": rows,
        #         "row_count": len(rows),
        #     }
        # )

        # db에서 가져오기
        rows = DefaultBerthWindowStatus.objects.all()
        context.update(
            {
                "rows": rows,
                "row_count": rows.count(),
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
        rows = DefaultRdrDemand.objects.all()
        context.update(
            {
                "rows": rows,
                "row_count": rows.count(),
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


DAY_ORDER = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}


def _format_time(time_str):
    """Format time string for display (strip seconds, handle edge cases)."""
    if not time_str:
        return ""
    time_str = time_str.strip()
    if not time_str:
        return ""
    if ":" not in time_str:
        try:
            val = int(time_str)
            hours = val // 60
            minutes = val % 60
            return f"{hours:02d}:{minutes:02d}"
        except ValueError:
            return time_str
    parts = time_str.split(":")
    return f"{parts[0]}:{parts[1]}"


def _parse_time_minutes(time_str):
    """Parse time string to total minutes from midnight."""
    if not time_str:
        return None
    time_str = time_str.strip()
    if not time_str:
        return None
    if ":" not in time_str:
        try:
            return int(time_str)
        except ValueError:
            return None
    parts = time_str.split(":")
    try:
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return hours * 60 + minutes
    except ValueError:
        return None


def _calc_duration(detail):
    """Calculate duration between ETB and ETD as human-readable string."""
    etb_day = detail.get("etb_day", "").strip().upper()
    etb_time = detail.get("etb_time", "").strip()
    etd_day = detail.get("etd_day", "").strip().upper()
    etd_time = detail.get("etd_time", "").strip()

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

        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"
    except (ValueError, IndexError, TypeError):
        return ""



def csv_download(request, filename):
    """Download a CSV file from the data directory by filename."""
    path = _data_dir() / filename
    if not path.exists():
        raise Http404(f"Missing data file: {filename}")
    return FileResponse(open(path, "rb"), as_attachment=True, filename=filename, content_type="text/csv")


def csv_upload(request, filename):
    """Receive uploaded CSV and save to data directory under the given filename.

    Simple behavior: saves file and redirects back to Referer or input list.
    """
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER", "input:input_list"))

    uploaded = request.FILES.get("csv_file")
    if not uploaded:
        # No file selected — redirect back (view/tests may assert messaging separately)
        return redirect(request.META.get("HTTP_REFERER", "input:input_list"))

    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    dest = data_dir / filename
    # Write uploaded file in binary chunks
    with dest.open("wb") as handle:
        for chunk in uploaded.chunks():
            handle.write(chunk)

    return redirect(request.META.get("HTTP_REFERER", "input:input_list"))
