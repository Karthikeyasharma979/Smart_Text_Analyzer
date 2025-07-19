from flask import Blueprint, request, jsonify
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
import os

genai.configure(api_key=os.environ.get("API_KEY"))

humanizer_bp = Blueprint("humanizer_bp", __name__)

# Load the embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

@humanizer_bp.route("/humanize", methods=["POST"])
def humanize_text():
    try:
        data = request.get_json()
        text = data.get("text")

        if not text:
            return jsonify({"error": "Missing 'text' field in JSON body"}), 400

        # Generate humanized text using Gemini
        model = genai.GenerativeModel("gemini-2.5-pro")
        prompt = f"Rewrite the following text to make it sound natural, human-like, and conversational:\n\n{text}"
        response = model.generate_content(prompt)
        humanized_text = response.text.strip()

        # Get embeddings
        embeddings = embedding_model.encode([text, humanized_text], convert_to_tensor=True)
        similarity_score = util.cos_sim(embeddings[0], embeddings[1]).item()

        # Humanization percentage: (1 - similarity)
        humanization_percent = round((1 - similarity_score) * 100, 2)

        return jsonify({
            "original": text,
            "humanized": humanized_text,
            "similarity_score": round(similarity_score, 4),
            "humanization_percentage": humanization_percent
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
