# complete_db_reset_auto.py - Version ohne Bestätigungsprompt
import sqlite3
import os
from datetime import datetime

# Datenbankpfade
QUIZ_DB_PATH = '/home/QQgame/qqgame/quiz.db'
HIGHSCORE_DB_PATH = '/home/QQgame/qqgame/highscores.db'

def reset_quiz_database():
    """Löscht und erstellt die Quiz-Datenbank neu"""
    print("=== Quiz-Datenbank wird zurückgesetzt ===")

    # Alte DB löschen falls vorhanden
    if os.path.exists(QUIZ_DB_PATH):
        os.remove(QUIZ_DB_PATH)
        print(f"Alte Quiz-DB gelöscht: {QUIZ_DB_PATH}")

    # Neue DB erstellen
    conn = sqlite3.connect(QUIZ_DB_PATH)
    c = conn.cursor()

    # Categories Tabelle erstellen
    c.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    print("Categories-Tabelle erstellt")

    # Test-Kategorien hinzufügen
    test_categories = [
        'Allgemeinwissen',
        'Geschichte',
        'Geographie',
        'Sport'
    ]

    for category in test_categories:
        c.execute("INSERT INTO categories (name) VALUES (?)", (category,))

        # Tabelle für jede Kategorie erstellen
        sanitized_name = category.replace(' ', '_').replace('-', '_')
        c.execute(f'''
            CREATE TABLE {sanitized_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                choice1 TEXT NOT NULL,
                choice2 TEXT NOT NULL,
                choice3 TEXT NOT NULL,
                choice4 TEXT NOT NULL,
                correct_index INTEGER NOT NULL
            )
        ''')
        print(f"Tabelle für Kategorie '{category}' erstellt")

        # Test-Fragen hinzufügen
        add_test_questions(c, sanitized_name, category)

    conn.commit()
    conn.close()
    print("Quiz-Datenbank erfolgreich erstellt!")

def add_test_questions(cursor, table_name, category):
    """Fügt Test-Fragen für jede Kategorie hinzu"""

    if category == 'Allgemeinwissen':
        questions = [
            ("Wie viele Kontinente gibt es?", "5", "6", "7", "8", 3),
            ("Welche Farbe entsteht wenn man Rot und Blau mischt?", "Grün", "Lila", "Orange", "Gelb", 2),
            ("Wie viele Beine hat eine Spinne?", "6", "8", "10", "12", 2),
            ("In welchem Jahr fiel die Berliner Mauer?", "1987", "1989", "1991", "1993", 2),
            ("Welcher Planet ist der Sonne am nächsten?", "Venus", "Merkur", "Erde", "Mars", 2)
        ]
    elif category == 'Geschichte':
        questions = [
            ("Wann begann der Zweite Weltkrieg?", "1938", "1939", "1940", "1941", 2),
            ("Wer war der erste Bundeskanzler Deutschlands?", "Willy Brandt", "Helmut Schmidt", "Konrad Adenauer", "Ludwig Erhard", 3),
            ("In welchem Jahr wurde die DDR gegründet?", "1948", "1949", "1950", "1951", 2),
            ("Welches Ereignis löste den Ersten Weltkrieg aus?", "Russische Revolution", "Attentat in Sarajevo", "Invasion Belgiens", "Mobilmachung Frankreichs", 2),
            ("Wann endete das Römische Reich?", "476 n.Chr.", "500 n.Chr.", "410 n.Chr.", "455 n.Chr.", 1)
        ]
    elif category == 'Geographie':
        questions = [
            ("Welches ist das größte Land der Welt?", "China", "USA", "Russland", "Kanada", 3),
            ("Wie heißt die Hauptstadt von Australien?", "Sydney", "Melbourne", "Canberra", "Perth", 3),
            ("Welcher ist der längste Fluss der Welt?", "Amazonas", "Nil", "Mississippi", "Jangtse", 2),
            ("Auf welchem Kontinent liegt Ägypten?", "Asien", "Afrika", "Europa", "Australien", 2),
            ("Welcher Berg ist der höchste der Welt?", "K2", "Mount Everest", "Kilimandscharo", "Mont Blanc", 2)
        ]
    elif category == 'Sport':
        questions = [
            ("Wie oft finden Olympische Sommerspiele statt?", "Alle 2 Jahre", "Alle 4 Jahre", "Alle 3 Jahre", "Alle 5 Jahre", 2),
            ("In welcher Sportart wird der Davis Cup ausgespielt?", "Golf", "Tennis", "Fußball", "Basketball", 2),
            ("Wie viele Spieler hat eine Fußballmannschaft auf dem Feld?", "10", "11", "12", "9", 2),
            ("Welche Farbe hat das Trikot des Führenden bei der Tour de France?", "Grün", "Rot", "Gelb", "Blau", 3),
            ("Wie lang ist ein Marathon?", "40,195 km", "42,195 km", "41,195 km", "43,195 km", 2)
        ]
    else:
        questions = []

    for q in questions:
        cursor.execute(f'''
            INSERT INTO {table_name} (question, choice1, choice2, choice3, choice4, correct_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', q)

    print(f"  -> {len(questions)} Test-Fragen für '{category}' hinzugefügt")

def reset_highscore_database():
    """Löscht und erstellt die Highscore-Datenbank neu"""
    print("\n=== Highscore-Datenbank wird zurückgesetzt ===")

    # Alte DB löschen falls vorhanden
    if os.path.exists(HIGHSCORE_DB_PATH):
        os.remove(HIGHSCORE_DB_PATH)
        print(f"Alte Highscore-DB gelöscht: {HIGHSCORE_DB_PATH}")

    # Neue DB erstellen
    conn = sqlite3.connect(HIGHSCORE_DB_PATH)
    c = conn.cursor()

    # Für jede Kategorie eine Highscore-Tabelle erstellen
    categories = ['Allgemeinwissen', 'Geschichte', 'Geographie', 'Sport']

    for category in categories:
        sanitized_name = category.replace(' ', '_').replace('-', '_')
        c.execute(f'''
            CREATE TABLE {sanitized_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print(f"Highscore-Tabelle für '{category}' erstellt")

        # Ein paar Test-Highscores hinzufügen
        test_scores = [
            ('Max Mustermann', 8),
            ('Anna Schmidt', 7),
            ('Peter Mueller', 9),
            ('Lisa Weber', 6),
            ('Tom Fischer', 10)
        ]

        for name, score in test_scores:
            c.execute(f'''
                INSERT INTO {sanitized_name} (player_name, score)
                VALUES (?, ?)
            ''', (name, score))

    conn.commit()
    conn.close()
    print("Highscore-Datenbank erfolgreich erstellt!")

def verify_databases():
    """Überprüft ob beide Datenbanken korrekt erstellt wurden"""
    print("\n=== Datenbank-Verifikation ===")

    # Quiz-DB prüfen
    if os.path.exists(QUIZ_DB_PATH):
        conn = sqlite3.connect(QUIZ_DB_PATH)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM categories")
        cat_count = c.fetchone()[0]
        print(f"✓ Quiz-DB: {cat_count} Kategorien gefunden")

        c.execute("SELECT name FROM categories")
        categories = c.fetchall()
        for cat in categories:
            cat_name = cat[0].replace(' ', '_').replace('-', '_')
            c.execute(f"SELECT COUNT(*) FROM {cat_name}")
            q_count = c.fetchone()[0]
            print(f"  - {cat[0]}: {q_count} Fragen")

        conn.close()
    else:
        print("✗ Quiz-DB nicht gefunden!")

    # Highscore-DB prüfen
    if os.path.exists(HIGHSCORE_DB_PATH):
        conn = sqlite3.connect(HIGHSCORE_DB_PATH)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print(f"✓ Highscore-DB: {len(tables)} Tabellen gefunden")

        for table in tables:
            c.execute(f"SELECT COUNT(*) FROM {table[0]}")
            score_count = c.fetchone()[0]
            print(f"  - {table[0]}: {score_count} Highscores")

        conn.close()
    else:
        print("✗ Highscore-DB nicht gefunden!")

if __name__ == "__main__":
    print("=== AUTOMATISCHER DATENBANK-RESET ===")
    print("Starte sofort (ohne Bestätigung)...")

    reset_quiz_database()
    reset_highscore_database()
    verify_databases()
    print("\n🎉 Datenbank-Reset abgeschlossen!")
    print("\nDu kannst jetzt die Flask-App starten und testen.")