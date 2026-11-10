from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
app = Flask(__name__)
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='dbuser',
        password='redhat',
        database='pizza'
    )

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/register')
def register_form():
    return render_template('register.html')    
@app.route('/contact')
def contact():
    return render_template('contact.html')
@app.route('/processmessage', methods=['POST'])
def process_message():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    message = request.form.get('message')

    # Here you can process the form data, e.g., save it to a database or send an email
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (name, phone, email, message) VALUES (%s, %s, %s, %s)', (name, phone, email, message))
    conn.commit()
    cursor.close()
    conn.close()    
    return render_template('confirmation.html', name=name)    
if __name__ == '__main__':
    app.run(debug=True)