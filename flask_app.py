from flask import Flask, render_template, request, redirect, url_for, jsonify
from highscore_manager import qualifies_for_top_10, add_new_high_score, get_top_10_scores
import sqlite3
import logging
import re
import csv
import os
import random
import json
from openai import OpenAI
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

# =====================================================
# 1. VARIABLES AND CONFIGURATION
# =====================================================
DB_PATH = '/home/QQgame/qqgame/quiz.db'
UPLOAD_FOLDER = '/home/QQgame/qqgame/uploads'
LOG_FILE_PATH = '/home/QQgame/qqgame/app.log'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
client = OpenAI(api_key=OPENAI_API_KEY)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: [%(module)s] %(message)s',
)

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 Error: {error}")
    return "Internal Server Error", 500

# Delete the log file at application start (optional behavior)
if os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w'):
        pass  # Clears the file

# =====================================================
# 2. HELPER FUNCTIONS
# =====================================================
# Helper function to sanitize category name for table creation
def sanitize_table_name(category_name):
    return re.sub(r'\W+', '_', category_name)

# Function to get categories from the database
def get_categories():
    try:
        logging.info("[Admin] Fetching categories from the database.")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM categories")
        categories = c.fetchall()
        logging.debug(f"[Admin] Categories fetched: {categories}")
        conn.close()
        return categories
    except Exception as e:
        logging.error(f"[Admin] Error fetching categories: {e}")
        return []

# Function to check if table exists for a category
def table_exists(category):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name= ?", (category,))
        table = c.fetchone()
        conn.close()
        logging.debug(f"[Admin/Quiz] Table exists check for category '{category}': {table is not None}")
        return table is not None
    except Exception as e:
        logging.error(f"Error checking if table exists for category {category}: {e}")
        return False

# Function to get questions from a selected category
def get_questions(category):
    sanitized_name = sanitize_table_name(category)
    if not table_exists(sanitized_name):
        logging.error(f"[Admin/Quiz] Table for category {category} (sanitized as {sanitized_name}) does not exist.")
        return []

    try:
        logging.info(f"[Admin/Quiz] Fetching questions for category: {category}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"SELECT id, question, choice1, choice2, choice3, choice4, correct_index FROM {sanitized_name}"
        logging.debug(f"[Admin/Quiz] SQL Query: {query}")
        c.execute(query)
        questions = c.fetchall()
        logging.debug(f"[Admin/Quiz] Questions fetched for category {category}: {questions}")
        conn.close()
        return questions
    except Exception as e:
        logging.error(f"[Admin/Quiz] Error fetching questions for category {category}: {e}")
        return []

def reset_highscores_for_category(category):
    """Setzt alle Highscores für eine bestimmte Kategorie zurück"""
    try:
        logging.info(f"[Admin] Resetting highscores for category: {category}")
        sanitized_category = sanitize_table_name(category)
        conn = sqlite3.connect('/home/QQgame/qqgame/highscores.db')
        c = conn.cursor()
        c.execute(f"DELETE FROM {sanitized_category}")
        conn.commit()
        conn.close()
        logging.info(f"[Admin] Successfully reset highscores for category: {category}")
    except Exception as e:
        logging.error(f"[Admin] Error resetting highscores for category {category}: {e}")

# =====================================================
# 3. CATEGORY MANAGEMENT
# =====================================================
# Function to add a new category and create a corresponding table
def add_category(category_name):
    try:
        logging.info(f"[Admin] Adding new category: {category_name}")
        sanitized_name = sanitize_table_name(category_name)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        logging.debug(f"[Admin] Inserted new category '{category_name}' into categories table.")

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {sanitized_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            choice1 TEXT NOT NULL,
            choice2 TEXT NOT NULL,
            choice3 TEXT NOT NULL,
            choice4 TEXT NOT NULL,
            correct_index INTEGER NOT NULL
        )
        """
        logging.debug(f"[Admin] Creating table with query: {create_table_query}")
        c.execute(create_table_query)

        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"[Admin] Error adding category {category_name}: {e}")

# =====================================================
# 4. ROUTES
# =====================================================
@app.route('/')
def index():
    logging.info("[Quiz] Rendering home page with category selection.")
    categories = get_categories()
    return render_template('index.html', categories=categories)

@app.route('/quiz/<category>')
def quiz(category):
    logging.info(f"[Quiz] Rendering quiz page for category: {category}")
    questions = get_questions(category)
    return render_template('quiz.html', questions=questions, category=category)

# =====================================================
# 5. ADMIN ROUTES - CATEGORY AND QUESTION MANAGEMENT
# =====================================================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        new_category = request.form.get('category_name')
        if new_category:
            logging.info(f"[Admin] Attempting to add new category: {new_category}")
            add_category(new_category)
        return redirect(url_for('admin'))

    categories = get_categories()
    return render_template('admin.html', categories=categories)

# ================================================
# KI PoC
# ================================================
@app.route('/generate_quiz_with_ai', methods=['POST', 'GET'])
def generate_quiz_with_ai():
    logging.info("[Flask App] Start der Quizgenerierung mit KI.")
    if request.method == 'GET':
        logging.info("[Flask App] GET-Request: Quizgenerierungsseite wird angezeigt.")
        return render_template('generate_quiz.html')

    if request.method == 'POST':
        try:
            quiz_title = request.form.get('quiz_title')
            quiz_topic = request.form.get('quiz_topic')
            num_questions = int(request.form.get('num_questions', 5))
            quiz_language = request.form.get('quiz_language')

            logging.info(f"[Flask App] Quiz Titel: {quiz_title}, Thema: {quiz_topic}, Anzahl der Fragen: {num_questions}, Sprache: {quiz_language}")
            logging.info("[Flask App] Senden der Anfrage an OpenAI API...")

            # OpenAI API request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Assistent zur Erstellung von Quizfragen. Die Fragen und Antworten müssen faktisch korrekt sein."},
                    {"role": "user", "content": f"Generiere {num_questions} Quizfragen in der Sprache {quiz_language} für das Thema: {quiz_title} - {quiz_topic}. Formatiere das Ergebnis in der folgenden JSON-Struktur: [{'question': 'string', 'choice1': 'string', 'choice2': 'string', 'choice3': 'string', 'choice4': 'string', 'correct_index': int}]."}
                ]
            )

            logging.info("[Flask App] OpenAI API Antwort empfangen.")
            quiz_questions = response.choices[0].message.content
            logging.debug(f"[Flask App] Generierte Fragen: {quiz_questions}")

            return render_template('generate_quiz.html', quiz_title=quiz_title, generated_questions=quiz_questions)

        except Exception as e:
            logging.error(f"[Flask App] Fehler: {e}")
            return render_template('generate_quiz.html', error_message="Ein Fehler ist aufgetreten.")
