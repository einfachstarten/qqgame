import sqlite3
import os

# Pfad zur Datenbankdatei
DB_PATH = '/home/QQgame/qqgame/quiz.db'

# Erstellen einer Verbindung zur Datenbank
def create_connection(db_file):
    """Verbindung zur SQLite-Datenbank erstellen"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Verbindung zur Datenbank {db_file} erfolgreich.")
        return conn
    except sqlite3.Error as e:
        print(f"Fehler bei der Verbindung zur Datenbank: {e}")
    return conn

# Tabellen löschen und neu erstellen
def reset_database(conn):
    try:
        c = conn.cursor()
        
        # Kategorien-Tabelle löschen, falls sie existiert
        c.execute("DROP TABLE IF EXISTS categories")
        print("Tabelle 'categories' gelöscht.")
        
        # Kategorien-Tabelle neu erstellen
        c.execute('''CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                     )''')
        print("Tabelle 'categories' wurde erstellt.")
        
        # Beispielkategorien hinzufügen
        categories = ['Spezialquiz für Projektmanager', 'Fußballquiz 1', 'Fun Facts aus aller Welt']
        c.executemany("INSERT INTO categories (name) VALUES (?)", [(category,) for category in categories])
        print(f"{len(categories)} Beispielkategorien hinzugefügt.")

        # Alle vorhandenen Tabellen löschen, die den Spielnamen als Tabelle haben könnten
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('categories')")
        tables = c.fetchall()
        for table_name in tables:
            c.execute(f"DROP TABLE IF EXISTS {table_name[0]}")
            print(f"Tabelle '{table_name[0]}' gelöscht.")

        # Änderungen speichern
        conn.commit()
        print("Änderungen erfolgreich gespeichert.")
        
    except sqlite3.Error as e:
        print(f"Fehler bei der Rücksetzung der Datenbank: {e}")
        conn.rollback()

def main():
    # Datenbankverbindung herstellen
    conn = create_connection(DB_PATH)

    # Falls Verbindung erfolgreich, Datenbank zurücksetzen
    if conn is not None:
        reset_database(conn)
        conn.close()
        print("Datenbank wurde zurückgesetzt.")
    else:
        print("Fehler: Verbindung zur Datenbank konnte nicht hergestellt werden.")

if __name__ == '__main__':
    main()
