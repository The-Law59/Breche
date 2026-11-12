from django.conf import settings
from django.db import models
from django.urls import reverse


class Path(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "debutant", "Débutant"
        INTERMEDIATE = "intermediaire", "Intermédiaire"
        ADVANCED = "avance", "Avancé"

    title = models.CharField("titre", max_length=80)
    slug = models.SlugField(unique=True)
    level = models.CharField("niveau", max_length=15, choices=Level.choices, default=Level.BEGINNER)
    summary = models.CharField("résumé", max_length=240)
    color = models.CharField("couleur", max_length=10, default="intro", help_text="Même code que les catégories (web, crypto…).")
    order = models.PositiveSmallIntegerField("ordre", default=0)
    is_published = models.BooleanField("publié", default=False)

    class Meta:
        verbose_name = "parcours"
        verbose_name_plural = "parcours"
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("path_detail", args=[self.slug])


class Lesson(models.Model):
    path = models.ForeignKey(Path, on_delete=models.CASCADE, related_name="lessons", verbose_name="parcours")
    title = models.CharField("titre", max_length=100)
    slug = models.SlugField(max_length=110)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    minutes = models.PositiveSmallIntegerField("durée (min)", default=10)
    content = models.TextField("contenu", help_text="Markdown accepté.")
    challenge = models.ForeignKey(
        "ctf.Challenge", null=True, blank=True, on_delete=models.SET_NULL, related_name="lessons",
        verbose_name="défi d'application",
    )

    class Meta:
        verbose_name = "leçon"
        ordering = ["path", "order", "id"]
        constraints = [models.UniqueConstraint(fields=["path", "slug"], name="unique_lesson_slug")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lesson_detail", args=[self.path.slug, self.slug])


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="unique_lesson_progress")]
