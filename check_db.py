import sqlite3

# Pfad zu deiner Datenbank
DB_PATH = '/home/QQgame/qqgame/quiz.db'

def remove_duplicate_categories(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Suche nach doppelten Kategorien
        cursor.execute("SELECT name, COUNT(*) FROM categories GROUP BY name HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        
        for duplicate in duplicates:
            category_name = duplicate[0]
            # Behalte einen Eintrag und lösche die restlichen
            cursor.execute("DELETE FROM categories WHERE name = ? AND id NOT IN (SELECT MIN(id) FROM categories WHERE name = ?)", (category_name, category_name))
        
        conn.commit()
        conn.close()
        print("Duplikate erfolgreich entfernt.")
    except Exception as e:
        print(f"Fehler beim Entfernen von Duplikaten: {e}")

# Ausführen
if __name__ == "__main__":
    remove_duplicate_categories(DB_PATH)
