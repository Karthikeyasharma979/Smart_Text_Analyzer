from flask import Blueprint, request, jsonify,Flask
from routes.upload import upload_bp

app = Flask(__name__)
app.register_blueprint(upload_bp)

@app.route('/',methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Documentor API!"}),200
if __name__=="__main__":
    app.run(debug=True, port=5000)
