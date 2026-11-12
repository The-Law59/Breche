# Brèche

Plateforme d'entraînement à la cybersécurité par les CTF, pensée pour les débutants et les étudiants, dans l'esprit de Root-Me.

- **Défis** classés par catégorie et difficulté, avec indices (payants en points), fichiers à télécharger et validation du flag.
- **Parcours guidés** : des leçons courtes qui mènent chacune à un défi d'application. Un parcours terminé donne un badge.
- **Joueurs solo et équipes** : chacun garde son score, une équipe additionne les défis résolus par ses membres (chaque défi compte une fois).
- **Classements** joueurs et équipes, profils publics, fil d'activité.
- **Administration** complète sur `/admin/` pour gérer défis, leçons, annonces et joueurs sans toucher au code.

## Lancer en local

Il faut Python 3.12 ou plus récent.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # 11 défis débutants + 3 parcours
python manage.py createsuperuser    # ton compte administrateur
python manage.py runserver
```

Le site est alors sur http://127.0.0.1:8000 et l'administration sur http://127.0.0.1:8000/admin/.

Pour lancer les tests :

```bash
python manage.py test
```

## Ajouter un défi

1. Va sur `/admin/` → **Défis** → **Ajouter**.
2. Remplis le titre, la catégorie, la difficulté, les points et l'énoncé (Markdown accepté).
3. Saisis le **flag** : il est enregistré sous forme d'empreinte SHA-256 et n'est plus jamais affiché, même aux admins.
4. Ajoute des indices (avec leur coût) et des fichiers si besoin.
5. Coche **Publié** quand le défi est prêt.

Les défis qui demandent un serveur vulnérable (web dynamique, pwn) se déploient **à part**, sur une machine isolée. Ne les fais jamais tourner sur le même serveur que la plateforme. Indique leur adresse dans le champ « Accès ».

## Mettre en ligne

Le plus simple est un petit serveur (VPS) avec Docker :

```bash
cp .env.example .env    # puis remplis les valeurs
docker compose up -d --build
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

L'application écoute sur `127.0.0.1:8000`. Place devant un reverse proxy qui gère le HTTPS (Caddy est le plus simple : `breche.example.fr { reverse_proxy 127.0.0.1:8000 }`).

Variables importantes (voir `.env.example`) :

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète, obligatoire en production |
| `DJANGO_ALLOWED_HOSTS` | Ton nom de domaine |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://` + ton nom de domaine |
| `DATABASE_URL` | Fournie automatiquement par docker-compose |
| `BRECHE_MAX_ATTEMPTS_PER_MINUTE` | Limite anti-bruteforce des flags |
| `BRECHE_TEAM_MAX_SIZE` | Taille maximale d'une équipe |

## Organisation du code

| Dossier | Contenu |
|---|---|
| `accounts/` | Joueurs, équipes, inscription, profils |
| `ctf/` | Catégories, défis, indices, résolutions, classement (`scoring.py`), contenu de démarrage (`seed_data.py`) |
| `learn/` | Parcours, leçons, progression |
| `templates/`, `static/` | Pages HTML, styles et scripts |
| `config/` | Réglages Django |

## Pistes pour la suite

- Réinitialisation du mot de passe par e-mail (nécessite un service d'envoi d'e-mails).
- Limitation des tentatives de connexion.
- Défis dynamiques (une instance Docker par joueur) pour le web et le pwn.
- Événements limités dans le temps (CTF avec date de début et de fin).
- Write-ups des joueurs, visibles après résolution.
