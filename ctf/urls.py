from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("defis/", views.challenge_list, name="challenge_list"),
    path("defis/<slug:slug>/", views.challenge_detail, name="challenge_detail"),
    path("defis/<slug:slug>/valider/", views.submit_flag, name="submit_flag"),
    path("defis/<slug:slug>/indices/<int:hint_id>/", views.unlock_hint, name="unlock_hint"),
    path("fichiers/<int:pk>/", views.download_file, name="download_file"),
    path("classement/", views.scoreboard, name="scoreboard"),
]
