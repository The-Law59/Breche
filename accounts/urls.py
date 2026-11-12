from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("inscription/", views.signup, name="signup"),
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("mot-de-passe/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("mot-de-passe/ok/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("joueurs/<str:username>/", views.profile, name="profile"),
    path("reglages/", views.settings_view, name="settings"),
    path("equipe/", views.my_team, name="my_team"),
    path("equipe/quitter/", views.team_leave, name="team_leave"),
    path("equipe/nouveau-code/", views.team_new_code, name="team_new_code"),
    path("equipes/<slug:slug>/", views.team_detail, name="team_detail"),
]
