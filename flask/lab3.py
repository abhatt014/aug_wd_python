# app.py
from flask import Flask, request  # Import request object

app = Flask(__name__)

@app.route('/search')
def search():
    # request.args is a dictionary-like object containing query parameters
    query_term = request.args.get('q')  # Use .get() to avoid errors if param is missing
    category = request.args.get('category', 'all')  # Provide a default value

    if query_term:
        return f"Searching for '{query_term}' in category '{category}'."
    else:
        return "Please provide a search term using ?q=your_query"

@app.route('/api/info')
def api_info():
    name = request.args.get('name')  # For GET requests, use request.args
    age = request.args.get('age')
    response_data = {}
    if name:
        response_data['name'] = name
    if age:
        response_data['age'] = age
    if not response_data:
        return "Please provide 'name' and/or 'age' as query parameters"
    return response_data  # Flask will automatically convert this dictionary to a JSON response

if __name__ == '__main__':
    app.run(debug=True)
