from flask import Flask,request,jsonify
from pymongo import MongoClient
import bcrypt   
app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')  
db = client['flask']
col = db['flaskers']

@app.route('/users',methods = ['GET'])
def get():
    users = []
    for i in col.find({},{"_id":0}):
        users.append(i)
    return jsonify(users)

@app.route('/register',methods = ['POST'])
def create():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON data'}), 400

    username = data.get('username')
    password = data.get('password')
    hpw = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    existing_user = col.find_one({'username': username},{"_id":0})
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    col.insert_one({'username': username, 'password': password})
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login',methods =['POST'])
def login():
    data = request.get_json()
    user  = data.get('username')
    password = data.get('password')
    if not user or not password:
        return jsonify({'errror':'Username is requires'}),400
    exuser = col.find_one({'username':user},{"_id":0})
    expass = exuser.get('password')
    if not exuser:
        return jsonify({'error': 'User not found'}), 404
    if not bcrypt.checkpw(password.encode('utf-8'),expass.encode('utf-8')):
        return jsonify({'error': 'Invalid password'}), 401
    return jsonify({'message': 'Login successful'}), 200
    
if __name__=="__main__":
    app.run(debug=True)
