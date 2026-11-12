from django.urls import path

from . import views

urlpatterns = [
    path("", views.path_list, name="path_list"),
    path("<slug:slug>/", views.path_detail, name="path_detail"),
    path("<slug:path_slug>/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("<slug:path_slug>/<slug:slug>/terminer/", views.complete_lesson, name="complete_lesson"),
]
