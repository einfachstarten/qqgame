from flask import Flask, render_template, request, redirect, url_for, jsonify
from highscore_manager import qualifies_for_top_10, add_new_high_score, get_top_10_scores
from config import OPENAI_API_KEY
import sqlite3
import logging
import re
import csv
import random
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)
import time
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# =====================================================
# 1. VARIABLES AND CONFIGURATION
# =====================================================
DB_PATH = '/home/QQgame/qqgame/quiz.db'
UPLOAD_FOLDER = '/home/QQgame/qqgame/uploads'
LOG_FILE_PATH = '/home/QQgame/qqgame/app.log'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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

# Function to get categories from the database by ID
def get_category_by_id(category_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        category = c.fetchone()
        conn.close()
        return category
    except Exception as e:
        logging.error(f"[Admin] Error fetching category by ID {category_id}: {e}")
        return None

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

# Check If a question already exists in the category        
def question_exists(category, question_text):
    try:
        sanitized_name = sanitize_table_name(category)
        logging.info(f"[Admin] Checking if question exists for category {category}: {question_text}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"SELECT COUNT(1) FROM {sanitized_name} WHERE question = ?"
        c.execute(query, (question_text,))
        exists = c.fetchone()[0] > 0
        conn.close()
        return exists
    except Exception as e:
        logging.error(f"[Admin] Error checking if question exists: {e}")
        return False

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

# Function to delete a category
def delete_category(category_id):
    try:
        logging.info(f"[Admin] Deleting category with ID: {category_id}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        category_name = c.fetchone()
        if category_name:
            sanitized_name = sanitize_table_name(category_name[0])
            c.execute(f"DROP TABLE IF EXISTS {sanitized_name}")
        c.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()
        logging.info(f"[Admin] Successfully deleted category with ID: {category_id}")
    except Exception as e:
        logging.error(f"[Admin] Error deleting category with ID {category_id}: {e}")

# =====================================================
# 4. ROUTES
# =====================================================
# Home page - Select a category to start the quiz
@app.route('/')
def index():
    logging.info("[Quiz] Rendering home page with category selection.")
    categories = get_categories()
    if not categories:
        logging.warning("[Quiz] No categories found to display on the home page.")
    return render_template('index.html', categories=categories)

# Start the quiz for a selected category
@app.route('/quiz/<category>')
def quiz(category):
    logging.info(f"[Quiz] Rendering quiz page for category: {category}")
    questions = get_questions(category)
    if not questions:
        logging.warning(f"[Quiz] No questions found for category {category}.")
    return render_template('quiz.html', questions=questions, category=category)

# Fetch quiz questions as JSON
@app.route('/quiz_questions/<category>')
def quiz_questions(category):
    sanitized_name = sanitize_table_name(category)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        logging.info(f"[Quiz] Fetching questions for category {category} as JSON.")
        c.execute(f"SELECT question, choice1, choice2, choice3, choice4, correct_index FROM {sanitized_name}")
        questions = c.fetchall()
        conn.close()

        # Convert questions to a list of dictionaries
        questions_list = [
            {
                "question": q[0],
                "choice1": q[1],
                "choice2": q[2],
                "choice3": q[3],
                "choice4": q[4],
                "correct": q[q[5]]
            } for q in questions
        ]

        return jsonify(questions_list)
    except Exception as e:
        logging.error(f"[Quiz] Error fetching questions for category {category}: {e}")
        return jsonify({"error": "Unable to fetch questions"}), 500

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

@app.route('/delete_category', methods=['POST'])
def delete_category_route():
    category_id = request.form.get('category_id')
    if category_id:
        logging.info(f"[Admin] Attempting to delete category with ID: {category_id}")
        delete_category(category_id)
    return redirect(url_for('admin'))

# View questions for a specific category
@app.route('/admin/category/<category>')
def admin_category_questions(category):
    logging.info(f"[Admin] Fetching questions for category: {category} in admin portal.")
    questions = get_questions(category)
    if not questions:
        logging.warning(f"[Admin] No questions found for category {category}.")
    return render_template('admin_category.html', category=category, questions=questions)


# ================================================
# KI PoC
# ================================================

@app.route('/generate_quiz_with_ai', methods=['POST', 'GET'])
def generate_quiz_with_ai():
    # Loggen des Starts der Anfrage
    logging.info("[Flask App] Start der Quizgenerierung mit KI.")

    if request.method == 'GET':
        # Für einen GET-Request: Render ein Formular oder eine Seite
        logging.info("[Flask App] GET-Request: Quizgenerierungsseite wird angezeigt.")
        return render_template('generate_quiz.html')  # Die Vorlage, die du bereits hast.

    if request.method == 'POST':
        try:
            # Schritt 1: Anfrage von Admin, woher kommt die Anfrage?
            logging.info("[Flask App] POST-Request: Anfrage vom Admin empfangen.")

            # Schritt 2: Verarbeiten von Nutzereingaben (z.B. Quiztitel, Thema, Anzahl Fragen, Sprache)
            quiz_title = request.form.get('quiz_title')
            quiz_topic = request.form.get('quiz_topic')
            num_questions = int(request.form.get('num_questions', 5))  # Sicherstellen, dass es eine Zahl ist
            quiz_language = request.form.get('quiz_language')  # Ausgewählte Sprache

            logging.info(f"[Flask App] Quiz Titel: {quiz_title}, Thema: {quiz_topic}, Anzahl der Fragen: {num_questions}, Sprache: {quiz_language}")

            # Schritt 3: Senden der Anfrage an die OpenAI API
            logging.info("[Flask App] Senden der Anfrage an OpenAI API...")

            # OpenAI API-Anfrage mit der richtigen Methode, dem benötigten Format und der festgelegten Sprache
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Backend-Assistent für die Erstellung von Quizfragen. Die Fragen und Antworten müssen IMMER faktisch korrekt sein, und dürfen keinesfalls erfunden sein."},
                    {"role": "user", "content": f"Generiere {num_questions} Quizfragen in der Sprache {quiz_language} für das Thema: {quiz_topic}. Formatiere das Ergebnis in der folgenden JSON-Struktur: [{{'question': 'string', 'choice1': 'string', 'choice2': 'string', 'choice3': 'string', 'choice4': 'string', 'correct_index': int}}]. An welcher Stelle die korrekte Antwort steht, soll immer komplett zufällig zugeordnet werden (zwischen 1 und 4)." }
                ]
            )

            logging.info("[Flask App] OpenAI API Anfrage gesendet.")

            # Schritt 4: Überprüfen der Antwort und zufällige Verteilung der richtigen Antwort
            if response and response.choices:
                logging.info("[Flask App] OpenAI API Antwort erfolgreich empfangen.")
                quiz_questions = response.choices[0].message.content
                logging.info(f"[Flask App] Generierte Fragen im JSON-Format: {quiz_questions}")
            else:
                logging.warning("[Flask App] Keine Antwort oder leere Antwort von OpenAI API erhalten.")
                quiz_questions = "Keine Fragen generiert."

            # Schritt 5: Weiterverarbeitung der erhaltenen Daten und Rückgabe an die HTML-Seite
            return render_template('generate_quiz.html', generated_questions=quiz_questions)

        except openai.error.RateLimitError as e:  # Correct import of RateLimitError
            logging.error(f"[Flask App] OpenAI Rate Limit überschritten: {e}")
            return "Rate Limit überschritten, bitte versuchen Sie es später erneut.", 429

        except openai.error.APIError as e:  # Correct import of APIError
            logging.error(f"[Flask App] OpenAI API-Fehler: {e}")
            return f"Fehler beim Abrufen der Antwort von OpenAI: {e}", 500

        except Exception as e:
            logging.error(f"[Flask App] Ein unbekannter Fehler ist aufgetreten: {e}")
            return "Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.", 500





# =====================================================
# 6. QUESTION MANAGEMENT - ADD, EDIT, DELETE
# =====================================================
@app.route('/admin/category/<category>/add', methods=['POST'])
def add_question_route(category):
    question_id = request.form.get('question_id')
    question_text = request.form.get('question_text')
    answer1 = request.form.get('answer1')
    answer2 = request.form.get('answer2')
    answer3 = request.form.get('answer3')
    answer4 = request.form.get('answer4')
    correct_answer = request.form.get('correct_answer')

    # Ensure all fields are filled
    if not (question_text and answer1 and answer2 and answer3 and answer4 and correct_answer):
        logging.warning(f"[Admin] Form submission missing required fields for category {category}.")
        return redirect(url_for('admin_category_questions', category=category))

    if question_id:
        # Update the existing question
        logging.info(f"[Admin] Updating question with ID {question_id} in category {category}")
        update_question(category, question_id, question_text, answer1, answer2, answer3, answer4, correct_answer)
    else:
        # Add the new question to the database
        logging.info(f"[Admin] Adding new question to category: {category}")
        add_question(category, question_text, answer1, answer2, answer3, answer4, correct_answer)

    return redirect(url_for('admin_category_questions', category=category))

# Function to add a new question to a specific category
def add_question(category, question_text, choice1, choice2, choice3, choice4, correct_index):
    try:
        sanitized_name = sanitize_table_name(category)
        logging.info(f"[Admin] Adding new question to category: {category} (sanitized as {sanitized_name})")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"INSERT INTO {sanitized_name} (question, choice1, choice2, choice3, choice4, correct_index) VALUES (?, ?, ?, ?, ?, ?)"
        logging.debug(f"[Admin] SQL Query to add question: {query}")
        c.execute(query, (question_text, choice1, choice2, choice3, choice4, correct_index))
        conn.commit()
        conn.close()
        logging.info(f"[Admin] Successfully added question to {category}")
    except Exception as e:
        logging.error(f"[Admin] Error adding question to {category}: {e}")

# Route to render the edit form for a question
@app.route('/admin/category/<category>/edit/<int:question_id>', methods=['GET', 'POST'])
def edit_question(category, question_id):
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        answer1 = request.form.get('answer1')
        answer2 = request.form.get('answer2')
        answer3 = request.form.get('answer3')
        answer4 = request.form.get('answer4')
        correct_index = request.form.get('correct_index')

        if not (question_text and answer1 and answer2 and answer3 and answer4 and correct_index):
            logging.warning("[Admin] Form submission missing required fields.")
            return redirect(url_for('edit_question', category=category, question_id=question_id))

        update_question(category, question_id, question_text, answer1, answer2, answer3, answer4, correct_index)
        return redirect(url_for('admin_category_questions', category=category))

    question = get_question_by_id(category, question_id)
    if question is None:
        logging.error(f"[Admin] Question with ID {question_id} not found.")
        return redirect(url_for('admin_category_questions', category=category))

    return render_template('edit_question.html', category=category, question=question)

# Function to fetch a single question by its ID
def get_question_by_id(category, question_id):
    try:
        logging.info(f"[Admin] Fetching question with ID {question_id} from category {category}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"SELECT * FROM {sanitize_table_name(category)} WHERE id = ?"
        c.execute(query, (question_id,))
        question = c.fetchone()
        conn.close()
        return question
    except Exception as e:
        logging.error(f"[Admin] Error fetching question with ID {question_id} from category {category}: {e}")
        return None

# Function to update a question in the database
def update_question(category, question_id, question_text, choice1, choice2, choice3, choice4, correct):
    try:
        sanitized_name = sanitize_table_name(category)
        logging.info(f"[Admin] Updating question with ID {question_id} in category {category}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"UPDATE {sanitized_name} SET question = ?, choice1 = ?, choice2 = ?, choice3 = ?, choice4 = ?, correct_index = ? WHERE id = ?"
        c.execute(query, (question_text, choice1, choice2, choice3, choice4, correct, question_id))
        conn.commit()
        conn.close()
        logging.info(f"[Admin] Successfully updated question with ID {question_id} in category {category}")
    except Exception as e:
        logging.error(f"[Admin] Error updating question with ID {question_id} in category {category}: {e}")

# Route to handle the deletion of a question
@app.route('/admin/category/<category>/delete/<int:question_id>', methods=['POST'])
def delete_question_route(category, question_id):
    delete_question(category, question_id)
    return redirect(url_for('admin_category_questions', category=category))

# Function to delete a question by its ID
def delete_question(category, question_id):
    try:
        logging.info(f"[Admin] Deleting question with ID {question_id} from category {category}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"DELETE FROM {sanitize_table_name(category)} WHERE id = ?"
        c.execute(query, (question_id,))
        conn.commit()
        conn.close()
        logging.info(f"[Admin] Successfully deleted question with ID {question_id} from category {category}")
    except Exception as e:
        logging.error(f"[Admin] Error deleting question with ID {question_id} from category {category}: {e}")

# =====================================================
# 7. FILE UPLOAD (CSV) FOR QUESTIONS
# =====================================================
@app.route('/admin/category/<category>/upload', methods=['POST'])
def upload_questions(category):
    if 'file' not in request.files:
        logging.error("[Admin] No file part in the request.")
        return redirect(url_for('admin_category_questions', category=category))

    file = request.files['file']

    if file.filename == '':
        logging.error("[Admin] No selected file.")
        return redirect(url_for('admin_category_questions', category=category))

    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logging.info(f"[Admin] File {filename} uploaded successfully.")

            with open(filepath, 'r', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                for row in csv_reader:
                    if len(row) == 6:  # Erwartet werden 6 Spalten: question, choice1, choice2, choice3, choice4, correct_index
                        question_text = row[0]
                        answer1 = row[1]
                        answer2 = row[2]
                        answer3 = row[3]
                        answer4 = row[4]
                        correct_index = int(row[5])  # Sicherstellen, dass correct_index eine Zahl ist

                        # Überprüfen, ob die Frage bereits existiert
                        if not question_exists(category, question_text):
                            add_question(category, question_text, answer1, answer2, answer3, answer4, correct_index)
                            logging.info(f"[Admin] Successfully added question: {question_text}")
                        else:
                            logging.info(f"[Admin] Skipped duplicate question: {question_text}")
                    else:
                        logging.warning(f"[Admin] Incorrect row format in CSV: {row}")

            os.remove(filepath)
            logging.info(f"[Admin] File {filename} processed and deleted.")
        except Exception as e:
            logging.error(f"[Admin] Error processing CSV file: {e}")

    return redirect(url_for('admin_category_questions', category=category))


# =====================================================
# 8. HIGHSCORE FUNCTIONALITY
# =====================================================

# -----------------------------------------------------
# Überprüft, ob ein Spieler mit seiner Punktzahl in den Top 10 für eine bestimmte Kategorie ist
# Diese Route wird aufgerufen, wenn das Quiz beendet ist und die Punktzahl überprüft wird.
# Sie gibt zurück, ob der Spieler sich mit seiner Punktzahl in die Highscores eintragen darf.
# -----------------------------------------------------
@app.route('/check_highscore/<category>/<int:score>')
def check_highscore(category, score):
    qualifies = qualifies_for_top_10(category, score)
    return jsonify({'qualifies': qualifies})

# -----------------------------------------------------
# Fügt eine neue Highscore in die Datenbank für die jeweilige Kategorie ein.
# Diese Route wird aufgerufen, wenn der Spieler sich nach dem Quiz für die Top 10 qualifiziert
# und seinen Namen eingibt. Die Highscore-Daten (Kategorie, Name, Punktzahl) werden
# an die Datenbank übermittelt und dort gespeichert.
# -----------------------------------------------------
@app.route('/add_highscore', methods=['POST'])
def add_highscore():
    # Die Daten kommen als JSON vom Frontend (Spielername, Kategorie, Punktzahl)
    data = request.get_json()
    category = data.get('category')
    player_name = data.get('player_name')
    score = data.get('score')

    # Überprüft, ob alle notwendigen Daten vorhanden sind
    if not (category and player_name and score):
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    # Fügt den neuen Highscore hinzu
    add_new_high_score(category, player_name, score)
    return jsonify({'status': 'success'})

# -----------------------------------------------------
# Zeigt die Top 10 Highscores für eine bestimmte Kategorie an.
# Diese Route wird verwendet, um die besten 10 Punktzahlen in einer bestimmten Kategorie zu erhalten
# und im Frontend (z. B. in der Highscore-Liste oder im Admin-Panel) anzuzeigen.
# -----------------------------------------------------
# Route für JSON-Antwort 
@app.route('/high_scores/<category>')
def high_scores(category):
    top_scores = get_top_10_scores(category)
    return jsonify(top_scores)

# Admin Route für Highscores
@app.route('/admin/high_scores/<category>')
def admin_high_scores(category):
    top_scores = get_top_10_scores(category)
    return render_template('highscores.html', scores=top_scores, category=category, enumerate=enumerate)


# -----------------------------------------------------
# Setzt alle Highscores für eine bestimmte Kategorie zurück.
# Diese Route wird verwendet, wenn ein Administrator die Highscores für eine Kategorie
# im Admin-Panel zurücksetzen möchte. Nach dem Zurücksetzen wird der Benutzer
# wieder auf die Highscore-Seite der Kategorie umgeleitet.
# -----------------------------------------------------
@app.route('/admin/category/<category>/reset_highscores', methods=['POST'])
def reset_highscores(category):
    reset_highscores_for_category(category)
    return redirect(url_for('admin_high_scores', category=category))



# =====================================================
# 9. APPLICATION START
# =====================================================
if __name__ == '__main__':
    logging.info("Starting Flask application.")
    app.run(debug=True)