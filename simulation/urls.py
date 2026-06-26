from django.urls import path

from simulation import views

app_name = "simulation"

urlpatterns = [
    path("", views.simulation_list, name="simulation_list"),
    path("create/", views.simulation_create, name="simulation_create"),
    path("monitoring/", views.simulation_monitoring, name="simulation_monitoring"),
]
