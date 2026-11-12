from django.conf import settings

from .scoring import player_score


def player(request):
    ctx = {"FLAG_FORMAT": settings.BRECHE_FLAG_FORMAT}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        ctx["my_score"] = player_score(user)
    return ctx
