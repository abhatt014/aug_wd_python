app.py
from flask import Flask

# 1. Create an instance of the Flask class
# __name__ is a special Python variable that gets the name of the current module.
# Flask uses this to know where to look for resources like templates and static files.
app = Flask(__name__)

# 2. Define a route and a view function
# The @app.route('/') decorator tells Flask that the URL path '/' (the root of your site)
# should trigger the home() function.
@app.route('/')
def home():
 # This function is called a "view function".
 # It must return the response that will be sent back to the client.
 return "Welcome to my first Flask app!"

# 3. Run the Flask development server
if __name__ == '__main__':
 # debug=True is very useful during development because:
 # - The server will automatically reload if you change your code.
 # - It provides a helpful debugger in the browser if an error occurs.
 # IMPORTANT: Do NOT use debug=True in a production environment!
 app.run(debug=True)
