from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ctf.models import Category, Solve
from ctf.scoring import player_rank, player_score, ranked_teams
from learn.models import Path

from .forms import ProfileForm, SignupForm, TeamCreateForm, TeamJoinForm
from .models import Team, User


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Bienvenue {user.username} ! Commence par le parcours « Bases du CTF ».")
        return redirect("path_list")
    return render(request, "registration/signup.html", {"form": form})


def profile(request, username):
    player = get_object_or_404(User, username=username, is_active=True)
    solves = Solve.objects.filter(user=player).select_related("challenge__category")
    per_cat = dict(solves.values_list("challenge__category").annotate(n=Count("id")))
    categories = Category.objects.annotate(total=Count("challenges", filter=Q(challenges__is_published=True))).filter(total__gt=0)
    for c in categories:
        c.done = per_cat.get(c.pk, 0)
    paths = Path.objects.filter(is_published=True).annotate(
        n=Count("lessons", distinct=True),
        done=Count("lessons__progress", filter=Q(lessons__progress__user=player), distinct=True),
    )
    return render(request, "accounts/profile.html", {
        "player": player,
        "solves": solves[:30],
        "solve_count": solves.count(),
        "score": player_score(player),
        "rank": player_rank(player),
        "categories": categories,
        "badges": [p for p in paths if p.n and p.done == p.n],
        "is_me": request.user == player,
    })


@login_required
def settings_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil enregistré.")
        return redirect("profile", request.user.username)
    return render(request, "accounts/settings.html", {"form": form})


@login_required
def my_team(request):
    if request.user.team:
        return redirect(request.user.team)
    create_form = TeamCreateForm(prefix="c")
    join_form = TeamJoinForm(prefix="j")
    if request.method == "POST":
        if "create" in request.POST:
            create_form = TeamCreateForm(request.POST, prefix="c")
            if create_form.is_valid():
                with transaction.atomic():
                    team = create_form.save(commit=False)
                    team.captain = request.user
                    team.save()
                    request.user.team = team
                    request.user.save(update_fields=["team"])
                messages.success(request, f"Équipe « {team.name} » créée. Partage le code d'invitation à tes coéquipiers.")
                return redirect(team)
        elif "join" in request.POST:
            join_form = TeamJoinForm(request.POST, prefix="j")
            if join_form.is_valid():
                team = Team.objects.filter(invite_code=join_form.cleaned_data["code"].strip()).first()
                if team is None:
                    join_form.add_error("code", "Ce code ne correspond à aucune équipe.")
                elif team.is_full:
                    join_form.add_error("code", f"Cette équipe est complète ({settings.BRECHE_TEAM_MAX_SIZE} membres maximum).")
                else:
                    request.user.team = team
                    request.user.save(update_fields=["team"])
                    messages.success(request, f"Tu as rejoint « {team.name} ».")
                    return redirect(team)
    return render(request, "accounts/team_join.html", {
        "create_form": create_form, "join_form": join_form, "max_size": settings.BRECHE_TEAM_MAX_SIZE,
    })


def team_detail(request, slug):
    team = get_object_or_404(Team, slug=slug)
    members = team.members.filter(is_active=True)
    for m in members:
        m.score = player_score(m)
    row = next((r for r in ranked_teams() if r["team"].pk == team.pk), None)
    solves = Solve.objects.filter(user__in=members).select_related("challenge__category", "user")[:20]
    return render(request, "accounts/team_detail.html", {
        "team": team, "members": sorted(members, key=lambda m: -m.score), "row": row,
        "rank": (ranked_teams().index(row) + 1) if row else None,
        "solves": solves, "is_member": request.user.is_authenticated and request.user.team_id == team.pk,
        "is_captain": request.user.is_authenticated and team.captain_id == request.user.pk,
        "max_size": settings.BRECHE_TEAM_MAX_SIZE,
    })


@login_required
@require_POST
def team_leave(request):
    team = request.user.team
    if team is None:
        return redirect("my_team")
    with transaction.atomic():
        request.user.team = None
        request.user.save(update_fields=["team"])
        remaining = team.members.order_by("date_joined")
        if not remaining.exists():
            team.delete()
        elif team.captain_id == request.user.pk:
            team.captain = remaining.first()
            team.save(update_fields=["captain"])
    messages.info(request, f"Tu as quitté « {team.name} ».")
    return redirect("my_team")


@login_required
@require_POST
def team_new_code(request):
    team = request.user.team
    if team and team.captain_id == request.user.pk:
        team.regenerate_invite_code()
        messages.success(request, "Nouveau code d'invitation généré. L'ancien ne fonctionne plus.")
        return redirect(team)
    return redirect("my_team")
