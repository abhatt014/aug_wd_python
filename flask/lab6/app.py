#: Create a Flask app that displays a predefined list of to-do items on an HTML page
from flask import Flask, render_template
app = Flask(__name__)

@app.route('/todos')
def show_todos():
    todos = [
        "Finish Flask tutorial",
        "Grocery shopping",
        "Read a chapter of a book",
        "Go for a walk"

    ]
    return render_template('todo.html', todos=todos)
if __name__ == '__main__':
    app.run(debug=True)