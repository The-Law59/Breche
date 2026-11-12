# Déployer Brèche sur Proxmox

Ce guide installe Brèche dans une machine virtuelle Debian sur ton Proxmox, puis la rend accessible depuis Internet.

## 1. Créer la machine virtuelle

Une **VM** est préférable à un conteneur LXC : Docker y fonctionne sans réglage particulier et l'isolation avec le reste de ton réseau est meilleure.

| Réglage | Valeur conseillée |
|---|---|
| Image | Debian 12 (netinst) |
| Processeurs | 2 vCPU |
| Mémoire | 2 Go |
| Disque | 20 Go |
| Réseau | un bridge ou un VLAN séparé de ton réseau domestique si possible |

Pendant l'installation de Debian, coche seulement **serveur SSH** et **utilitaires usuels du système**.

> **Isolation** : un site public tourne chez toi. Si ton routeur le permet, place la VM dans une zone séparée (VLAN ou DMZ) pour qu'elle ne puisse pas joindre tes autres appareils. Et quand tu ajouteras des défis avec des serveurs volontairement vulnérables, mets-les dans une **autre** VM, isolée elle aussi.

## 2. Installer Docker

Connecte-toi en SSH à la VM, puis :

```bash
sudo apt update && sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Déconnecte-toi puis reconnecte-toi pour que le dernier réglage s'applique.

## 3. Récupérer et configurer Brèche

```bash
sudo mkdir -p /opt/breche && sudo chown $USER /opt/breche
git clone https://github.com/TON-COMPTE/breche.git /opt/breche
cd /opt/breche
cp .env.example .env
```

Le dépôt est privé : `git clone` te demandera ton identifiant GitHub et un **jeton d'accès** à la place du mot de passe (GitHub → Settings → Developer settings → Personal access tokens, droit de lecture sur le dépôt suffit).

Génère deux secrets :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Ouvre `.env` (`nano .env`) et remplis :

- `DJANGO_SECRET_KEY` : le premier secret ;
- `POSTGRES_PASSWORD` : le second ;
- `DJANGO_ALLOWED_HOSTS` : ton nom de domaine, par exemple `ctf.mondomaine.fr` ;
- `DJANGO_CSRF_TRUSTED_ORIGINS` : `https://ctf.mondomaine.fr`.

Pour un premier essai **uniquement sur ton réseau local** (sans HTTPS), mets plutôt `DJANGO_ALLOWED_HOSTS=IP_DE_LA_VM` et ajoute `DJANGO_HTTPS=0`, et remplace `127.0.0.1:8000:8000` par `8000:8000` dans `docker-compose.yml`. Remets ces réglages avant d'ouvrir le site sur Internet.

## 4. Démarrer

```bash
docker compose up -d --build
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
docker compose ps
```

Les deux conteneurs `db` et `web` doivent être `running` (ou `healthy`).

## 5. Rendre le site accessible depuis Internet

Il te faut un **nom de domaine**. Deux possibilités :

### Option A, conseillée : tunnel Cloudflare

Aucun port à ouvrir sur ta box et l'adresse IP de ta maison reste cachée. Le domaine doit être géré par Cloudflare (gratuit).

1. Dans le tableau de bord Cloudflare : **Zero Trust → Networks → Tunnels → Create a tunnel**, type *Cloudflared*.
2. Copie le jeton affiché (la longue chaîne après `--token`) dans `.env` : `CLOUDFLARE_TUNNEL_TOKEN=...`
3. Dans l'onglet **Public Hostname** du tunnel : sous-domaine `ctf`, domaine `mondomaine.fr`, service `HTTP` → `web:8000`.
4. Démarre le tunnel :

```bash
docker compose --profile tunnel up -d
```

Cloudflare fournit le HTTPS automatiquement.

### Option B : redirection de ports et Caddy

1. Chez ton registrar, crée un enregistrement DNS `A` qui pointe `ctf.mondomaine.fr` vers l'IP publique de ta box (si elle change, utilise un service de DNS dynamique).
2. Sur ta box, redirige les ports **80** et **443** vers l'IP de la VM.
3. Sur la VM, installe Caddy, qui gère le certificat HTTPS tout seul :

```bash
sudo apt install -y caddy
echo 'ctf.mondomaine.fr {
    reverse_proxy 127.0.0.1:8000
}' | sudo tee /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## 6. Sauvegardes

Deux niveaux, les deux sont utiles :

- **Proxmox** : Datacenter → Backup → ajoute une sauvegarde planifiée de la VM (mode *snapshot*), de préférence vers un autre disque.
- **Données** : le script fourni exporte la base et les fichiers des défis.

```bash
chmod +x scripts/sauvegarde.sh
./scripts/sauvegarde.sh
```

Pour le lancer chaque nuit, ajoute la ligne indiquée en haut du script avec `crontab -e`.

## 7. Mettre à jour le site

```bash
cd /opt/breche
git pull
docker compose up -d --build
```

Les migrations de base de données s'appliquent automatiquement au démarrage.

## En cas de problème

| Symptôme | Piste |
|---|---|
| Erreur 400 « Bad Request » | Le nom de domaine n'est pas dans `DJANGO_ALLOWED_HOSTS` |
| Erreur 403 « CSRF » à la connexion | `DJANGO_CSRF_TRUSTED_ORIGINS` doit contenir `https://` + le domaine |
| La page boucle en redirection | Le proxy n'envoie pas l'en-tête HTTPS : vérifie Caddy ou le tunnel |
| Autre erreur | `docker compose logs web --tail 50` |
