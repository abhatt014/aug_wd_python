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
@app.route('/login')    
def login_form():
    return render_template('login.html')
    
@app.route('/register')
def register_form():
    return render_template('register.html')    
@app.route('/processregistration', methods=['POST'])
def register(): 
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    password = request.form.get('password')
    #check of unique phone number and email address
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s OR phone = %s', (email, phone))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        return render_template('register.html', error='An account with this email or phone number already exists.')

    else:
        cursor.execute('INSERT INTO users (name, email, phone, address, password, role) VALUES (%s, %s, %s, %s, %s, %s)', (name, email, phone, address, password, 'customer'))
        conn.commit()
        cursor.close()
        conn.close()
        return render_template('confirmation.html', newuser=name)    

    # Here you can process the form data, e.g., save it to a database
      
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