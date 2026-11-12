from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Team, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "team", "school", "is_staff", "date_joined")
    list_filter = BaseUserAdmin.list_filter + ("team",)
    fieldsets = BaseUserAdmin.fieldsets + (("Brèche", {"fields": ("team", "school", "bio")}),)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "captain", "created_at")
    search_fields = ("name",)
    readonly_fields = ("invite_code",)
