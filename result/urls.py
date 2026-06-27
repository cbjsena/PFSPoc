from django.urls import path

from result import views

app_name = "result"

urlpatterns = [
    path("", views.result_list, name="result_list"),
    path("cost-calculation/", views.result_cost_calculation, name="result_cost_calculation"),
]
