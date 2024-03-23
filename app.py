from flask import Flask, render_template, redirect, url_for, request, session
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import pandas as pd
import pickle

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load student data
student_data = pd.read_excel("data/CAT-1.xlsx")
student_df = pd.DataFrame(student_data)

# Load the pickled model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load education dataset
df = pd.read_excel("data/education dataset-1.xlsx")

# Function to classify bloomers
def classify_bloomer(mark):
    if mark < 40:
        return 0  # Low Bloomer
    elif 40 <= mark < 70:
        return 1  # Medium Bloomer
    else:
        return 2  # High Bloomer

# Function to get student marks
def get_student_marks(user_id):
    if user_id in student_df['User ID'].values:
        student_marks = student_df[student_df['User ID'] == user_id].iloc[:, 2:]
        return student_marks.values.flatten()
    else:
        return None

# Function to get subject info
def get_subject_info(subject_name):
    if subject_name in df['SUBJECT'].values:
        subject_info = df[df['SUBJECT'] == subject_name]
        return subject_info[['UNIT', 'TOPIC', 'YOUTUBE LINK', 'FAST BLOOMER', 'MEDIUM BLOOMER', 'SLOW BLOOMER']].to_string(index=False)
    else:
        return None

# Read user credentials
user_credentials = pd.read_excel("data/Password.xlsx")

# Read well-known subjects and skills
well_known_data = pd.read_excel("data/Well Known.xlsx")

# Read data.csv
csv_file_path = os.path.join(os.path.dirname(__file__), 'data', 'data.csv')
data = pd.read_csv(csv_file_path)
data.columns = data.columns.str.lower()

@app.route('/')
def home():
    return render_template('summa.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/more_to_know')
def more_to_know():
    return render_template('more_to_know.html')

@app.route('/chat_with_senior')
def chat_with_senior():
    return render_template('chat_with_senior.html')

@app.route('/show_names', methods=['POST'])
def show_names():
    selected_skill = request.form['skill']
    filtered_data = data[(data['skill1'] == selected_skill) | (data['skill2'] == selected_skill)]
    names_with_links = filtered_data[['name', 'linkedin']].values.tolist()
    return render_template('names.html', skill=selected_skill, names_with_links=names_with_links)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        # Check if the user exists in the Excel sheet
        user = user_credentials[(user_credentials['UserID'] == user_id) & (user_credentials['Password'] == password)]

        if not user.empty:
            # User exists and password is correct
            # Store user_id in session and redirect to main page
            session['user_id'] = user_id
            return redirect(url_for('main'))
        else:
            # User does not exist or password is incorrect
            # Show an error message on the login page
            error_message = 'Invalid user ID or password'
            return render_template('login.html', error=error_message)

    return render_template('login.html')

@app.route('/main')
def main():
    user_id = session.get('user_id')
    return render_template('main.html', user_id=user_id)

@app.route('/analysis/<user_id>', methods=['GET', 'POST'])
def analysis(user_id):
    # Get marks for the user ID
    student_marks = get_student_marks(user_id)

    if student_marks is not None:
        bloomers = {}
        # Classify bloomers for each subject separately
        for i in range(len(student_marks)):
            subject_name = student_df.columns[2:][i]  # Exclude User ID and Student Name
            marks = student_marks[i]

            # Classify bloomers for each mark separately
            bloomers[subject_name] = classify_bloomer(marks)

        # Perform analysis and generate pie chart
        total_marks = sum(marks for marks in bloomers.values())
        percentages = {subject: (marks / total_marks) * 100 for subject, marks in bloomers.items()}
        sorted_percentages = sorted(percentages.items(), key=lambda x: x[1], reverse=True)

        # Generate pie chart
        labels = [subject for subject, _ in sorted_percentages]
        values = [marks for _, marks in sorted_percentages]

        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.read()).decode('utf-8')

        # Get subject information for all subjects
        subject_info_dict = {}
        for subject_name in bloomers.keys():
            subject_info = get_subject_info(subject_name)
            if subject_info:
                subject_info_dict[subject_name] = subject_info

        # Render the result page
        return render_template('result.html', img_data=img_data, percentages=sorted_percentages, bloomers=bloomers, subject_info_dict=subject_info_dict)

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    # Your submit feedback route implementation
    pass

if __name__ == '__main__':
    app.run(debug=True)
