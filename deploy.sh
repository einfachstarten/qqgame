#!/bin/bash

# QQGame Deployment Script
# Automatisiert Git-Commits, Pushes und Server-Neustarts

echo "🚀 QQGame Deployment Script gestartet..."
echo "=========================================="

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arbeitsverzeichnis
PROJECT_DIR="/home/QQgame/qqgame"
cd "$PROJECT_DIR"

echo -e "${BLUE}📁 Arbeitsverzeichnis: $(pwd)${NC}"

# 1. Git Status prüfen
echo -e "\n${YELLOW}1. Git Status prüfen...${NC}"
git status

# 2. Untracked Files anzeigen
echo -e "\n${YELLOW}2. Neue/geänderte Dateien:${NC}"
git diff --name-status

# 3. Benutzer fragen ob fortfahren
echo -e "\n${YELLOW}Möchtest du diese Änderungen committen und pushen?${NC}"
read -p "Commit-Message eingeben (oder Enter für Standard-Message): " commit_message

# Standard-Message falls leer
if [ -z "$commit_message" ]; then
    commit_message="Automatisches Deployment $(date '+%Y-%m-%d %H:%M:%S')"
fi

echo -e "\n${BLUE}📝 Commit-Message: $commit_message${NC}"

# 4. Alle Änderungen hinzufügen
echo -e "\n${YELLOW}3. Dateien zu Git hinzufügen...${NC}"
git add .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ git add erfolgreich${NC}"
else
    echo -e "${RED}❌ git add fehlgeschlagen${NC}"
    exit 1
fi

# 5. Commit erstellen
echo -e "\n${YELLOW}4. Commit erstellen...${NC}"
git commit -m "$commit_message"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Commit erfolgreich erstellt${NC}"
elif [ $? -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Keine Änderungen zum committen${NC}"
    echo -e "${BLUE}Soll trotzdem versucht werden zu pushen? (y/n)${NC}"
    read -p "" push_anyway
    if [ "$push_anyway" != "y" ]; then
        echo -e "${YELLOW}Deployment abgebrochen${NC}"
        exit 0
    fi
else
    echo -e "${RED}❌ Commit fehlgeschlagen${NC}"
    exit 1
fi

# 6. Push zu GitHub
echo -e "\n${YELLOW}5. Push zu GitHub...${NC}"
echo -e "${BLUE}Pushing zu origin master...${NC}"

git push origin master

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Push zu GitHub erfolgreich${NC}"
else
    echo -e "${RED}❌ Push fehlgeschlagen${NC}"
    echo -e "${YELLOW}Möchtest du trotzdem fortfahren? (y/n)${NC}"
    read -p "" continue_deploy
    if [ "$continue_deploy" != "y" ]; then
        exit 1
    fi
fi

# 7. PythonAnywhere Web App neustarten
echo -e "\n${YELLOW}6. PythonAnywhere Web App neustarten...${NC}"

# API-Aufruf für Webapp-Neustart (funktioniert in PythonAnywhere Console)
echo -e "${BLUE}Starte Web App neu...${NC}"

# Verschiedene Methoden für Neustart versuchen
if command -v pa_reload_webapp.py &> /dev/null; then
    pa_reload_webapp.py qqgame.pythonanywhere.com
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Web App erfolgreich neugestartet${NC}"
    else
        echo -e "${YELLOW}⚠️  Automatischer Neustart fehlgeschlagen${NC}"
        echo -e "${BLUE}Bitte manuell in der PythonAnywhere Web-Konsole neustarten${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  pa_reload_webapp.py nicht gefunden${NC}"
    echo -e "${BLUE}Alternative: Berühre WSGI-Datei für Neustart...${NC}"
    touch /var/www/qqgame_pythonanywhere_com_wsgi.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ WSGI-Datei berührt - App sollte neustarten${NC}"
    else
        echo -e "${YELLOW}⚠️  Bitte manuell neustarten: https://www.pythonanywhere.com/user/QQgame/webapps/qqgame.pythonanywhere.com${NC}"
    fi
fi

# 8. Zusammenfassung
echo -e "\n${GREEN}=========================================="
echo -e "🎉 DEPLOYMENT ABGESCHLOSSEN! 🎉"
echo -e "==========================================${NC}"
echo -e "${BLUE}📊 Zusammenfassung:${NC}"
echo -e "   • Commit: $commit_message"
echo -e "   • Repository: https://github.com/einfachstarten/qqgame"
echo -e "   • Live-Site: https://qqgame.pythonanywhere.com"
echo -e "\n${YELLOW}🔗 Nützliche Links:${NC}"
echo -e "   • Admin-Panel: https://qqgame.pythonanywhere.com/admin"
echo -e "   • GitHub Repo: https://github.com/einfachstarten/qqgame"
echo -e "   • PythonAnywhere: https://www.pythonanywhere.com/user/QQgame/"

# 9. Optionale Tests
echo -e "\n${YELLOW}Möchtest du einen schnellen Test durchführen? (y/n)${NC}"
read -p "" run_test

if [ "$run_test" = "y" ]; then
    echo -e "\n${BLUE}🧪 Führe Tests durch...${NC}"

    # Test 1: Website erreichbar
    echo -e "${YELLOW}Test 1: Website-Erreichbarkeit...${NC}"
    if curl -s --head https://qqgame.pythonanywhere.com | head -n 1 | grep -q "200 OK"; then
        echo -e "${GREEN}✅ Website ist erreichbar${NC}"
    else
        echo -e "${RED}❌ Website nicht erreichbar oder lädt langsam${NC}"
    fi

    # Test 2: Admin-Panel
    echo -e "${YELLOW}Test 2: Admin-Panel...${NC}"
    if curl -s https://qqgame.pythonanywhere.com/admin | grep -q "Admin Panel"; then
        echo -e "${GREEN}✅ Admin-Panel funktioniert${NC}"
    else
        echo -e "${RED}❌ Problem mit Admin-Panel${NC}"
    fi

    echo -e "${BLUE}🔍 Für detaillierte Logs: tail -f /home/QQgame/qqgame/app.log${NC}"
fi

echo -e "\n${GREEN}✨ Alles erledigt! Viel Spaß mit deinem QQGame! ✨${NC}"