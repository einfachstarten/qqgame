#!/bin/bash

# Quick Deploy - Für schnelle Updates ohne viel Gefrage

echo "⚡ Quick Deploy gestartet..."

cd /home/QQgame/qqgame

# Commit-Message aus Parameter oder Standard
COMMIT_MSG="${1:-Auto-Update $(date '+%H:%M')}"

echo "📝 Commit: $COMMIT_MSG"

# Alles in einem Rutsch
git add . && \
git commit -m "$COMMIT_MSG" && \
git push origin master && \
touch /var/www/qqgame_pythonanywhere_com_wsgi.py

if [ $? -eq 0 ]; then
    echo "✅ Deployment erfolgreich!"
    echo "🌐 https://qqgame.pythonanywhere.com"
else
    echo "❌ Fehler beim Deployment"
    exit 1
fi