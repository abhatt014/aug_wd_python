from flask import Flask, request, render_template, redirect, url_for,session
import mysql.connector
from datetime import date, timedelta

# DB status values, in order, and the labels shown under the tracker
ORDER_STEPS = ['Pending approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']
STEP_LABELS = ['Waiting for approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']


app = Flask(__name__)
app.secret_key = 'aASDFG45ev3weFwes5ghER%^u'  
def friendly_time(dt):
    """'Today, 8:41 pm' / 'Yesterday, 2:05 pm' / '12 Nov 2026, 7:30 pm'"""
    t = dt.strftime('%I:%M %p').lstrip('0').lower()
    today = date.today()
    if dt.date() == today:
        return f'Today, {t}'
    if dt.date() == today - timedelta(days=1):
        return f'Yesterday, {t}'
    return f"{dt.strftime('%d %b %Y')}, {t}"

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
@app.route('/admin/users')
def admin_users():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_form'))
    user_role = session.get('user_role')
    if user_role == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin/users.html', users=users)
    else:
        return redirect(url_for('index'))  # Redirect non-admin users to the index page    
@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    return redirect(url_for('index'))  
@app.route('/admin/dashboard')
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_form'))
    user_role = session.get('user_role')
    if user_role == 'admin':
        return render_template('admin/dashboard.html')
    else:
        return redirect(url_for('index'))  # Redirect non-admin users to the index page

@app.route('/myorders')
def my_orders():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_form'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT
            o.id AS order_id,
            o.order_number,
            o.status,
            o.total_amount,
            o.created_at,
            oi.item_name,
            oi.quantity,
            oi.unit_price,
            (oi.quantity * oi.unit_price) AS item_total
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC, o.id, oi.id
    ''', (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Group flat rows -> one dict per order with a list of its items
    orders = {}
    for row in rows:
        oid = row['order_id']
        if oid not in orders:
            status = row['status']
            orders[oid] = {
                'order_number': row['order_number'],
                'status': status,
                'total_amount': row['total_amount'],
                'placed_at': friendly_time(row['created_at']),
                'step': ORDER_STEPS.index(status) if status in ORDER_STEPS else 0,
                'line_items': [],
            }
        orders[oid]['line_items'].append({
            'item_name': row['item_name'],
            'quantity': row['quantity'],
            'item_total': row['item_total'],
        })

    # dicts keep insertion order, so the ORDER BY (newest first) is preserved
    return render_template('my-orders.html',
                           orders=list(orders.values()),
                           step_labels=STEP_LABELS)          
@app.route('/login')    
def login_form():
    return render_template('login.html')
@app.route('/processlogin', methods=['POST'])
def process_login():
    email = request.form.get('email')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        # User exists, redirect to the appropriate page based on role
        if user['role'] == 'admin':
            #maintain user session
            session['user_id'] = user['id']
            #store user name in session for greeting
            session['user_name'] = user['name']
            #store user role in session for greeting
            session['user_role'] = user['role']
            return redirect(url_for('admin_dashboard'))
        else:
            #maintain user session
            session['user_id'] = user['id']
            #store user name in session for greeting
            session['user_name'] = user['name']
            return redirect(url_for('my_orders'))
    else:
        # Invalid credentials, show an error message
        return render_template('login.html', error='Invalid email or password.')    
    
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