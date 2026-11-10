from flask import Flask, request, render_template,redirect,url_for
import mysql.connector

app = Flask(__name__)
def db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="dbuser",
        password="redhat",
        database="pizza"
    )
@app.route('/')
def index():
    conn = db_connection()
    cur=conn.cursor(dictionary=True)
    query = "SELECT * FROM users"
    cur.execute(query)
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users
@app.route('/insert')
def insert():
    return render_template('insert.html')

@app.route('/registeruser', methods=['POST'])
def register_user():
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    conn = db_connection()
    cur = conn.cursor()
    query = "INSERT INTO users (firstname, lastname, email,phone,password) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(query, (first_name, last_name, email, phone, password))
    conn.commit()
    cur.close()
    conn.close()

    #redirct the user to index page after successful registration
    return redirect(url_for('index'))

    # return render_template('index.html')

# @app.route('/search', methods=['POST'])
# def search():
#     query = request.form.get('email')
#     return f"Search results for: {query}"    
if __name__ == '__main__':
    app.run(debug=True)