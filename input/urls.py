from django.urls import path

from input import views

app_name = "input"

urlpatterns = [
    path("", views.input_list, name="input_list"),
    path("current-proforma-schedules/", views.current_proforma_schedules, name="current_proforma_schedules"),
    path("proforma-schedules/", views.proforma_schedules, name="proforma_schedules"),
    path("berth-window-status/", views.berth_window_status, name="berth_window_status"),
    path("rdr/", views.rdr, name="rdr"),
    path("fleet-deploy-plan/", views.fleet_deploy_plan, name="fleet_deploy_plan"),

    # CSV download / upload endpoints for input app
    path("csv/download/<str:filename>/", views.csv_download, name="csv_download"),
    path("csv/upload/<str:filename>/", views.csv_upload, name="csv_upload"),
]
