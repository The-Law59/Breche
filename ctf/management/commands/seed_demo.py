from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from ctf import seed_data
from ctf.models import Announcement, Category, Challenge, Hint
from learn.models import Lesson, Path


class Command(BaseCommand):
    help = "Installe les défis et parcours de démarrage (relançable sans risque : met à jour l'existant)."

    @transaction.atomic
    def handle(self, *args, **opts):
        cats = {}
        for name, slug, color, desc, order in seed_data.CATEGORIES:
            cats[slug], _ = Category.objects.update_or_create(
                slug=slug, defaults={"name": name, "color": color, "description": desc, "order": order}
            )

        challenges = {}
        for i, d in enumerate(seed_data.CHALLENGES):
            ch, _ = Challenge.objects.update_or_create(
                slug=d["slug"],
                defaults={
                    "title": d["title"], "category": cats[d["cat"]], "difficulty": d["difficulty"],
                    "points": d["points"], "description": d["description"].strip(), "author": d.get("author", ""),
                    "connection_info": d.get("connection_info", ""), "is_published": True, "order": i,
                },
            )
            ch.set_flag(d["flag"])
            ch.save(update_fields=["flag_hash"])
            ch.hints.all().delete()
            for order, (text, cost) in enumerate(d.get("hints", [])):
                Hint.objects.create(challenge=ch, text=text, cost=cost, order=order)
            for f in ch.files.all():
                f.file.delete(save=False)
                f.delete()
            for name, content in d.get("files", {}).items():
                cf = ch.files.model(challenge=ch, name=name)
                cf.file.save(name, ContentFile(content), save=True)
            challenges[d["slug"]] = ch

        for p in seed_data.PATHS:
            path, _ = Path.objects.update_or_create(
                slug=p["slug"],
                defaults={"title": p["title"], "level": p["level"], "color": p["color"], "order": p["order"],
                          "summary": p["summary"], "is_published": True},
            )
            for order, (slug, title, minutes, chall, content) in enumerate(p["lessons"]):
                Lesson.objects.update_or_create(
                    path=path, slug=slug,
                    defaults={"title": title, "minutes": minutes, "order": order,
                              "content": content.strip(), "challenge": challenges.get(chall)},
                )

        for title, body in seed_data.ANNOUNCEMENTS:
            Announcement.objects.get_or_create(title=title, defaults={"body": body})

        self.stdout.write(self.style.SUCCESS(
            f"{len(challenges)} défis, {len(seed_data.PATHS)} parcours et {len(cats)} catégories installés."
        ))
