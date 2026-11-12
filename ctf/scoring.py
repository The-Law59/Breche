"""Calcul des scores.

Score d'un joueur = somme des points des défis résolus − coût des indices débloqués.
Score d'une équipe = chaque défi compte une seule fois, même si plusieurs membres l'ont
résolu ; on retire les indices débloqués par ses membres (chacun une seule fois).
À égalité, celui qui a atteint son score en premier passe devant.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, IntegerField, Max, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from .models import HintUnlock, Solve


def _sum_subquery(qs, field):
    return Coalesce(
        Subquery(
            qs.filter(user=OuterRef("pk")).values("user").annotate(t=Sum(field)).values("t"),
            output_field=IntegerField(),
        ),
        Value(0),
    )


def ranked_players():
    User = get_user_model()
    return (
        User.objects.filter(is_active=True, is_staff=False)
        .annotate(
            solve_points=_sum_subquery(Solve.objects.all(), "challenge__points"),
            hint_points=_sum_subquery(HintUnlock.objects.all(), "hint__cost"),
            solve_count=Count("solves", distinct=True),
            last_solve=Max("solves__created_at"),
        )
        .filter(solve_count__gt=0)
        .select_related("team")
        .order_by("-solve_points", "hint_points", "last_solve")
    )


def player_score(user):
    solved = Solve.objects.filter(user=user).aggregate(t=Sum("challenge__points"))["t"] or 0
    hints = HintUnlock.objects.filter(user=user).aggregate(t=Sum("hint__cost"))["t"] or 0
    return solved - hints


def player_rank(user):
    """Rang du joueur (1 = premier), ou None s'il n'a encore rien résolu."""
    for i, p in enumerate(ranked_players(), start=1):
        if p.pk == user.pk:
            return i
    return None


def ranked_teams():
    from accounts.models import Team

    rows = []
    teams = Team.objects.prefetch_related("members").all()
    for team in teams:
        member_ids = [m.pk for m in team.members.all() if not m.is_staff]
        if not member_ids:
            continue
        firsts = {}
        for s in Solve.objects.filter(user_id__in=member_ids).select_related("challenge").order_by("created_at"):
            firsts.setdefault(s.challenge_id, s)
        if not firsts:
            continue
        hints = (
            HintUnlock.objects.filter(user_id__in=member_ids)
            .values("hint_id", "hint__cost").distinct()
        )
        hint_cost = sum(h["hint__cost"] for h in hints)
        rows.append({
            "team": team,
            "score": sum(s.challenge.points for s in firsts.values()) - hint_cost,
            "solve_count": len(firsts),
            "member_count": len(member_ids),
            "last_solve": max(s.created_at for s in firsts.values()),
        })
    rows.sort(key=lambda r: (-r["score"], r["last_solve"]))
    return rows
