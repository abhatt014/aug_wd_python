#Create a Flask app that serves an HTML page displaying a personalized welcome message and the current date.
from flask import Flask, render_template    
from datetime import datetime
app = Flask(__name__)
@app.route('/welcome/<username>')
def welcome(username):
    current_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('welcome.html', user=username, curr_date=current_date)
if __name__ == '__main__':
    app.run(debug=True)
    