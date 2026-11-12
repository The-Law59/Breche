import bleach
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "table", "thead", "tbody", "tr", "th", "td", "kbd",
}
ALLOWED_ATTRS = {"a": ["href", "title", "rel", "target"], "code": ["class"]}


@register.filter
def markdown(text):
    """Markdown → HTML nettoyé (aucun script ni attribut dangereux ne passe)."""
    html = md.markdown(text or "", extensions=["fenced_code", "tables", "sane_lists"])
    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols={"http", "https", "mailto"})
    clean = bleach.linkify(clean, callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank])
    return mark_safe(clean)


@register.inclusion_tag("ctf/_difficulty.html")
def difficulty(level):
    return {"level": level, "bars": [i <= level for i in range(1, 5)]}


@register.filter
def percent(part, total):
    try:
        return round(100 * part / total) if total else 0
    except (TypeError, ZeroDivisionError):
        return 0
