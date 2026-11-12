from django.contrib import admin

from .models import Lesson, Path


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 0
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("challenge",)


@admin.register(Path)
class PathAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "order", "is_published")
    list_editable = ("order", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]
