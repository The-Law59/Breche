import hashlib
import hmac

from django.conf import settings
from django.db import models
from django.urls import reverse


def hash_flag(raw: str) -> str:
    """Les flags ne sont jamais stockés en clair : seulement leur empreinte SHA-256."""
    return hashlib.sha256(raw.strip().encode("utf-8")).hexdigest()


class Category(models.Model):
    COLORS = [
        ("intro", "Découverte"), ("web", "Web"), ("crypto", "Crypto"), ("foren", "Forensics"),
        ("rev", "Reverse"), ("pwn", "Pwn"), ("osint", "OSINT"), ("steg", "Stégano"), ("net", "Réseau"),
    ]
    name = models.CharField("nom", max_length=40, unique=True)
    slug = models.SlugField(unique=True)
    color = models.CharField("couleur", max_length=10, choices=COLORS, default="intro")
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        verbose_name = "catégorie"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Challenge(models.Model):
    class Difficulty(models.IntegerChoices):
        EASY = 1, "Facile"
        MEDIUM = 2, "Moyen"
        HARD = 3, "Difficile"
        INSANE = 4, "Insane"

    title = models.CharField("titre", max_length=80)
    slug = models.SlugField(max_length=90, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="challenges", verbose_name="catégorie")
    difficulty = models.PositiveSmallIntegerField("difficulté", choices=Difficulty.choices, default=Difficulty.EASY)
    points = models.PositiveIntegerField(default=100)
    description = models.TextField(help_text="Markdown accepté.")
    connection_info = models.CharField(
        "accès", max_length=200, blank=True,
        help_text="Ex. : nc chall.breche.io 9001 ou une URL. Laisse vide si le défi est hors ligne.",
    )
    author = models.CharField("auteur", max_length=40, blank=True)
    flag_hash = models.CharField(max_length=64, editable=False)
    is_published = models.BooleanField("publié", default=False)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "défi"
        ordering = ["category__order", "difficulty", "points", "order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("challenge_detail", args=[self.slug])

    def set_flag(self, raw: str):
        self.flag_hash = hash_flag(raw)

    def check_flag(self, raw: str) -> bool:
        return bool(self.flag_hash) and hmac.compare_digest(hash_flag(raw), self.flag_hash)


class ChallengeFile(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="files")
    file = models.FileField("fichier", upload_to="challenges/%Y/")
    name = models.CharField("nom affiché", max_length=100, blank=True)

    class Meta:
        verbose_name = "fichier"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.name or self.file.name.rsplit("/", 1)[-1]


class Hint(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="hints")
    text = models.TextField("texte")
    cost = models.PositiveIntegerField("coût", default=0, help_text="Points retirés au joueur qui le débloque.")
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        verbose_name = "indice"
        ordering = ["order", "id"]

    def __str__(self):
        return f"Indice {self.order} · {self.challenge}"


class HintUnlock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hint_unlocks")
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name="unlocks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "hint"], name="unique_hint_unlock")]


class Solve(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="solves")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="solves")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "résolution"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "challenge"], name="unique_solve")]

    def __str__(self):
        return f"{self.user} → {self.challenge}"


class Submission(models.Model):
    """Trace de chaque tentative, pour limiter le bruteforce. Le flag tenté n'est pas conservé."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "tentative"
        ordering = ["-created_at"]


class Announcement(models.Model):
    title = models.CharField("titre", max_length=120)
    body = models.TextField("texte", blank=True)
    is_published = models.BooleanField("publiée", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "annonce"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
