from django.urls import path

from result import views

app_name = "result"

urlpatterns = [
    path("", views.result_list, name="result_list"),
    path("leaderboard/", views.result_leaderboard, name="result_leaderboard"),
]
