# app.py (continued from above, or a new file with the Flask setup)
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Welcome to my first Flask app!"

@app.route('/about')
def about_page():
    return "This is the About Us page."

@app.route('/contact')
def contact_page():
    return "Contact us at contact@example.com"

if __name__ == '__main__':
    app.run(debug=True)
