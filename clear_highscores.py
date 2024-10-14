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

# Function to clear the high scores for a selected category
def clear_highscores(category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Delete all records in the table
    c.execute(f"DELETE FROM {category}")
    conn.commit()
    
    conn.close()
    print(f"High scores for category '{category}' have been cleared.")

# Main function to display categories and prompt the user for input
def main():
    categories = get_categories()
    
    if not categories:
        print("No categories found.")
        return
    
    print("Available categories:")
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    
    # Prompt user to select a category
    while True:
        try:
            selection = int(input(f"Select the category to clear (1-{len(categories)}): "))
            if 1 <= selection <= len(categories):
                break
            else:
                print(f"Please enter a number between 1 and {len(categories)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # Clear the selected category
    selected_category = categories[selection - 1]
    confirm = input(f"Are you sure you want to clear the high scores for '{selected_category}'? (y/n): ")
    
    if confirm.lower() == 'y':
        clear_highscores(selected_category)
    else:
        print("Operation canceled.")

if __name__ == "__main__":
    main()
