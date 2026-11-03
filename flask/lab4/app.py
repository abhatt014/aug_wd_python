from flask import Flask,render_template,request
import datetime
app = Flask(__name__)

@app.route('/')
def home():
    current_date = datetime.datetime.now()
    return render_template("index.html",curr_date=current_date)

@app.route('/contact-us')
def contact():
    return render_template("contact.html")
@app.route('/process',methods=['POST'])
def process():
    #capture form data with method post and return it as a dictionary
    details={}
    details['username'] = request.form.get('username')
    details['phone'] = request.form.get('phone')  
    details['email'] = request.form.get('email')
    details['message'] = request.form.get('message')

    return details
if __name__ == "__main__":
    app.run(debug=True)    
    