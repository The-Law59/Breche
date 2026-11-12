from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Brèche · administration"
admin.site.site_title = "Brèche"
admin.site.index_title = "Gérer la plateforme"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("parcours/", include("learn.urls")),
    path("", include("ctf.urls")),
]
