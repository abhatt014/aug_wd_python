# app1.py 192.168.81.184
# get / --> list all avail routes (api endpoints)
# get /call-app2 --> from app1 send a get req to app2 and display response
# post /api/greet --> app2 will conenct to this route
# get|post /api/greet --> app2 will connect to this route and send a post request with json data name=demo

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
APP2_URL = "http://192.168.81.188:5001"  # URL of app2
@app.route('/')
def home():
    return jsonify(
        app="app1",
        port=5000,
        try_this="open http://192.168.81.184:5000/call-app2 to call app2"
    )
@app.route('/call-app2')
def call_app2():
    response = requests.get(f"{APP2_URL}/api/info")
    return jsonify(
        app="app1",
        port=5000,
        app2_response=response.json()
    )
@app.route('/api/greet', methods=['POST']) 
def greet():
    data = request.get_json()
    name = data.get('name', 'Guest')
    return jsonify(
        message=f"Hello, {name}! Greetings from app1."
    )    

@app.route('/api/info', methods=['GET', 'POST'])
def info():
    if request.method == 'GET':
        return jsonify(
            app="app1",
            port=5000,
            message="This is app1 responding to a GET request."
        )
    elif request.method == 'POST':
        data = request.get_json()
        return jsonify(
            app="app1",
            port=5000,
            received_data=data
        )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
