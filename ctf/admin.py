from django import forms
from django.contrib import admin
from django.db.models import Count

from .models import Announcement, Category, Challenge, ChallengeFile, Hint, Solve, Submission


class ChallengeAdminForm(forms.ModelForm):
    flag = forms.CharField(
        label="Flag", required=False, widget=forms.TextInput(attrs={"size": 60, "autocomplete": "off"}),
        help_text="Saisis le flag exact (ex. BRCH{...}). Il est enregistré sous forme d'empreinte et ne "
                  "sera plus jamais affiché. Laisse vide pour garder le flag actuel.",
    )

    class Meta:
        model = Challenge
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if not self.instance.flag_hash and not data.get("flag"):
            self.add_error("flag", "Un nouveau défi doit avoir un flag.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("flag"):
            obj.set_flag(self.cleaned_data["flag"])
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class HintInline(admin.TabularInline):
    model = Hint
    extra = 0


class FileInline(admin.TabularInline):
    model = ChallengeFile
    extra = 0


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    form = ChallengeAdminForm
    list_display = ("title", "category", "difficulty", "points", "is_published", "nb_solves")
    list_filter = ("is_published", "category", "difficulty")
    list_editable = ("is_published",)
    search_fields = ("title", "description", "author")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [HintInline, FileInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "difficulty", "points", "author", "is_published", "order")}),
        ("Énoncé", {"fields": ("description", "connection_info")}),
        ("Validation", {"fields": ("flag",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_n=Count("solves"))

    @admin.display(description="Résolutions", ordering="_n")
    def nb_solves(self, obj):
        return obj._n


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "order")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Solve)
class SolveAdmin(admin.ModelAdmin):
    list_display = ("user", "challenge", "created_at")
    list_filter = ("challenge__category",)
    search_fields = ("user__username", "challenge__title")
    date_hierarchy = "created_at"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "challenge", "correct", "created_at")
    list_filter = ("correct",)
    search_fields = ("user__username", "challenge__title")
    date_hierarchy = "created_at"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "created_at")
    list_editable = ("is_published",)
