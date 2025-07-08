from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import language_tool_python
import textstat
import re
from datetime import datetime
import logging
import os
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize language tool
try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool: {e}")
    tool = None

# MongoDB connection
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
    db = client['grammar_tool']
    col = db['text_analyses']
    col.create_index("user")
    col.create_index("timestamp")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    db = None
    col = None

def gram_check(text: str) -> Tuple[List[Dict], str]:
    """Grammar checking with manual correction handling and offset tracking"""
    if not tool or not text.strip():
        return [], text

    try:
        matches = tool.check(text)

        issues = []
        corrected_text = text
        offset_shift = 0  # Tracks total change in string length due to replacements

        # Extract issues (for display), based on original text
        for match in sorted(matches, key=lambda x: x.offset):
            issue = {
                "error": text[match.offset : match.offset + match.errorLength],
                "suggestions": match.replacements[:3],
                "message": match.message,
                "offset": match.offset,
                "errorLength": match.errorLength,
                "type": get_error_type(match.category)
            }
            issues.append(issue)

        # Apply corrections one by one, tracking position shifts
        for match in sorted(matches, key=lambda x: x.offset):
            if match.replacements:
                original_start = match.offset
                original_end = match.offset + match.errorLength

                # Adjust with current offset shift
                start = original_start + offset_shift
                end = original_end + offset_shift

                replacement = match.replacements[0]
                before = corrected_text[:start]
                after = corrected_text[end:]
                corrected_text = before + replacement + after

                # Update offset shift for next replacements
                shift_amount = len(replacement) - (original_end - original_start)
                offset_shift += shift_amount

                logger.info(f"Replaced at {original_start}-{original_end}: '{text[original_start:original_end]}' -> '{replacement}'")

        corrected_text = post_process_corrections(corrected_text)
        return issues, corrected_text

    except Exception as e:
        logger.error(f"Error in grammar check: {e}")
        return [], text


def post_process_corrections(text: str) -> str:
    """Additional post-processing for common correction issues"""
    # Fix spacing issues around punctuation
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    
    # Fix common incomplete phrases
    text = re.sub(r'if any of hurt', 'if any of this hurt you', text)
    text = re.sub(r'if any of this hurt(?!\s+you)', 'if any of this hurt you', text)
    
    # Fix double spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def get_error_type(category: str) -> str:
    """Simplified error type categorization"""
    if 'GRAMMAR' in category:
        return 'grammar'
    elif 'TYPO' in category:
        return 'spelling'
    elif 'PUNCT' in category:
        return 'punctuation'
    elif 'STYLE' in category:
        return 'style'
    else:
        return 'other'

def calculate_readability(text: str) -> Dict:
    """Calculate readability metrics"""
    if not text.strip():
        return {"error": "Empty text"}
    
    try:
        flesch_score = textstat.flesch_reading_ease(text)
        
        # Convert to percentage (0-100% scale)
        # Flesch scores can be negative or above 100, so we normalize
        readability_percentage = max(0, min(100, flesch_score))
        
        # Determine readability level
        if flesch_score >= 90:
            level = "Very Easy"
        elif flesch_score >= 80:
            level = "Easy"
        elif flesch_score >= 70:
            level = "Fairly Easy"
        elif flesch_score >= 60:
            level = "Standard"
        elif flesch_score >= 50:
            level = "Fairly Difficult"
        elif flesch_score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"
        
        return {
            "flesch_score": round(flesch_score, 2),
            "readability_percentage": round(readability_percentage, 2),
            "level": level,
            "word_count": len(text.split()),
            "reading_time_minutes": round(textstat.reading_time(text), 2)
        }
    except Exception as e:
        logger.error(f"Error calculating readability: {e}")
        return {"error": "Could not calculate readability"}

def calculate_correction_score(original: str, corrected: str, errors_count: int) -> float:
    """Calculate correction improvement score"""
    if original == corrected:
        return 100.0
    
    word_count = len(original.split())
    if word_count == 0:
        return 0.0
    
    # Simple correction score based on errors fixed per word
    correction_percentage = max(0, 100 - (errors_count / word_count * 100))
    return round(correction_percentage, 2)

def generate_tone_suggestions(text: str, tone: str) -> str:
    """Generate text suggestions based on tone"""
    tone_transformations = {
        'formal': {
            'replacements': {
                r'\bcan\'t\b': 'cannot',
                r'\bdon\'t\b': 'do not',
                r'\bwon\'t\b': 'will not',
                r'\bisn\'t\b': 'is not',
                r'\bI think\b': 'I believe',
                r'\bkinda\b': 'somewhat',
                r'\bgonna\b': 'going to',
                r'\bwanna\b': 'want to'
            },
            'prefix': 'I would like to respectfully present the following: ',
            'suffix': ' I hope this information proves valuable.'
        },
        'casual': {
            'replacements': {
                r'\bcannot\b': 'can\'t',
                r'\bdo not\b': 'don\'t',
                r'\bwill not\b': 'won\'t',
                r'\bis not\b': 'isn\'t',
                r'\bI believe\b': 'I think',
                r'\bsomewhat\b': 'kinda'
            },
            'prefix': 'Hey there! ',
            'suffix': ' Hope this helps!'
        },
        'professional': {
            'replacements': {
                r'\bcan\'t\b': 'cannot',
                r'\bdon\'t\b': 'do not',
                r'\bI think\b': 'In my professional opinion',
                r'\bmaybe\b': 'perhaps',
                r'\bstuff\b': 'materials'
            },
            'prefix': 'Based on my analysis, ',
            'suffix': ' Please let me know if you require further clarification.'
        },
        'friendly': {
            'replacements': {
                r'\bHello\b': 'Hi there',
                r'\bThank you\b': 'Thanks so much',
                r'\bregards\b': 'best wishes'
            },
            'prefix': 'I\'m happy to share that ',
            'suffix': ' Looking forward to hearing from you!'
        },
        'persuasive': {
            'replacements': {
                r'\bI think\b': 'I\'m confident that',
                r'\bmaybe\b': 'certainly',
                r'\bprobably\b': 'definitely',
                r'\bcould\b': 'will'
            },
            'prefix': 'You\'ll find that ',
            'suffix': ' This opportunity shouldn\'t be missed!'
        }
    }
    
    if tone not in tone_transformations:
        return text
    
    transformed = text
    tone_config = tone_transformations[tone]
    
    # Apply replacements
    for pattern, replacement in tone_config['replacements'].items():
        transformed = re.sub(pattern, replacement, transformed, flags=re.IGNORECASE)
    
    # Add prefix/suffix if text is short enough
    if len(transformed.split()) < 50:
        transformed = tone_config.get('prefix', '') + transformed + tone_config.get('suffix', '')
    
    return transformed

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "language_tool": tool is not None,
        "database": col is not None,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(status), 200

@app.route("/posttext", methods=["POST"])
def posttext():
    """Streamlined text analysis endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'user' not in data or 'text' not in data:
            return jsonify({"error": "User and text are required"}), 400
        
        text = data['text'].strip()
        user = data['user'].strip()
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        # Core analysis
        issues, corrected_text = gram_check(text)
        readability = calculate_readability(text)
        correction_score = calculate_correction_score(text, corrected_text, len(issues))
        
        # Generate tone suggestions
        tone_suggestions = {}
        tones = ['formal', 'casual', 'professional', 'friendly', 'persuasive']
        for tone in tones:
            tone_suggestions[tone] = generate_tone_suggestions(corrected_text, tone)
        
        # Simple document for database
        document = {
            "user": user,
            "text": text,
            "timestamp": datetime.utcnow(),
            "errors": issues,
            "corrected_text": corrected_text,
            "readability": readability,
            "correction_score": correction_score,
            "tone_suggestions": tone_suggestions
        }
        
        # Save to database
        document_id = None
        if col is not None:
            try:
                result = col.insert_one(document)
                document_id = str(result.inserted_id)
            except Exception as e:
                logger.error(f"Database insertion failed: {e}")
        
        # Clean response
        response = {
            "success": True,
            "document_id": document_id,
            "errors": issues,
            "corrected_text": corrected_text,
            "readability": readability,
            "correction_score": correction_score,
            "tone_suggestions": tone_suggestions
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in posttext: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/gettext", methods=["GET"])
def gettext():
    """Enhanced text retrieval with all requested data"""
    try:
        user = request.args.get('user')
        limit = int(request.args.get('limit', 10))
        
        if not user:
            return jsonify({"error": "User parameter is required"}), 400
        
        if col is None:
            return jsonify({"error": "Database not available"}), 503
        
        # Find user's texts with all data
        cursor = col.find(
            {"user": user}, 
            {
                "_id": 0,
                "text": 1,
                "timestamp": 1,
                "errors": 1,
                "corrected_text": 1,
                "readability": 1,
                "correction_score": 1,
                "tone_suggestions": 1
            }
        ).sort("timestamp", -1).limit(limit)
        
        results = list(cursor)
        
        if not results:
            return jsonify({"message": "No texts found for user", "results": []}), 404
        
        # Format response with all requested data
        formatted_results = []
        for result in results:
            formatted_result = {
                "original_text": result.get("text", ""),
                "corrected_text": result.get("corrected_text", ""),
                "timestamp": result.get("timestamp", ""),
                "readability": {
                    "score": result.get("readability", {}).get("flesch_score", 0),
                    "percentage": result.get("readability", {}).get("readability_percentage", 0),
                    "level": result.get("readability", {}).get("level", "Unknown"),
                    "word_count": result.get("readability", {}).get("word_count", 0),
                    "reading_time": result.get("readability", {}).get("reading_time_minutes", 0)
                },
                "correction_score": result.get("correction_score", 0),
                "errors": result.get("errors", []),
                "tone_suggestions": result.get("tone_suggestions", {})
            }
            formatted_results.append(formatted_result)
        
        response = {
            "success": True,
            "user": user,
            "total_found": len(results),
            "results": formatted_results
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in gettext: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/tones", methods=["GET"])
def get_available_tones():
    """Get list of available tones"""
    tones = {
        "formal": "Professional and respectful tone",
        "casual": "Relaxed and informal tone",
        "professional": "Business-appropriate tone",
        "friendly": "Warm and approachable tone",
        "persuasive": "Convincing and compelling tone"
    }
    return jsonify({"available_tones": tones}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 4000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Flask application on port {port}")
    app.run(debug=debug, port=port)