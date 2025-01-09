from flask import Flask, render_template, jsonify, request, redirect, url_for, session,flash,Response
# import requests
import pyttsx3
import threading
import time
import os
import base64

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# In-memory user database
users_db = {}  # {'username': {'password': password, 'name': name, 'photo': photo}}

# Ensure the user_photos folder exists
if not os.path.exists('static/user_photos'):
    os.makedirs('static/user_photos')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Wit.ai API details
WIT_AI_TOKEN = "IX3GFNFW7EF2Q6Z4SJCPKGTIMTQ3KFMQ"  # Replace with your Wit.ai token
WIT_AI_URL = "https://api.wit.ai/message"

# Function to handle text-to-speech
def speak_text(text):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)
    engine.say(text)
    engine.runAndWait()


# Routes
@app.route('/')
def first():
    """Render the first page."""
    return render_template('first.html')




@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Handle user sign-in."""
    if request.method == 'POST':
        usn = request.form['usn']
        password = request.form['password']  # Implement actual password logic
        
        if usn in users_db:
            session['user_logged_in'] = True
            return redirect(url_for('home'))
        else:
            return "Invalid credentials.", 401

    return render_template('signin.html')


@app.route('/home')
def home():
    """Render the home page."""
    # if 'user_logged_in' not in session:
    #     return redirect(url_for('signin'))
    return render_template('home.html')


@app.route('/intro')
def intro():
    """Render the intro page."""
    return render_template('intro.html')


@app.route('/speak-welcome')
def speak_welcome():
    """Speak the welcome message."""
    text = "Hello, welcome to Equal Edge. We aim for universal accessibility."
    threading.Thread(target=speak_text, args=(text,)).start()
    return jsonify({"text": text})


@app.route('/ask-disability')
def ask_disability():
    """Ask the disability question."""
    time.sleep(5)  # Sim ulated delay
    text = "Do you have any disabilities that we should be aware of?"
    threading.Thread(target=speak_text, args=(text,)).start()
    return jsonify({"text": text})

import cv2

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
webcam = None
uploads_dir = 'uploads'
os.makedirs(uploads_dir, exist_ok=True)
user_faces = {}  # Dictionary to hold registered faces

# Constants for face dimensions
FACE_WIDTH, FACE_HEIGHT = 80, 80

# Define upload folder path
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')


# Load registered faces into memory
def load_registered_faces():
    for filename in os.listdir(uploads_dir):
        if filename.endswith('.jpg'):
            username = filename.rsplit('.', 1)[0]
            filepath = os.path.join(uploads_dir, filename)
            face = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            user_faces[username] = face

# Call to load faces at app startup
load_registered_faces()

# Function to capture a face from the webcam
def capture_face():
    global webcam
    webcam = cv2.VideoCapture(0, cv2.CAP_ANY)  # Use any backend for webcam

    if not webcam.isOpened():
        print("Error: Could not access the webcam.")
        return None

    ret, frame = webcam.read()
    webcam.release()  # Release the webcam

    if not ret:
        print("Failed to grab frame")
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No face detected")
        return None

    x, y, w, h = faces[0]
    face = gray[y:y + h, x:x + w]  # Extract grayscale face region
    return face

# Function to generate video frames for live feed
def gen_frames():
    global webcam
    webcam = cv2.VideoCapture(0, cv2.CAP_ANY)  # Use any backend for webcam

    if not webcam.isOpened():
        print("Error: Could not access the webcam.")
        return

    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            ret, frame = webcam.read()
            if not ret:
                print("Failed to grab frame")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame")
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    finally:
        webcam.release()  # Ensure the webcam is released


# Route for signing up a user
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Capture form inputs
        name = request.form['name']
        age = request.form['age']
        usn = request.form['usn']
        institution = request.form['institution']
        
        # Capture face
        face = capture_face()

        if face is None:
            flash("Face not detected. Please try again.", 'error')
            return redirect(url_for('signup'))

        # Define standard face dimensions
        face_resized = cv2.resize(face, (FACE_WIDTH, FACE_HEIGHT))

        # Save the resized face image
        filename = secure_filename(usn + '_photo.jpg')
        filepath = os.path.join(uploads_dir, filename)
        cv2.imwrite(filepath, face_resized)

        # Optional: Save user details and face in memory or database
        user_faces[usn] = {
            'name': name,
            'age': age,
            'institution': institution,
            'face': face_resized,
        }

        flash("Sign-up successful! You can now sign in.", 'success')
        return redirect(url_for('signin'))  # Redirect to signin after signup

    return render_template('signup.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


from werkzeug.utils import secure_filename
from google.cloud import documentai_v1beta3 as documentai


# Configure Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your-key.json"

def analyze_document(file_path):
    """Process the uploaded document using Google Document AI."""
    client = documentai.DocumentUnderstandingServiceClient()

    # Load the file content
    with open(file_path, 'rb') as file:
        content = file.read()

    # Configure the document AI request
    input_config = documentai.types.RawDocument(content=content, mime_type='application/pdf')

    # Replace PROJECT_ID and PROCESSOR_ID with your actual IDs
    request = documentai.types.ProcessRequest(
        name="projects/YOUR_PROJECT_ID/locations/us/processors/YOUR_PROCESSOR_ID",
        raw_document=input_config
    )

    # Send the document for processing
    result = client.process_document(request=request)

    # Extract text from the document
    text = result.document.text
    return parse_information(text)

def parse_information(text):
    """Extract Name, Age, and Disability Condition from the document text."""
    lines = text.splitlines()
    name, age, condition = "Unknown", "Unknown", "Unknown"
    
    for line in lines:
        if "Name:" in line:
            name = line.split(":", 1)[1].strip()
        elif "Age:" in line:
            age = line.split(":", 1)[1].strip()
        elif "Condition:" in line:
            condition = line.split(":", 1)[1].strip()

    return {"name": name, "age": age, "disability_condition": condition}

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle file uploads and process using Document AI."""
    if request.method == 'POST':
        # Check if a file is included in the request
        if 'file' not in request.files:
            return "No file uploaded.", 400
        
        file = request.files['file']
        
        # Check if the file has a valid filename
        if file.filename == '':
            return "No selected file.", 400
        
        # Save the file to the upload folder
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Analyze the document and generate a report
            report = analyze_document(file_path)

            # Return the report in the response
            return render_template('report.html', report=report)

    # Render the upload page for GET requests
    return render_template('upload.html')

# Dictionary to store To-Do items
tasks = {}


@app.route("/todo")
def todo():
    """Render the to-do list page."""
    return render_template("todo.html", todo_list=tasks)

@app.route("/add_todo", methods=["POST"])
def add_task():
    """Add a task to the to-do list."""
    task = request.form.get("task")
    if task:
        task_id = len(tasks) + 1
        tasks[task_id] = task
    return redirect(url_for("todo"))


@app.route("/remove_todo", methods=["POST"])
def remove_task():
    """
    Remove a task from the to-do list based on partial matching.
    """
    data = request.get_json()
    task_to_remove = data.get("task").lower()

    # Find and remove the task with a partial match
    for task_id, task in list(tasks.items()):
        if is_partial_match(task.lower(), task_to_remove):
            del tasks[task_id]

    return jsonify(success=True)

def is_partial_match(str1, str2):
    """
    Check if two strings are a partial match (more than half of the characters match).
    """
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()

    # Split into words for better comparison
    words1 = str1.split()
    words2 = str2.split()

    # Check if any word in str1 matches any word in str2
    for word1 in words1:
        for word2 in words2:
            if word1 in word2 or word2 in word1:
                return True
    return False

print(tasks)



@app.route('/cr-teacher')
def cr_teacher():
    """Render the cr-teacher page."""
    return render_template('cr-teacher.html')

@app.route('/profiles')
def profiles():
    """Render the profiles page."""
    return render_template('profiles.html')

@app.route('/report')
def report():
    """Render the report page."""
    return render_template('report.html')

import re
commands = {
    'go to home': '/home', 'show home': '/home',
    'open profile': '/profile', 'view profile': '/profile',
    'view task': '/todo', 'show task': '/todo',
    'open assignments': '/assignments', 'view assignments': '/assignments',
    'go to intro': '/intro', 'show intro': '/intro',
    'open upload': '/upload', 'go to upload': '/upload',
    'sign up': '/signup', 'open signup': '/signup',
    'go to first': '/', 'show first': '/',
    'go to cr-teacher': '/cr-teacher', 'show cr-teacher': '/cr-teacher',
    'go to home page': '/home', 'show home page': '/home',
    'go to profiles': '/profiles', 'show profiles': '/profiles',
    'go to report': '/report', 'show report': '/report'
}

@app.route('/signup2', methods=['POST'])
def signup2():
    # Get form data from the request
    name = request.form.get('name')
    age = request.form.get('age')
    usn = request.form.get('usn')
    institution = request.form.get('institution')
    
    # Example: Save the data to the database (you need to configure your database)
    # Here, we're just printing the data
    if name and age and usn and institution:
        # Replace with actual database logic
        print(f"Name: {name}, Age: {age}, USN: {usn}, Institution: {institution}")
        return redirect(url_for('home'))
    else:
        return redirect(url_for('signup'))


@app.route('/process_command', methods=['POST'])
def process_command():
    data = request.get_json()
    command = data.get('command', '').lower()

    # Check if the command matches any of the predefined commands
    for key in commands:
        if re.search(r'\b' + re.escape(key) + r'\b', command):  # Match the command loosely
            # Return the corresponding local URL for the matched command
            return jsonify({'redirect_url': commands[key]})

    # If no command matches, return a default redirect (could be a local route as well)
    return jsonify({'redirect_url': '/home'})

@app.route('/teacher-signup', methods=['GET', 'POST'])
def teacher_signup():
    if request.method == 'POST':
        # Capture form inputs
        name = request.form['name']
        age = request.form['age']
        usn = request.form['usn']
        institution = request.form['institution']
        
        # Capture face
        face = capture_face()

        if face is None:
            print("Face not detected. Please try again.", 'error')
            # return redirect(url_for('teacher_signup'))
            return redirect(url_for('t_index'))

        # Define standard face dimensions
        face_resized = cv2.resize(face, (FACE_WIDTH, FACE_HEIGHT))

        # Save the resized face image
        filename = secure_filename(usn + '_photo.jpg')
        filepath = os.path.join(uploads_dir, filename)
        cv2.imwrite(filepath, face_resized)

        # Optional: Save user details and face in memory or database
        user_faces[usn] = {
            'name': name,
            'age': age,
            'institution': institution,
            'face': face_resized,
        }

        flash("Sign-up successful! You can now sign in.", 'success')
        return redirect(url_for('t_index'))  # Redirect to signin after signup

    return render_template('teacher_signup.html')


@app.route('/teacher-signup2', methods=['POST'])
def teacher_signup2():
    # Get form data from the request
    name = request.form.get('name')
    age = request.form.get('age')
    usn = request.form.get('usn')
    institution = request.form.get('institution')
    
    # Example: Save the data to the database (you need to configure your database)
    # Here, we're just printing the data
    if name and age and usn and institution:
        # Replace with actual database logic
        print(f"Name: {name}, Age: {age}, USN: {usn}, Institution: {institution}")
        return redirect(url_for('t-index'))
    else:
        return redirect(url_for('teacher_signup'))

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'chandu123',
    'database': 'equaledge'
}


# Utility function to interact with the MySQL database
def execute_query(query, params=(), fetchall=False, fetchone=False, connection=None):
    if connection is None:
        connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetchall:
            result = cursor.fetchall()
        elif fetchone:
            result = cursor.fetchone()
        else:
            result = None
        connection.commit()
        return result
    finally:
        cursor.close()
        if connection is None:  # Only close if not provided externally
            connection.close()

   
@app.route('/t-index',methods=['GET','POST'])
def t_index():
    return render_template('t_index.html')

import mysql.connector
@app.route('/create-test', methods=['GET', 'POST'])
def create_test():
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        created_by = request.form.get('created_by')

        if test_name and created_by:
            connection = mysql.connector.connect(**db_config)
            try:
                # Insert test
                execute_query(
                    "INSERT INTO Tests (test_name, created_by) VALUES (%s, %s)",
                    (test_name, created_by),
                    connection=connection
                )

                # Retrieve last inserted test ID
                result = execute_query("SELECT LAST_INSERT_ID() AS test_id", fetchone=True, connection=connection)
                test_id = result['test_id'] if result else None

                if test_id:
                    print(f"Test Created Successfully. Test ID: {test_id}")
                    return redirect(url_for('add_questions', test_id=test_id))
                else:
                    print("Error retrieving the test ID.")
            except mysql.connector.Error as e:
                print(f"Database Error: {e}")
            finally:
                connection.close()
        else:
            print("Test name and created_by are required!")
    return render_template('create_test.html')


@app.route('/add-questions/<int:test_id>', methods=['GET', 'POST'])
def add_questions(test_id):
    # Ensure the test_id exists in the Tests table
    test_exists = execute_query(
        "SELECT test_id FROM Tests WHERE test_id = %s",
        (test_id,),
        fetchone=True
    )
    if not test_exists:
        flash("Invalid Test ID!")
        return redirect(url_for('create_test'))

    if request.method == 'POST':
        question_text = request.form['question_text']
        if question_text:
            try:
                execute_query(
                    "INSERT INTO Questions (test_id, question_text) VALUES (%s, %s)",
                    (test_id, question_text)
                )
                flash("Question added successfully!")
            except mysql.connector.IntegrityError as e:
                flash(f"Error: {e}")
        else:
            flash("Question text is required!")
    return render_template('add_questions.html', test_id=test_id)



@app.route('/take-test', methods=['GET', 'POST'])
def take_test():
    if request.method == 'POST':
        test_id = request.form['test_id']
        if test_id:
            return redirect(url_for('view_test', test_id=test_id))
        else:
            flash("Test ID is required!")
    return render_template('take_test.html')


@app.route('/view-submissions/<int:test_id>', methods=['GET'])
def view_submissions(test_id):
    # Fetch the count of unique student submissions for the given test
    query = """
        SELECT COUNT(DISTINCT student_id) AS submission_count
        FROM Answers
        WHERE test_id = %s
    """
    result = execute_query(query, (test_id,), fetchone=True)
    
    if result:
        submission_count = result['submission_count']
    else:
        submission_count = 0
    
    return render_template('view_submissions.html', test_id=test_id, submission_count=submission_count)
def get_db_connection():
    return mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

@app.route('/view-answers-form', methods=['GET', 'POST'])
def view_answers_form():
    # Only execute the following block when it's a POST request
    if request.method == 'POST':
        # Get the test_id and student_id from the form
        test_id = request.form['test_id']
        student_id = request.form['student_id'].strip()  # Strip any spaces

        try:
            # Establish a database connection
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Query to fetch question IDs for the given test_id
            question_ids_query = """
            SELECT question_id FROM Questions WHERE test_id = %s
            """
            cursor.execute(question_ids_query, (test_id,))
            question_ids = cursor.fetchall()

            if not question_ids:
                return "No questions found for the provided test_id.", 404

            # Extract question_ids into a list
            question_ids_list = [q['question_id'] for q in question_ids]  # Using dictionary-based rows
            
            # Debugging print: Show the question_ids
            print("Question IDs for the test:", question_ids_list)

            if not question_ids_list:
                return "No question IDs found for the provided test_id.", 404

            # Construct the query with the proper number of placeholders
            placeholders = ', '.join(['%s'] * len(question_ids_list))
            query = f"""
            SELECT * FROM Answers
            WHERE student_id = %s AND question_id IN ({placeholders});
            """

            # Execute the query with proper parameters
            cursor.execute(query, (student_id, *question_ids_list))
            answers = cursor.fetchall()

            # Assuming question_ids_list is a list of question IDs you want to query
            placeholders1 = ', '.join(['%s'] * len(question_ids_list))  # Create placeholders for the list

# Define the query with the appropriate number of placeholders
            query1 = f"""
            SELECT * FROM questions
            WHERE question_id IN ({placeholders1});
            """

# Execute the query with the unpacked question_ids_list
            cursor.execute(query1, (*question_ids_list,))
            questions = cursor.fetchall()



            if not answers:
                print(f"No answers found for student_id: {student_id} and test_id: {test_id}")
                return "No answers found for the given student_id and test_id.", 404

            # Render the answers
            return render_template('view_answers.html', answers=answers,questions=questions)

        except Exception as e:
            print(f"Error occurred: {e}")
            return "An error occurred while fetching the answers.", 500
        finally:
            if connection:
                connection.close()  # Ensure connection is always closed

    # If it's a GET request, render the form for the user to input the test_id and student_id
    return render_template('view_answers_form.html')




@app.route('/view-answers/<int:test_id>', methods=['GET', 'POST'])
def view_answers(test_id):
    if request.method == 'POST':
        student_id = request.form['student_id']
        if student_id:
            try:
                answers = execute_query(
                    """
                    SELECT q.question_text, a.answer_text
                    FROM Questions q
                    JOIN Answers a ON q.question_id = a.question_id
                    WHERE a.student_id = %s AND q.test_id = %s
                    """,
                    (student_id, test_id),
                    fetchall=True
                )
                if answers:
                    return render_template('view_answers.html', answers=answers, test_id=test_id, student_id=student_id)
                else:
                    flash("No answers found for this student.")
            except mysql.connector.Error as e:
                flash(f"Error fetching answers: {e}")
        else:
            flash("Please provide a valid student ID.")
    return render_template('view_answers_form.html', test_id=test_id)

if __name__ == '__main__':
    app.run(debug=True)
