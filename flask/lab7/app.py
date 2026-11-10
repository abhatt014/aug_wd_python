#Create a Flask app with an HTML form that submits data using both GET (for a search-like query) and POST (for a contact mess
from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    return f"Search results for: {query}"

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    return f"Thank you, {name}! Your message has been received."

if __name__ == '__main__':
    app.run(debug=True)