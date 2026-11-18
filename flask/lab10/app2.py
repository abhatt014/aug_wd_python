# app2.py 
# get /			list all avail routes (api endpoints)	
# get /api/info	app1 connects to this route	
# get /call-app1	app2 will connect to app1 and display response
# post /api/greet	app2 will connect to app1 and send a post request with json data name=demo

from flask import Flask, request, jsonify
import requests
APP1_URL = "http://192.168.81.184:5000"
app = Flask(__name__)
@app.route('/api/greet', methods=['GET'])
def greet():
    name = request.args.get('name', 'Guest')
    response = requests.post(f"{APP1_URL}/api/greet", json={"name": name})
    return jsonify(
        app="app2",
        port=5001,
        app1_response=response.json()
    )   
@app.route('/')
def home():
    return jsonify(
        app="app2",
        port=5001,
        try_this="open http://192.168.81.188:5001/call-app1 to call app1"
    )
@app.route('/call-app1')
def call_app1():
    response = requests.get(f"{APP1_URL}/api/info")
    return jsonify(
        app="app2",
        port=5001,
        app1_response=response.json()
    )   
@app.route('/api/info', methods=['GET'])
def data():
    return jsonify(
        app="app2",
        port=5001,
        message="This is app2 responding to a GET request."
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)    