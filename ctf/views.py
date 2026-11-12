from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Min
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from learn.models import Path

from .models import Announcement, Category, Challenge, ChallengeFile, Hint, HintUnlock, Solve, Submission
from .scoring import player_rank, ranked_players, ranked_teams


def _published():
    return Challenge.objects.filter(is_published=True)


def home(request):
    challenges = _published()
    total = challenges.count()
    recent = list(Solve.objects.select_related("user", "challenge__category").filter(user__is_staff=False)[:8])
    firsts = dict(
        Solve.objects.filter(challenge__in={s.challenge_id for s in recent}, user__is_staff=False)
        .values_list("challenge").annotate(first=Min("created_at"))
    )
    for s in recent:
        s.is_first_blood = firsts.get(s.challenge_id) == s.created_at

    categories = (
        Category.objects.filter(challenges__is_published=True)
        .annotate(total=Count("challenges", distinct=True)).order_by("order")
    )
    ctx = {
        "total_challenges": total,
        "recent_solves": recent,
        "announcements": Announcement.objects.filter(is_published=True)[:3],
        "paths": Path.objects.filter(is_published=True).annotate(n=Count("lessons"))[:4],
        "player_count": ranked_players().count(),
    }
    if request.user.is_authenticated:
        solved_ids = set(request.user.solves.values_list("challenge_id", flat=True))
        per_cat = (
            Solve.objects.filter(user=request.user, challenge__is_published=True)
            .values("challenge__category").annotate(n=Count("id"))
        )
        done = {r["challenge__category"]: r["n"] for r in per_cat}
        for c in categories:
            c.done = done.get(c.pk, 0)
        next_up = (
            challenges.exclude(pk__in=solved_ids).select_related("category")
            .annotate(solve_count=Count("solves", distinct=True)).order_by("difficulty", "points")[:3]
        )
        ctx.update(solved_count=len(solved_ids & set(challenges.values_list("pk", flat=True))),
                   rank=player_rank(request.user), next_challenges=next_up)
    ctx["categories"] = categories
    return render(request, "ctf/home.html", ctx)


def challenge_list(request):
    challenges = (
        _published().select_related("category")
        .annotate(solve_count=Count("solves", distinct=True))
    )
    solved_ids = set()
    if request.user.is_authenticated:
        solved_ids = set(request.user.solves.values_list("challenge_id", flat=True))
    for c in challenges:
        c.is_solved = c.pk in solved_ids
    categories = Category.objects.filter(challenges__is_published=True).annotate(
        total=Count("challenges", distinct=True)).order_by("order")
    return render(request, "ctf/challenge_list.html", {
        "challenges": challenges, "categories": categories,
        "solved_count": len(solved_ids & {c.pk for c in challenges}),
    })


def challenge_detail(request, slug):
    challenge = get_object_or_404(_published().select_related("category"), slug=slug)
    solves = challenge.solves.select_related("user").filter(user__is_staff=False).order_by("created_at")
    hints = list(challenge.hints.all())
    is_solved = False
    if request.user.is_authenticated:
        is_solved = challenge.solves.filter(user=request.user).exists()
        unlocked = set(HintUnlock.objects.filter(user=request.user, hint__challenge=challenge).values_list("hint_id", flat=True))
        for h in hints:
            h.is_unlocked = h.pk in unlocked
    return render(request, "ctf/challenge_detail.html", {
        "challenge": challenge,
        "files": challenge.files.all(),
        "hints": hints,
        "is_solved": is_solved,
        "solve_count": solves.count(),
        "first_solvers": solves[:5],
        "lessons": challenge.lessons.filter(path__is_published=True).select_related("path"),
    })


@login_required
@require_POST
def submit_flag(request, slug):
    challenge = get_object_or_404(_published(), slug=slug)
    if challenge.solves.filter(user=request.user).exists():
        messages.info(request, "Tu as déjà résolu ce défi.")
        return redirect(challenge)

    since = timezone.now() - timedelta(minutes=1)
    recent = Submission.objects.filter(user=request.user, created_at__gte=since).count()
    if recent >= settings.BRECHE_MAX_ATTEMPTS_PER_MINUTE:
        messages.error(request, "Trop de tentatives en une minute. Attends un peu avant de réessayer.")
        return redirect(challenge)

    flag = request.POST.get("flag", "")[:200]
    correct = challenge.check_flag(flag)
    Submission.objects.create(user=request.user, challenge=challenge, correct=correct)
    if correct:
        try:
            with transaction.atomic():
                Solve.objects.create(user=request.user, challenge=challenge)
        except IntegrityError:
            pass
        messages.success(request, f"Flag correct ! +{challenge.points} points.")
    elif not flag.strip():
        messages.error(request, "Saisis un flag avant de valider.")
    else:
        messages.error(request, f"Flag incorrect. Vérifie la casse et le format {settings.BRECHE_FLAG_FORMAT}.")
    return redirect(challenge)


@login_required
@require_POST
def unlock_hint(request, slug, hint_id):
    challenge = get_object_or_404(_published(), slug=slug)
    hint = get_object_or_404(Hint, pk=hint_id, challenge=challenge)
    _, created = HintUnlock.objects.get_or_create(user=request.user, hint=hint)
    if created and hint.cost:
        messages.info(request, f"Indice débloqué : −{hint.cost} points.")
    return redirect(f"{challenge.get_absolute_url()}#indices")


@login_required
def download_file(request, pk):
    f = get_object_or_404(ChallengeFile.objects.select_related("challenge"), pk=pk)
    if not f.challenge.is_published and not request.user.is_staff:
        raise Http404
    try:
        handle = f.file.open("rb")
    except FileNotFoundError:
        raise Http404
    return FileResponse(handle, as_attachment=True, filename=f.display_name)


def scoreboard(request):
    view = "equipes" if request.GET.get("vue") == "equipes" else "joueurs"
    ctx = {"view": view}
    if view == "joueurs":
        ctx["players"] = ranked_players()[:200]
    else:
        ctx["teams"] = ranked_teams()[:200]
    return render(request, "ctf/scoreboard.html", ctx)
