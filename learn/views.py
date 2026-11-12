from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Lesson, LessonProgress, Path


def _done_ids(user):
    if not user.is_authenticated:
        return set()
    return set(LessonProgress.objects.filter(user=user).values_list("lesson_id", flat=True))


def path_list(request):
    done = _done_ids(request.user)
    paths = Path.objects.filter(is_published=True).prefetch_related("lessons").annotate(n=Count("lessons"))
    for p in paths:
        p.lesson_list = list(p.lessons.all())
        p.done = sum(1 for l in p.lesson_list if l.pk in done)
        for l in p.lesson_list:
            l.is_done = l.pk in done
    return render(request, "learn/path_list.html", {"paths": paths})


def path_detail(request, slug):
    path = get_object_or_404(Path, slug=slug, is_published=True)
    done = _done_ids(request.user)
    lessons = list(path.lessons.select_related("challenge"))
    for l in lessons:
        l.is_done = l.pk in done
    next_lesson = next((l for l in lessons if not l.is_done), None)
    return render(request, "learn/path_detail.html", {
        "path": path, "lessons": lessons, "next_lesson": next_lesson,
        "done": sum(l.is_done for l in lessons), "total": len(lessons),
    })


def lesson_detail(request, path_slug, slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related("path", "challenge"), path__slug=path_slug, slug=slug, path__is_published=True
    )
    lessons = list(lesson.path.lessons.all())
    i = lessons.index(lesson)
    done = _done_ids(request.user)
    return render(request, "learn/lesson_detail.html", {
        "lesson": lesson, "lessons": lessons, "done_ids": done,
        "is_done": lesson.pk in done,
        "prev": lessons[i - 1] if i > 0 else None,
        "next": lessons[i + 1] if i + 1 < len(lessons) else None,
        "position": i + 1,
    })


@login_required
@require_POST
def complete_lesson(request, path_slug, slug):
    lesson = get_object_or_404(Lesson, path__slug=path_slug, slug=slug, path__is_published=True)
    LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    messages.success(request, f"Leçon « {lesson.title} » terminée.")
    nxt = lesson.path.lessons.filter(order__gt=lesson.order).first()
    return redirect(nxt or lesson.path)
