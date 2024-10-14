import sqlite3

DB_PATH = '/home/QQgame/qqgame/highscores.db'

# Function to get all categories (tables) in the database
def get_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Fetch all tables (except SQLite's internal tables)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    categories = [row[0] for row in c.fetchall()]
    
    conn.close()
    return categories

# Function to add the timestamp column to a high score table
def add_timestamp_to_table(category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Check if the table already has the timestamp column
        c.execute(f"PRAGMA table_info({category})")
        columns = [row[1] for row in c.fetchall()]
        if 'timestamp' in columns:
            print(f"Category '{category}' already has a 'timestamp' column.")
            return
        
        # Add a timestamp column to the existing table
        print(f"Adding 'timestamp' column to the '{category}' table.")
        
        # Create a new table with the timestamp column
        c.execute(f'''
            CREATE TABLE {category}_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        ''')
        
        # Copy data from the old table to the new one
        c.execute(f'''
            INSERT INTO {category}_new (id, player_name, score)
            SELECT id, player_name, score FROM {category}
        ''')
        
        # Drop the old table and rename the new table
        c.execute(f"DROP TABLE {category}")
        c.execute(f"ALTER TABLE {category}_new RENAME TO {category}")
        
        conn.commit()
        print(f"Successfully added 'timestamp' column to '{category}'.")

    except Exception as e:
        print(f"Error adding 'timestamp' to table {category}: {e}")
    
    finally:
        conn.close()

# Main function to update all high score tables
def main():
    categories = get_categories()
    
    if not categories:
        print("No categories found.")
        return
    
    print("Updating high score tables to add 'timestamp' column...")
    
    for category in categories:
        add_timestamp_to_table(category)
    
    print("All high score tables updated.")

if __name__ == "__main__":
    main()
