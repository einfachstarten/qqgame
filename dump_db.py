import sqlite3

def print_table_contents(cursor, table_name):
    print(f"\nInhalt der Tabelle: {table_name}")
    
    # Abrufen der Spaltennamen
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [description[1] for description in cursor.fetchall()]
    print(f"Spalten: {columns}")

    # Abrufen und Ausgeben der Daten
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

def dump_database(db_path):
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Abrufen aller Tabellennamen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        print_table_contents(cursor, table_name)

    # Verbindung schließen
    conn.close()

if __name__ == "__main__":
    # Pfad zur Datenbank angeben
    db_path = 'quiz.db'
    
    # Datenbank ausgeben
    dump_database(db_path)
