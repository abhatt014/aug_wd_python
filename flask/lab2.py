# app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome! \n"

#  is a dynamic part. Whatever is in the URL at that position
# will be passed as an argument to the profile function.

@app.route('/user/<uname>')
def profile(uname):
    return f"Hello, {username}! This is your profile page. \n"

#You can also specify the type of the dynamic part, e.g., 
@app.route('/post/<post_id>')
def show_post(post_id):
    return f"<code>Displaying post number: {post_id} (Type: {type(post_id)}) \n"
    
# @app.route('/api/<name>')
# def data_check(name):
# length = len(name)
# if length <= 5:
# return f"The name '{name}' is too short (length: {length}). \n"
# else:
# return f"The name '{name}' is okay (length: {length}). \n"
if __name__ == '__main__':
    app.run(debug=True)

