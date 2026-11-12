import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def new_invite_code():
    return secrets.token_urlsafe(9)


class Team(models.Model):
    name = models.CharField("nom", max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    invite_code = models.CharField("code d'invitation", max_length=16, unique=True, default=new_invite_code)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="capitaine",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "équipe"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:40] or "equipe"
            slug, n = base, 2
            while Team.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("team_detail", args=[self.slug])

    @property
    def is_full(self):
        return self.members.count() >= settings.BRECHE_TEAM_MAX_SIZE

    def regenerate_invite_code(self):
        self.invite_code = new_invite_code()
        self.save(update_fields=["invite_code"])


class User(AbstractUser):
    team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="members", verbose_name="équipe",
    )
    school = models.CharField("établissement", max_length=80, blank=True)
    bio = models.CharField("présentation", max_length=200, blank=True)

    class Meta:
        verbose_name = "joueur"

    def get_absolute_url(self):
        return reverse("profile", args=[self.username])

    @property
    def initials(self):
        return (self.username[:2] or "?").upper()
