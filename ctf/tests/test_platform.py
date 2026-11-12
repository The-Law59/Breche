import base64
import io
import re
import zipfile

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Team, User
from ctf import seed_data
from ctf.models import Category, Challenge, Hint, HintUnlock, Solve, Submission
from ctf.scoring import player_score, ranked_players, ranked_teams
from learn.models import Lesson, LessonProgress


def make_challenge(slug="c1", flag="BRCH{ok}", points=100, published=True):
    cat, _ = Category.objects.get_or_create(slug="web", defaults={"name": "Web", "color": "web"})
    c = Challenge(title=slug, slug=slug, category=cat, points=points, description="x", is_published=published)
    c.set_flag(flag)
    c.save()
    return c


class FlagTests(TestCase):
    def test_flag_is_hashed_and_checked(self):
        c = make_challenge(flag="BRCH{secret}")
        self.assertNotIn("secret", c.flag_hash)
        self.assertTrue(c.check_flag("BRCH{secret}"))
        self.assertTrue(c.check_flag("  BRCH{secret}\n"))
        self.assertFalse(c.check_flag("BRCH{Secret}"))
        self.assertFalse(c.check_flag(""))


class SubmitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="motdepasse-solide-42")
        self.client.force_login(self.user)
        self.c = make_challenge()
        self.url = reverse("submit_flag", args=[self.c.slug])

    def test_correct_flag_creates_single_solve(self):
        self.client.post(self.url, {"flag": "BRCH{ok}"})
        self.client.post(self.url, {"flag": "BRCH{ok}"})
        self.assertEqual(Solve.objects.filter(user=self.user).count(), 1)
        self.assertEqual(player_score(self.user), 100)

    def test_wrong_flag(self):
        self.client.post(self.url, {"flag": "BRCH{nope}"})
        self.assertFalse(Solve.objects.exists())
        self.assertEqual(Submission.objects.filter(correct=False).count(), 1)

    @override_settings(BRECHE_MAX_ATTEMPTS_PER_MINUTE=3)
    def test_rate_limit_blocks_even_correct_flag(self):
        for _ in range(3):
            self.client.post(self.url, {"flag": "BRCH{nope}"})
        self.client.post(self.url, {"flag": "BRCH{ok}"})
        self.assertFalse(Solve.objects.exists())

    def test_anonymous_cannot_submit(self):
        self.client.logout()
        r = self.client.post(self.url, {"flag": "BRCH{ok}"})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Solve.objects.exists())

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_unpublished_challenge_hidden(self):
        hidden = make_challenge("cache", published=False)
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)
        self.client.post(reverse("submit_flag", args=["cache"]), {"flag": "BRCH{ok}"})
        self.assertFalse(Solve.objects.exists())
        self.assertNotContains(self.client.get(reverse("challenge_list")), "/defis/cache/")


class HintTests(TestCase):
    def test_hint_cost_is_subtracted_once(self):
        u = User.objects.create_user("bob", password="motdepasse-solide-42")
        self.client.force_login(u)
        c = make_challenge()
        h = Hint.objects.create(challenge=c, text="regarde mieux", cost=30)
        url = reverse("unlock_hint", args=[c.slug, h.pk])
        r = self.client.get(c.get_absolute_url())
        self.assertNotContains(r, "regarde mieux")
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(HintUnlock.objects.count(), 1)
        self.assertEqual(player_score(u), -30)
        self.assertContains(self.client.get(c.get_absolute_url()), "regarde mieux")


class ScoreboardTests(TestCase):
    def test_ranking_and_teams(self):
        c1, c2 = make_challenge("a", points=100), make_challenge("b", points=50)
        team = Team.objects.create(name="Les Testeurs")
        u1 = User.objects.create_user("u1", team=team)
        u2 = User.objects.create_user("u2", team=team)
        u3 = User.objects.create_user("u3")
        staff = User.objects.create_user("admin", is_staff=True)
        for u, c in [(u1, c1), (u2, c1), (u2, c2), (u3, c2), (staff, c1)]:
            Solve.objects.create(user=u, challenge=c)
        names = [p.username for p in ranked_players()]
        self.assertEqual(names, ["u2", "u1", "u3"])  # staff exclu
        rows = ranked_teams()
        self.assertEqual(rows[0]["score"], 150)  # c1 ne compte qu'une fois
        r = self.client.get(reverse("scoreboard") + "?vue=equipes")
        self.assertContains(r, "Les Testeurs")


class TeamTests(TestCase):
    def setUp(self):
        self.cap = User.objects.create_user("cap", password="motdepasse-solide-42")
        self.client.force_login(self.cap)
        self.client.post(reverse("my_team"), {"create": "1", "c-name": "Root Rangers"})
        self.team = Team.objects.get()

    def test_create_join_leave(self):
        self.assertEqual(self.team.captain, self.cap)
        mate = User.objects.create_user("mate")
        self.client.force_login(mate)
        self.client.post(reverse("my_team"), {"join": "1", "j-code": "mauvais"})
        mate.refresh_from_db()
        self.assertIsNone(mate.team)
        self.client.post(reverse("my_team"), {"join": "1", "j-code": self.team.invite_code})
        mate.refresh_from_db()
        self.assertEqual(mate.team, self.team)
        # le capitaine part : le rôle passe au membre restant
        self.client.force_login(self.cap)
        self.client.post(reverse("team_leave"))
        self.team.refresh_from_db()
        self.assertEqual(self.team.captain, mate)
        # le dernier membre part : l'équipe disparaît
        self.client.force_login(mate)
        self.client.post(reverse("team_leave"))
        self.assertFalse(Team.objects.exists())

    @override_settings(BRECHE_TEAM_MAX_SIZE=1)
    def test_full_team(self):
        other = User.objects.create_user("other")
        self.client.force_login(other)
        self.client.post(reverse("my_team"), {"join": "1", "j-code": self.team.invite_code})
        other.refresh_from_db()
        self.assertIsNone(other.team)

    def test_invite_code_private(self):
        self.client.logout()
        self.assertNotContains(self.client.get(self.team.get_absolute_url()), self.team.invite_code)


class SignupTests(TestCase):
    def test_signup_logs_in(self):
        r = self.client.post(reverse("signup"), {
            "username": "nouveau", "email": "n@example.org", "school": "IUT",
            "password1": "un-mot-de-passe-long", "password2": "un-mot-de-passe-long",
        })
        self.assertRedirects(r, reverse("path_list"))
        self.assertTrue(User.objects.filter(username="nouveau").exists())


class SeedTests(TestCase):
    """Le contenu de démarrage doit être installable et chaque défi réellement résoluble."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())
        call_command("seed_demo", stdout=io.StringIO())  # idempotent

    def test_all_flags_validate(self):
        self.assertEqual(Challenge.objects.count(), len(seed_data.CHALLENGES))
        for d in seed_data.CHALLENGES:
            ch = Challenge.objects.get(slug=d["slug"])
            self.assertTrue(ch.check_flag(d["flag"]), d["slug"])
            self.assertNotIn(d["flag"], ch.description) if d["slug"] != "bienvenue" else None

    def test_challenges_are_solvable_from_their_material(self):
        get = lambda slug: Challenge.objects.get(slug=slug)
        block = lambda slug: re.search(r"```\n(.+?)\n```", get(slug).description, re.S).group(1).strip()
        self.assertEqual(seed_data.caesar(block("cesar-en-vacances"), -3), seed_data.F_CAESAR)
        b64 = block("base64").split("=", 1)[1]
        self.assertEqual(base64.b64decode(b64).decode(), seed_data.F_B64)
        self.assertEqual(bytes.fromhex(block("hexadecimal").replace(" ", "")).decode(), seed_data.F_HEX)
        data = bytes.fromhex(block("xor-un-octet"))
        key = data[0] ^ ord("B")
        self.assertEqual(bytes(b ^ key for b in data).decode(), seed_data.F_XOR)

        def file_bytes(slug):
            f = get(slug).files.get()
            with f.file.open("rb") as h:
                return h.read()
        html = file_bytes("code-source").decode()
        parts = re.search(r"const morceaux = \[(.+?)\]", html).group(1)
        self.assertEqual("".join(re.findall(r"'([^']*)'", parts)), seed_data.F_SOURCE)
        z = zipfile.ZipFile(io.BytesIO(file_bytes("mauvaise-extension")))
        self.assertEqual(z.read("flag.txt").decode().strip(), seed_data.F_ZIP)
        self.assertIn(seed_data.F_META.encode(), file_bytes("metadonnees"))
        auth = re.search(r"Authorization: Basic (\S+)", file_bytes("authentification-basique").decode()).group(1)
        self.assertEqual(base64.b64decode(auth).decode().split(":", 1)[1], seed_data.F_BASIC)
        acro = "".join(l.lstrip("> ")[0] for l in get("acrostiche").description.splitlines() if l.startswith(">"))
        self.assertEqual(f"BRCH{{{acro.lower()}}}", seed_data.F_ACRO)
        secret = re.search(r'SECRET = "(.+)"', file_bytes("coffre-fort").decode()).group(1)
        self.assertEqual(secret[::-1], seed_data.F_REV)

    def test_pages_render(self):
        u = User.objects.create_user("joueur", password="motdepasse-solide-42")
        self.client.force_login(u)
        ch = Challenge.objects.get(slug="bienvenue")
        self.client.post(reverse("submit_flag", args=[ch.slug]), {"flag": seed_data.F_WELCOME})
        lesson = Lesson.objects.first()
        self.client.post(reverse("complete_lesson", args=[lesson.path.slug, lesson.slug]))
        self.assertTrue(LessonProgress.objects.filter(user=u).exists())
        urls = [reverse("home"), reverse("challenge_list"), reverse("scoreboard"), reverse("path_list"),
                reverse("profile", args=["joueur"]), reverse("my_team"), reverse("settings")]
        urls += [c.get_absolute_url() for c in Challenge.objects.all()]
        urls += [l.get_absolute_url() for l in Lesson.objects.all()] + [l.path.get_absolute_url() for l in Lesson.objects.all()]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for f in Challenge.objects.get(slug="coffre-fort").files.all():
            r = self.client.get(reverse("download_file", args=[f.pk]))
            self.assertEqual(r.status_code, 200)
            self.assertIn("attachment", r["Content-Disposition"])
        self.client.logout()
        self.assertEqual(self.client.get(reverse("download_file", args=[f.pk])).status_code, 302)
        for url in [reverse("home"), reverse("challenge_list"), reverse("path_list"), reverse("login"), reverse("signup")]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_markdown_is_sanitized(self):
        from ctf.templatetags.breche import markdown
        out = markdown("<script>alert(1)</script> [x](javascript:alert(1)) **gras**")
        self.assertNotIn("<script", out)
        self.assertNotIn("javascript:", out)
        self.assertIn("<strong>gras</strong>", out)
