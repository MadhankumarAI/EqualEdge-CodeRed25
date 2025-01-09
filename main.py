from flask import Flask, render_template, jsonify, request, redirect, url_for, session
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




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user sign-up."""
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        usn = request.form['usn']
        institution = request.form['institution']
        
        # Handle photo capture (biometric face)
        photo_data = request.form.get('photo')  # Base64 image string
        if photo_data:
            photo_filename = f"{usn}_photo.jpg"
            photo_path = os.path.join('static/user_photos', photo_filename)
            
            # Convert base64 string to an image and save
            image_data = base64.b64decode(photo_data.split(',')[1])
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            with open(photo_path, 'wb') as f:
                f.write(image_data)
        else:
            return "Photo is required for sign-up.", 400

        # Store user data
        users_db[usn] = {
            'name': name,
            'age': age,
            'institution': institution,
            'photo': photo_path
        }
        
        return redirect(url_for('signin'))
    
    return render_template('signup.html')

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

import re

commands = {
    'go to home': '/home', 'show home': '/home', 
    'open profile': '/profile', 'view profile': '/profile', 
    'view tasks': '/todo', 'show tasks': '/todo', 
    'open assignments': '/assignments', 'view assignments': '/assignments', 
    'go to intro': '/intro', 'show intro': '/intro', 
    'open upload': '/upload', 'go to upload': '/upload', 
    'sign up': '/signup', 'open signup': '/signup'
}


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

if __name__ == '__main__':
    app.run(debug=True)