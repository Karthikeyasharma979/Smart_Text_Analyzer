from flask import Blueprint, request, jsonify,Flask
from routes.upload import upload_bp
from routes.query import query_bp
import os
import shutil
CHROMA_PATH = "./chroma_db"
app = Flask(__name__)
app.register_blueprint(upload_bp)
app.register_blueprint(query_bp)

@app.route('/',methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Documentor API!"}),200
if __name__=="__main__":
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("🧹 Chroma DB cleared.")
    app.run(debug=True)

    app.run(debug=True, port=5000)  
