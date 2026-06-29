from django.urls import path

from simulation import views

app_name = "simulation"

urlpatterns = [
    path("", views.simulation_list, name="simulation_list"),
    path("simulation-monitoring", views.simulation_monitoring, name="simulation_monitoring"),
    path("simulation-creation/", views.simulation_creation, name="simulation_creation"),
    path("pfs-creation/", views.pfs_creation, name="pfs_creation"),
    path("created-result/", views.created_result, name="created_result"),
    path("berth-windows-adjustment/", views.berth_windows_adjustment, name="berth_windows_adjustment"),
    path("created-result-adjustment/", views.created_result_adjustment, name="created_result_adjustment"),
]
