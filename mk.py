from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flash messages

# MySQL Database Configuration
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


# Routes
@app.route('/')
def m():
    return render_template('m.html')

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
