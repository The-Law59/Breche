#!/bin/sh
# Sauvegarde la base de données et les fichiers des défis dans ./sauvegardes/
# À lancer depuis le dossier du projet. Pour l'automatiser chaque nuit (crontab -e) :
#   15 3 * * * cd /opt/breche && ./scripts/sauvegarde.sh >/dev/null 2>&1
set -eu
DEST="sauvegardes"
DATE=$(date +%Y-%m-%d_%H%M)
mkdir -p "$DEST"

docker compose exec -T db pg_dump -U breche breche | gzip > "$DEST/base_$DATE.sql.gz"
docker compose exec -T web tar -C /data -czf - media > "$DEST/fichiers_$DATE.tar.gz"

# Garde les 14 dernières sauvegardes de chaque type
ls -1t "$DEST"/base_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm --
ls -1t "$DEST"/fichiers_*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm --
echo "Sauvegarde terminée : $DEST/*_$DATE.*"
