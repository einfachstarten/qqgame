import sqlite3

# Path to your database
DB_PATH = '/home/QQgame/qqgame/quiz.db'

# Function to add initial categories to the categories table
def populate_categories():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Insert default categories into the table
        categories = [
            ('Science Quiz'),
            ('History Quiz'),
            ('Geography Quiz'),
            ('Technology Quiz')
        ]

        # Check if table exists and insert the categories
        c.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        for category in categories:
            c.execute("INSERT INTO categories (name) VALUES (?)", (category,))

        conn.commit()
        print("Categories added successfully!")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_categories()
