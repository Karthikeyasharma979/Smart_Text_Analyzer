from flask import Flask, Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import re
import google.generativeai as genai


# Replace "YOUR_HARDCODED_API_KEY_HERE" with your actual key if not using environment variable.
API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyByicleeKHnDKL6iaHdnkEUh10w0wSvfUs")
genai.configure(api_key=API_KEY)

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Upload Configuration ---
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for extracted text (for demonstration purposes)
# In a production environment, consider a persistent storage solution (e.g., database)
extract = {}

# --- Blueprint for Upload and Ask Functionality ---
upload_bp = Blueprint('upload', __name__)

# Function to check allowed file extensions
def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].strip().lower()
    print(f"Checking file extension: {ext}")
    return ext in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
def upload():
    """
    Handles PDF file uploads, extracts text, and stores it in memory.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    print(f"Received file: {file.filename}")

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        print(f"File saved to: {file_path}")

        try:
            # Extract PDF content using PyMuPDF
            doc = fitz.open(file_path)
            text_content = ''
            for page in doc:
                text_content += page.get_text()
            doc.close()

            # Clean extracted text: remove extra whitespace and join lines
            lines = [line for line in text_content.splitlines() if line.strip()]
            cleaned_text = re.sub(r"\s+", " ", " ".join(lines)).strip()
            print(f"Extracted and cleaned text for {filename} (first 100 chars): {cleaned_text[:100]}...")

            # Store text with filename as key
            extract[filename] = cleaned_text

            return jsonify({
                "message": "File uploaded and text extracted successfully.",
                "filename": filename,
                "text_preview": cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text
            }), 200

        except Exception as e:
            print(f"Error during PDF parsing for {filename}: {e}")
            return jsonify({"error": f"PDF parsing failed: {str(e)}"}), 500

    return jsonify({"error": "File type not allowed"}), 400

# Wrapper to call Google Generative AI LLM with context
def mockllm(prompt: str) -> str:
    """
    Calls the Google Generative AI model (Gemini) to generate a response
    based on the given prompt.
    """
    try:
        
        model = genai.GenerativeModel('gemini-2.5-pro') # Updated model name
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error in LLM response: {e}")
        return f"Error in LLM response: {str(e)}"

@upload_bp.route('/ask', methods=['POST'])
def ask():
    """
    Answers a question based on the previously uploaded and extracted document text.
    """
    data = request.get_json()
    filename = data.get('filename')
    question = data.get('question')

    if not filename or not question:
        return jsonify({"error": "Both 'filename' and 'question' must be provided."}), 400

    context = extract.get(filename)
    if not context:
        return jsonify({"error": f"No text found for file: {filename}. Please upload the file first."}), 400

    # Construct prompt for the LLM
    prompt = f"""
    Based on the document content below:
    ----
    {context}
    ----
    Answer the following question: {question}

    Provide a concise and direct answer.
    """
    print(f"Asking LLM question for {filename}: {question}")
    response = mockllm(prompt)
    return jsonify({"response": response}), 200

# --- Function to List Supported Gemini Models ---
@app.route('/   ', methods=['GET'])
def list_gemini_models_route():
    """
    Provides an API endpoint to list all Gemini models accessible with the
    configured API key that support the 'generateContent' method.
    """
    supported_models = []
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_info = {
                    "name": model.name.split('/')[-1],
                    "display_name": model.display_name,
                    "description": model.description,
                    "input_token_limit": model.input_token_limit,
                    "output_token_limit": model.output_token_limit,
                    "supported_methods": model.supported_generation_methods
                }
                supported_models.append(model_info)
        return jsonify({"supported_models": supported_models}), 200
    except Exception as e:
        print(f"Error listing models via API: {e}")
        return jsonify({"error": f"Failed to list models: {str(e)}."
                                 " Please check your API key and network connection."}), 500

# --- Register Blueprint and Run App ---
app.register_blueprint(upload_bp)

if __name__ == '__main__':
    # Run the Flask app
    # For development, debug=True is useful. For production, set debug=False
    # and use a production-ready WSGI server like Gunicorn.
    print("Starting Flask application...")
    print(f"Uploads will be saved to: {UPLOAD_FOLDER}")
    print("API Endpoints:")
    print("  POST /upload - Upload a PDF file.")
    print("  POST /ask - Ask a question about an uploaded PDF.")
    print("  GET /list_gemini_models - List supported Gemini models.")
    app.run(debug=True, port=5000)
