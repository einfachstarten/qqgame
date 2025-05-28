from flask import Flask, render_template, request, redirect, url_for, jsonify
from highscore_manager import qualifies_for_top_10, add_new_high_score, get_top_10_scores
from config import OPENAI_API_KEY
import sqlite3
import logging
import re
import csv
import random
import json
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

# NEW: Reset highscores function
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

# FIXED: Fetch quiz questions as JSON
@app.route('/quiz_questions/<category>')
def quiz_questions(category):
    """Fetch quiz questions as JSON - FIXED VERSION"""
    try:
        logging.info(f"[Quiz] Fetching questions for category {category} as JSON.")

        # Sanitize category name for database table
        sanitized_name = sanitize_table_name(category)

        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check if table exists first
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sanitized_name,))
        if not c.fetchone():
            logging.error(f"[Quiz] Table {sanitized_name} does not exist for category {category}")
            conn.close()
            return jsonify({"error": f"Category {category} not found"}), 404

        # Fetch questions
        c.execute(f"SELECT question, choice1, choice2, choice3, choice4, correct_index FROM {sanitized_name}")
        questions = c.fetchall()
        conn.close()

        if not questions:
            logging.warning(f"[Quiz] No questions found for category {category}")
            return jsonify({"error": f"No questions found for category {category}"}), 404

        # Convert questions to list of dictionaries
        questions_list = []
        for q in questions:
            # q[5] is correct_index (1-4), we need to get the correct choice text
            correct_index = q[5]  # This should be 1, 2, 3, or 4
            choices = [q[1], q[2], q[3], q[4]]  # choice1, choice2, choice3, choice4

            # Get the correct answer text based on the index
            if 1 <= correct_index <= 4:
                correct_answer = choices[correct_index - 1]  # Convert to 0-based index
            else:
                logging.error(f"[Quiz] Invalid correct_index {correct_index} for question: {q[0]}")
                correct_answer = choices[0]  # Fallback to first choice

            question_dict = {
                "question": q[0],
                "choice1": q[1],
                "choice2": q[2],
                "choice3": q[3],
                "choice4": q[4],
                "correct": correct_answer
            }
            questions_list.append(question_dict)

        logging.info(f"[Quiz] Successfully fetched {len(questions_list)} questions for category {category}")
        return jsonify(questions_list)

    except Exception as e:
        logging.error(f"[Quiz] Error fetching questions for category {category}: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

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

    # NEU: Fragen-Anzahl für jede Kategorie abrufen
    category_question_counts = {}
    for category in categories:
        questions = get_questions(category[1])
        category_question_counts[category[1]] = len(questions)

    return render_template('admin.html',
                         categories=categories,
                         category_question_counts=category_question_counts)

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

# Ersetze die KI-Route in flask_app.py mit dieser vollständigen Version

# Ersetze die generate_quiz_with_ai Route in flask_app.py mit dieser Version

@app.route('/generate_quiz_with_ai', methods=['POST', 'GET'])
def generate_quiz_with_ai():
    logging.info("[Flask App] Start der Quizgenerierung mit KI.")

    if request.method == 'GET':
        logging.info("[Flask App] GET-Request: Quizgenerierungsseite wird angezeigt.")
        return render_template('generate_quiz.html')

    if request.method == 'POST':
        try:
            logging.info("[Flask App] POST-Request: Anfrage vom Admin empfangen.")

            # Formulardaten extrahieren
            quiz_title = request.form.get('quiz_title')
            quiz_topic = request.form.get('quiz_topic')
            num_questions = int(request.form.get('num_questions', 5))
            quiz_language = request.form.get('quiz_language')

            logging.info(f"[Flask App] Quiz Titel: {quiz_title}, Thema: {quiz_topic}, Anzahl der Fragen: {num_questions}, Sprache: {quiz_language}")

            # Verbesserte OpenAI API-Anfrage
            logging.info("[Flask App] Senden der Anfrage an OpenAI API...")

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Du bist ein Experte für die Erstellung von faktisch korrekten Quizfragen.

KRITISCHE REGELN:
1. Alle Antworten müssen 100% faktisch korrekt sein
2. Erfinde NIEMALS Fakten oder schätze
3. Wenn du dir bei einem Fakt nicht sicher bist, formuliere die Frage anders
4. Prüfe jeden Fakt mental bevor du antwortest
5. Die richtige Antwort muss definitiv korrekt sein

ANTWORTFORMAT:
- Antworte NUR mit gültigem JSON
- Keine zusätzlichen Erklärungen oder Kommentare
- Verwende exakt diese Struktur: [{"question": "...", "choice1": "...", "choice2": "...", "choice3": "...", "choice4": "...", "correct_index": N}]

QUALITÄTSKONTROLLE:
- Stelle sicher, dass correct_index korrekt ist (1=choice1, 2=choice2, 3=choice3, 4=choice4)
- Alle falschen Antworten müssen plausibel aber definitiv falsch sein
- Keine Tricks oder mehrdeutigen Fragen"""
                    },
                    {
                        "role": "user",
                        "content": f"""Erstelle {num_questions} faktisch korrekte Quizfragen in der Sprache {quiz_language} zum Thema: {quiz_topic}.

BEISPIEL für korrekte Struktur:
[
  {{
    "question": "Welche Stadt wird als 'Big Apple' bezeichnet?",
    "choice1": "New York",
    "choice2": "Los Angeles",
    "choice3": "Chicago",
    "choice4": "Boston",
    "correct_index": 1
  }}
]

WICHTIGE ANFORDERUNGEN:
- Jede Frage muss faktisch überprüfbar sein
- Die richtige Antwort muss eindeutig korrekt sein
- Verteile correct_index zufällig zwischen 1-4
- Alle falschen Antworten müssen definitiv falsch sein
- Bei Unsicherheit: einfachere, eindeutige Fragen stellen

Thema: {quiz_topic}
Anzahl Fragen: {num_questions}
Sprache: {quiz_language}"""
                    }
                ],
                temperature=0.3,  # Niedrigere Temperatur für mehr Faktentreue
                max_tokens=2000,
                top_p=0.9  # Fokussiert auf wahrscheinlichere Antworten
            )

            logging.info("[Flask App] OpenAI API Anfrage gesendet.")

            # Antwort verarbeiten
            if response and response.choices:
                logging.info("[Flask App] OpenAI API Antwort erfolgreich empfangen.")
                quiz_questions_json = response.choices[0].message.content
                logging.info(f"[Flask App] Generierte Fragen im JSON-Format: {quiz_questions_json}")

                # JSON parsen
                import json
                try:
                    questions_data = json.loads(quiz_questions_json)
                    logging.info(f"[Flask App] JSON erfolgreich geparst, {len(questions_data)} Fragen gefunden.")

                    # Neue Validierung hinzufügen
                    validated_questions = validate_questions(questions_data, quiz_topic)

                    if len(validated_questions) == 0:
                        return render_template('generate_quiz.html',
                                             generated_questions="❌ Alle generierten Fragen haben die Qualitätskontrolle nicht bestanden. Bitte versuche es mit einem anderen Thema oder weniger Fragen.",
                                             success=False)

                    # Verwende validierte Fragen
                    questions_data = validated_questions

                    # Prüfen ob Kategorie bereits existiert
                    existing_categories = get_categories()
                    category_exists = any(cat[1] == quiz_title for cat in existing_categories)

                    if not category_exists:
                        # Kategorie zur Datenbank hinzufügen
                        add_category(quiz_title)
                        logging.info(f"[Flask App] Neue Kategorie '{quiz_title}' zur DB hinzugefügt")
                    else:
                        logging.info(f"[Flask App] Kategorie '{quiz_title}' existiert bereits")

                    # Fragen zur Datenbank hinzufügen
                    questions_added = 0
                    for q in questions_data:
                        try:
                            add_question(
                                quiz_title,
                                q['question'],
                                q['choice1'],
                                q['choice2'],
                                q['choice3'],
                                q['choice4'],
                                q['correct_index']
                            )
                            questions_added += 1
                            logging.info(f"[Flask App] Frage hinzugefügt: {q['question'][:50]}...")
                        except Exception as qe:
                            logging.error(f"[Flask App] Fehler beim Hinzufügen der Frage: {qe}")

                    logging.info(f"[Flask App] {questions_added} Fragen erfolgreich zur Datenbank hinzugefügt.")

                    # Highscore-Tabelle für die neue Kategorie erstellen
                    try:
                        from highscore_manager import create_highscore_table
                        create_highscore_table(quiz_title)
                        logging.info(f"[Flask App] Highscore-Tabelle für '{quiz_title}' erstellt")
                    except Exception as he:
                        logging.error(f"[Flask App] Fehler beim Erstellen der Highscore-Tabelle: {he}")

                    # Erfolgs-Message mit Qualitäts-Info
                    rejected_count = len(questions_data) - len(validated_questions) if 'questions_data' in locals() else 0
                    success_message = f"""🎉 Quiz '{quiz_title}' erfolgreich erstellt!

✅ {questions_added} qualitätsgeprüfte Fragen hinzugefügt
✅ Kategorie erstellt
✅ Highscore-System aktiviert
{f'⚠️ {rejected_count} Fragen nicht bestanden Qualitätskontrolle' if rejected_count > 0 else '✅ Alle Fragen bestanden Qualitätskontrolle'}

Das Quiz ist jetzt auf der Hauptseite verfügbar und spielbar!
"""

                    return render_template('generate_quiz.html',
                                         generated_questions=success_message,
                                         success=True,
                                         quiz_created=True,
                                         quiz_title=quiz_title)

                except json.JSONDecodeError as je:
                    logging.error(f"[Flask App] JSON Parse Error: {je}")
                    error_message = f"""❌ Fehler beim Verarbeiten der KI-Antwort

Die KI-Antwort war kein gültiges JSON-Format. Das kann bei komplexen Themen passieren.

Versuche es mit:
• Einfacherem Thema
• Weniger Fragen (3-5)
• Klarerer Themenbeschreibung

Rohe KI-Antwort:
{quiz_questions_json[:500]}...
"""
                    return render_template('generate_quiz.html',
                                         generated_questions=error_message,
                                         success=False)

            else:
                logging.warning("[Flask App] Keine Antwort oder leere Antwort von OpenAI API erhalten.")
                return render_template('generate_quiz.html',
                                     generated_questions="❌ Keine Antwort von der KI erhalten. Bitte versuche es erneut.")

        except Exception as e:
            logging.error(f"[Flask App] Ein unbekannter Fehler ist aufgetreten: {e}")
            return render_template('generate_quiz.html',
                                 generated_questions=f"❌ Unbekannter Fehler: {str(e)}")

# Validierungsfunktion hinzufügen (nach den anderen Hilfsfunktionen)
def validate_questions(questions_data, quiz_topic):
    """Einfache Validierung der generierten Fragen"""
    validated_questions = []

    for i, q in enumerate(questions_data):
        try:
            # Basis-Validierung
            if not all(key in q for key in ['question', 'choice1', 'choice2', 'choice3', 'choice4', 'correct_index']):
                logging.warning(f"[Validation] Frage {i+1} hat fehlende Felder, überspringe")
                continue

            # correct_index Validierung
            if not (1 <= q['correct_index'] <= 4):
                logging.warning(f"[Validation] Frage {i+1} hat ungültigen correct_index: {q['correct_index']}")
                continue

            # Leere Antworten prüfen
            choices = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
            if any(not choice.strip() for choice in choices):
                logging.warning(f"[Validation] Frage {i+1} hat leere Antworten")
                continue

            # Doppelte Antworten prüfen
            if len(set(choices)) != 4:
                logging.warning(f"[Validation] Frage {i+1} hat doppelte Antworten")
                continue

            # Fragen-/Antwortlänge prüfen
            if len(q['question']) < 10:
                logging.warning(f"[Validation] Frage {i+1} ist zu kurz")
                continue

            validated_questions.append(q)
            logging.info(f"[Validation] Frage {i+1} erfolgreich validiert")

        except Exception as e:
            logging.error(f"[Validation] Fehler bei Frage {i+1}: {e}")
            continue

    logging.info(f"[Validation] {len(validated_questions)} von {len(questions_data)} Fragen validiert")
    return validated_questions


# Neue Route für das Hinzufügen von Fragen zu bestehenden Quiz

# Füge diese Route zu deiner flask_app.py hinzu

@app.route('/expand_quiz_with_ai/<category>', methods=['GET', 'POST'])
def expand_quiz_with_ai(category):
    """Fügt neue Fragen zu einer bestehenden Kategorie hinzu - ohne Duplikate"""

    if request.method == 'GET':
        # Aktuelle Fragen abrufen
        current_questions = get_questions(category)
        return render_template('expand_quiz.html',
                             category=category,
                             current_count=len(current_questions))

    if request.method == 'POST':
        try:
            # Formulardaten extrahieren
            quiz_topic = request.form.get('quiz_topic', '').strip()
            num_questions = int(request.form.get('num_questions', 3))
            quiz_language = request.form.get('quiz_language', 'Deutsch')

            logging.info(f"[Flask App] Erweitere Quiz '{category}' um {num_questions} Fragen")

            # WICHTIG: Bestehende Fragen abrufen
            existing_questions = get_questions(category)
            existing_question_texts = [q[1] for q in existing_questions]  # q[1] ist der Fragentext

            logging.info(f"[Flask App] Gefunden: {len(existing_question_texts)} bestehende Fragen")

            # Bestehende Fragen für KI-Prompt formatieren
            existing_questions_summary = ""
            if existing_question_texts:
                # Nur die ersten 10 Fragen zeigen (damit Prompt nicht zu lang wird)
                sample_questions = existing_question_texts[:10]
                existing_questions_summary = f"""
BEREITS VORHANDENE FRAGEN (erstelle KEINE ähnlichen Fragen):
{chr(10).join([f"- {q}" for q in sample_questions])}
{f"... und {len(existing_question_texts) - 10} weitere Fragen" if len(existing_question_texts) > 10 else ""}
"""

            # Themen-Erkennung falls nicht spezifiziert
            if not quiz_topic:
                quiz_topic = f"Verschiedene Aspekte von {category}"

            # Intelligente KI-Anfrage
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Du bist ein Experte für die Erstellung von faktisch korrekten Quizfragen.

KRITISCHE REGELN:
1. Alle Antworten müssen 100% faktisch korrekt sein
2. Erfinde NIEMALS Fakten oder schätze
3. Erstelle KEINE ähnlichen oder identischen Fragen zu den bereits vorhandenen
4. Die richtige Antwort muss definitiv korrekt sein
5. Erstelle abwechslungsreiche, neue Fragen zum Thema

ANTWORTFORMAT:
- Antworte NUR mit gültigem JSON
- Verwende exakt diese Struktur: [{"question": "...", "choice1": "...", "choice2": "...", "choice3": "...", "choice4": "...", "correct_index": N}]"""
                    },
                    {
                        "role": "user",
                        "content": f"""Erstelle {num_questions} NEUE, faktisch korrekte Quizfragen in der Sprache {quiz_language} zum Thema: {quiz_topic}.

KATEGORIE: {category}
{existing_questions_summary}

WICHTIGE ANFORDERUNGEN:
- Erstelle NUR neue Fragen, die sich deutlich von den vorhandenen unterscheiden
- Alle Fragen müssen faktisch korrekt und überprüfbar sein
- Die richtige Antwort muss eindeutig korrekt sein
- Verteile correct_index zufällig zwischen 1-4
- Alle falschen Antworten müssen definitiv falsch sein
- Bringe Abwechslung in die Frageart (Wer/Was/Wann/Wo/Wie)

Erstelle {num_questions} einzigartige neue Fragen."""
                    }
                ],
                temperature=0.4,  # Etwas höher für mehr Kreativität bei der Variation
                max_tokens=2000,
                top_p=0.9
            )

            if response and response.choices:
                quiz_questions_json = response.choices[0].message.content
                questions_data = json.loads(quiz_questions_json)

                logging.info(f"[Flask App] KI hat {len(questions_data)} neue Fragen vorgeschlagen")

                # Erweiterte Validierung - auch auf Duplikate prüfen
                validated_questions = validate_questions_with_duplicates(questions_data, existing_question_texts, category)

                if len(validated_questions) == 0:
                    return render_template('expand_quiz.html',
                                         category=category,
                                         current_count=len(existing_questions),
                                         result="❌ Alle generierten Fragen haben die Qualitätskontrolle nicht bestanden oder waren zu ähnlich zu bestehenden Fragen. Versuche ein spezifischeres Unterthema.",
                                         success=False)

                # Fragen zur bestehenden Kategorie hinzufügen
                questions_added = 0
                for q in validated_questions:
                    try:
                        add_question(
                            category,
                            q['question'],
                            q['choice1'],
                            q['choice2'],
                            q['choice3'],
                            q['choice4'],
                            q['correct_index']
                        )
                        questions_added += 1
                        logging.info(f"[Flask App] Neue Frage hinzugefügt: {q['question'][:50]}...")
                    except Exception as qe:
                        logging.error(f"[Flask App] Fehler beim Hinzufügen der Frage: {qe}")

                # Finale Statistiken
                new_total = len(get_questions(category))
                rejected_count = len(questions_data) - len(validated_questions)

                success_message = f"""🎉 Quiz erfolgreich erweitert!

✅ {questions_added} neue einzigartige Fragen hinzugefügt
📊 Gesamt: {new_total} Fragen in "{category}" (vorher: {len(existing_questions)})
🔍 {len(validated_questions)} Fragen bestanden Qualitätskontrolle
{f'⚠️ {rejected_count} Fragen als Duplikate/ungültig abgelehnt' if rejected_count > 0 else '✅ Alle Fragen waren einzigartig'}
🧠 KI hat bestehende {len(existing_question_texts)} Fragen berücksichtigt

Das erweiterte Quiz ist sofort spielbar!"""

                return render_template('expand_quiz.html',
                                     category=category,
                                     current_count=new_total,
                                     result=success_message,
                                     success=True)

        except Exception as e:
            logging.error(f"[Flask App] Fehler beim Erweitern des Quiz: {e}")
            return render_template('expand_quiz.html',
                                 category=category,
                                 current_count=len(get_questions(category)),
                                 result=f"❌ Fehler: {str(e)}",
                                 success=False)


# Erweiterte Validierungsfunktion mit Duplikat-Erkennung
def validate_questions_with_duplicates(questions_data, existing_question_texts, category):
    """Validiert Fragen und prüft auf Duplikate"""
    validated_questions = []

    for i, q in enumerate(questions_data):
        try:
            # Basis-Validierung (wie vorher)
            if not all(key in q for key in ['question', 'choice1', 'choice2', 'choice3', 'choice4', 'correct_index']):
                logging.warning(f"[Validation] Frage {i+1} hat fehlende Felder, überspringe")
                continue

            if not (1 <= q['correct_index'] <= 4):
                logging.warning(f"[Validation] Frage {i+1} hat ungültigen correct_index: {q['correct_index']}")
                continue

            choices = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
            if any(not choice.strip() for choice in choices):
                logging.warning(f"[Validation] Frage {i+1} hat leere Antworten")
                continue

            if len(set(choices)) != 4:
                logging.warning(f"[Validation] Frage {i+1} hat doppelte Antworten")
                continue

            # NEU: Duplikat-Erkennung
            new_question_text = q['question'].strip()

            # Ähnlichkeit mit bestehenden Fragen prüfen
            is_duplicate = False
            for existing_q in existing_question_texts:
                # Einfache Ähnlichkeits-Prüfung
                if similar_questions(new_question_text, existing_q):
                    logging.warning(f"[Validation] Frage {i+1} ist zu ähnlich zu bestehender Frage: '{existing_q[:50]}...'")
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            validated_questions.append(q)
            logging.info(f"[Validation] Frage {i+1} erfolgreich validiert und einzigartig")

        except Exception as e:
            logging.error(f"[Validation] Fehler bei Frage {i+1}: {e}")
            continue

    logging.info(f"[Validation] {len(validated_questions)} von {len(questions_data)} Fragen validiert (einzigartig)")
    return validated_questions


def similar_questions(q1, q2, threshold=0.7):
    """Einfache Ähnlichkeits-Prüfung zwischen zwei Fragen"""
    import re

    # Text normalisieren
    def normalize(text):
        # Kleinbuchstaben, nur Buchstaben/Zahlen behalten
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

    q1_norm = normalize(q1)
    q2_norm = normalize(q2)

    # Wörter aufteilen
    words1 = set(q1_norm.split())
    words2 = set(q2_norm.split())

    # Jaccard-Ähnlichkeit berechnen
    if len(words1) == 0 and len(words2) == 0:
        return True

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    similarity = intersection / union if union > 0 else 0

    return similarity > threshold


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

# FIXED: Check if score qualifies for top 10
@app.route('/check_highscore/<category>/<int:score>')
def check_highscore(category, score):
    """Check if score qualifies for top 10 - FIXED VERSION"""
    try:
        logging.info(f"[Highscore] Checking if score {score} qualifies for category {category}")

        qualifies = qualifies_for_top_10(category, score)
        logging.info(f"[Highscore] Score {score} for {category} qualifies: {qualifies}")

        return jsonify({'qualifies': qualifies})

    except Exception as e:
        logging.error(f"[Highscore] Error checking highscore for {category}/{score}: {e}")
        return jsonify({'qualifies': False, 'error': str(e)}), 500

# Add new highscore
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

# FIXED: Get top 10 scores for category
@app.route('/high_scores/<category>')
def high_scores(category):
    """Get top 10 scores for category - FIXED VERSION"""
    try:
        logging.info(f"[Highscore] Fetching top scores for category {category}")

        top_scores = get_top_10_scores(category)
        logging.info(f"[Highscore] Found {len(top_scores)} scores for category {category}")

        return jsonify(top_scores)

    except Exception as e:
        logging.error(f"[Highscore] Error fetching scores for {category}: {e}")
        return jsonify({'error': str(e)}), 500

# Admin Route für Highscores
@app.route('/admin/high_scores/<category>')
def admin_high_scores(category):
    top_scores = get_top_10_scores(category)
    return render_template('highscores.html', scores=top_scores, category=category, enumerate=enumerate)

# Reset highscores for category
@app.route('/admin/category/<category>/reset_highscores', methods=['POST'])
def reset_highscores(category):
    reset_highscores_for_category(category)
    return redirect(url_for('admin_high_scores', category=category))

# =====================================================
# 9. DEBUG ROUTES (OPTIONAL)
# =====================================================
@app.route('/debug/categories')
def debug_categories():
    """Debug route to check categories and tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Get all categories
        c.execute("SELECT * FROM categories")
        categories = c.fetchall()

        result = {
            "categories": categories,
            "tables": []
        }

        # Check tables for each category
        for cat in categories:
            cat_name = cat[1]
            sanitized = sanitize_table_name(cat_name)

            # Check if table exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (sanitized,))
            table_exists = c.fetchone() is not None

            # Count questions if table exists
            question_count = 0
            if table_exists:
                c.execute(f"SELECT COUNT(*) FROM {sanitized}")
                question_count = c.fetchone()[0]

            result["tables"].append({
                "category": cat_name,
                "sanitized": sanitized,
                "table_exists": table_exists,
                "question_count": question_count
            })

        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# 10. APPLICATION START
# =====================================================
if __name__ == '__main__':
    logging.info("Starting Flask application.")
    app.run(debug=True)