from datetime import datetime 
import sqlite3
import re

DB_PATH = '/home/QQgame/qqgame/highscores.db'

def sanitize_table_name(category_name):
    # Remove all non-alphanumeric characters and replace spaces with underscores
    return re.sub(r'\W+', '_', category_name)

def create_highscore_table(category):
    """Creates a high score table for the category if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    sanitized_category = sanitize_table_name(category)
    
    # Create table if it doesn't exist with the timestamp column
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS {sanitized_category} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def qualifies_for_top_10(category, score):
    """Checks if the score qualifies for the top 10 in the category."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    sanitized_category = sanitize_table_name(category)
    
    # Ensure the high score table exists
    create_highscore_table(sanitized_category)
    
    # Fetch the current top 10 scores
    c.execute(f'''
        SELECT score FROM {sanitized_category}
        ORDER BY score DESC
        LIMIT 10
    ''')
    top_scores = c.fetchall()
    
    # If less than 10 scores, the player automatically qualifies
    if len(top_scores) < 10:
        conn.close()
        return True
    
    # Otherwise, check if the score is higher than the lowest top score
    lowest_top_score = top_scores[-1][0]  # The lowest score in the top 10
    conn.close()
    return score > lowest_top_score

def add_new_high_score(category, player_name, score):
    """Adds a new high score to the category."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    sanitized_category = sanitize_table_name(category)
    
    # Ensure the high score table exists
    create_highscore_table(sanitized_category)
    
    # Insert the new high score with a timestamp
    c.execute(f'''
        INSERT INTO {sanitized_category} (player_name, score, timestamp)
        VALUES (?, ?, datetime('now'))
    ''', (player_name, score))
    
    conn.commit()
    conn.close()

def get_top_10_scores(category):
    """Retrieves the top 10 scores for the category with formatted timestamp."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    sanitized_category = sanitize_table_name(category)
    
    # Ensure the high score table exists
    create_highscore_table(sanitized_category)
    
    # Fetch the top 10 scores along with the timestamp
    c.execute(f'''
        SELECT player_name, score, timestamp FROM {sanitized_category}
        ORDER BY score DESC, timestamp ASC
        LIMIT 10
    ''')
    top_scores = c.fetchall()
    
    conn.close()
    
    # Format the timestamp
    formatted_scores = []
    for row in top_scores:
        player_name, score, timestamp = row
        formatted_timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d. %B %Y, %H:%M')
        formatted_scores.append({'player_name': player_name, 'score': score, 'timestamp': formatted_timestamp})
    
    return formatted_scores
    
    return [{'player_name': row[0], 'score': row[1], 'timestamp': row[2]} for row in top_scores]
