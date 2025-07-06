from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import language_tool_python
import textstat
import re
from collections import Counter
from datetime import datetime
import logging
import os
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize language tool with error handling
try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool: {e}")
    tool = None

def gram_check(text: str) -> Tuple[List[Dict], str, List[Dict]]:
    """Enhanced grammar checking with better error handling"""
    if not tool:
        return [], text, []
    
    if not text or not text.strip():
        return [], text, []
    
    try:
        matches = tool.check(text)
        
        issues = []
        corrected_text = text 
        correction_options = []
        
        if matches:
            sorted_matches = sorted(matches, key=lambda x: x.offset, reverse=True)
            
            for match in matches:
                issue = {
                    "error": text[match.offset : match.offset + match.errorLength],
                    "suggestions": match.replacements[:5],
                    "message": match.message,
                    "offset": match.offset,
                    "errorLength": match.errorLength,
                    "category": match.category,
                    "ruleId": match.ruleId,
                    "context": {
                        "before": text[max(0, match.offset - 20):match.offset],
                        "after": text[match.offset + match.errorLength:match.offset + match.errorLength + 20]
                    },
                    "severity": categorize_severity(match.category),
                    "type": categorize_error_type(match.category, match.ruleId)
                }
                issues.append(issue)
            
            for match in sorted_matches:
                if match.replacements:
                    start = match.offset
                    end = match.offset + match.errorLength
                    replacement = match.replacements[0]
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
            
            correction_options = generate_correction_options(text, matches)
        
        return issues, corrected_text, correction_options
    
    except Exception as e:
        logger.error(f"Error in grammar check: {e}")
        return [], text, []

def categorize_severity(category: str) -> str:
    """Categorize error severity based on category"""
    high_severity = ['GRAMMAR', 'TYPOS', 'CASING']
    medium_severity = ['STYLE', 'REDUNDANCY', 'WORD_ORDER']
    
    if category in high_severity:
        return 'high'
    elif category in medium_severity:
        return 'medium'
    else:
        return 'low'

def categorize_error_type(category: str, rule_id: str) -> str:
    """Categorize error type for better UI display"""
    if 'SPELL' in rule_id or 'TYPO' in category:
        return 'spelling'
    elif 'GRAMMAR' in category:
        return 'grammar'
    elif 'PUNCT' in rule_id:
        return 'punctuation'
    elif 'STYLE' in category:
        return 'style'
    elif 'REDUNDANCY' in category:
        return 'redundancy'
    else:
        return 'other'

def generate_correction_options(original_text: str, matches: List, max_options: int = 4) -> List[Dict]:
    """Generate multiple correction options with enhanced logic"""
    if not matches:
        return [{"version": "Original", "text": original_text, "description": "No corrections needed"}]
    
    sorted_matches = sorted(matches, key=lambda x: x.offset, reverse=True)
    correction_options = []
    
    option1 = original_text
    for match in sorted_matches:
        if match.replacements:
            start = match.offset
            end = match.offset + match.errorLength
            replacement = match.replacements[0]
            option1 = option1[:start] + replacement + option1[end:]
    
    correction_options.append({
        "version": "Primary Correction",
        "text": option1,
        "description": "Using the most recommended suggestions",
        "changes_count": len([m for m in matches if m.replacements])
    })
    
    if any(len(match.replacements) > 1 for match in matches):
        option2 = original_text
        for match in sorted_matches:
            if match.replacements:
                start = match.offset
                end = match.offset + match.errorLength
                replacement = match.replacements[1] if len(match.replacements) > 1 else match.replacements[0]
                option2 = option2[:start] + replacement + option2[end:]
        
        if option2 != option1:
            correction_options.append({
                "version": "Alternative Correction",
                "text": option2,
                "description": "Using alternative suggestions where available",
                "changes_count": len([m for m in matches if len(m.replacements) > 1])
            })
    
    option3 = original_text
    high_severity_changes = 0
    for match in sorted_matches:
        if match.replacements and categorize_severity(match.category) == 'high':
            start = match.offset
            end = match.offset + match.errorLength
            replacement = match.replacements[0]
            option3 = option3[:start] + replacement + option3[end:]
            high_severity_changes += 1
    
    if high_severity_changes > 0 and option3 not in [opt["text"] for opt in correction_options]:
        correction_options.append({
            "version": "Conservative Correction",
            "text": option3,
            "description": "Only fixing critical errors (grammar, spelling, typos)",
            "changes_count": high_severity_changes
        })
    
    option4 = original_text
    style_changes = 0
    for match in sorted_matches:
        if match.replacements and match.category in ['STYLE', 'REDUNDANCY', 'WORD_ORDER']:
            start = match.offset
            end = match.offset + match.errorLength
            replacement = match.replacements[0]
            option4 = option4[:start] + replacement + option4[end:]
            style_changes += 1
    
    if style_changes > 0 and option4 not in [opt["text"] for opt in correction_options]:
        correction_options.append({
            "version": "Style Enhancement",
            "text": option4,
            "description": "Focus on style and readability improvements",
            "changes_count": style_changes
        })
    
    return correction_options[:max_options]

def calculate_readability(text: str) -> Dict:
    """Enhanced readability calculation with more metrics"""
    if not text.strip():
        return {"error": "Empty text provided"}
    
    try:
        word_count = len(text.split())
        sentence_count = textstat.sentence_count(text)
        char_count = len(text)
        
        scores = {
            "flesch_reading_ease": round(textstat.flesch_reading_ease(text), 2),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(text), 2),
            "gunning_fog": round(textstat.gunning_fog(text), 2),
            "automated_readability_index": round(textstat.automated_readability_index(text), 2),
            "coleman_liau_index": round(textstat.coleman_liau_index(text), 2),
            "reading_time_minutes": round(textstat.reading_time(text, ms_per_char=14.69), 2),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "character_count": char_count,
            "avg_words_per_sentence": round(word_count / sentence_count, 2) if sentence_count > 0 else 0,
            "lexicon_count": textstat.lexicon_count(text),
            "syllable_count": textstat.syllable_count(text)
        }
        
        flesch_score = scores["flesch_reading_ease"]
        if flesch_score >= 90:
            readability_level = "Very Easy"
            audience = "5th grade"
        elif flesch_score >= 80:
            readability_level = "Easy"
            audience = "6th grade"
        elif flesch_score >= 70:
            readability_level = "Fairly Easy"
            audience = "7th grade"
        elif flesch_score >= 60:
            readability_level = "Standard"
            audience = "8th-9th grade"
        elif flesch_score >= 50:
            readability_level = "Fairly Difficult"
            audience = "10th-12th grade"
        elif flesch_score >= 30:
            readability_level = "Difficult"
            audience = "College level"
        else:
            readability_level = "Very Difficult"
            audience = "Graduate level"
        
        scores["readability_level"] = readability_level
        scores["target_audience"] = audience
        
        return scores
    except Exception as e:
        logger.error(f"Error calculating readability: {e}")
        return {"error": "Could not calculate readability scores"}

def analyze_text_complexity(text: str) -> Dict:
    """Additional text complexity analysis"""
    try:
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        complex_words = [word for word in words if textstat.syllable_count(word) >= 3]
        
        analysis = {
            "complex_words_count": len(complex_words),
            "complex_words_percentage": round((len(complex_words) / len(words)) * 100, 2) if words else 0,
            "avg_sentence_length": round(len(words) / len([s for s in sentences if s.strip()]), 2) if sentences else 0,
            "longest_sentence": max([len(s.split()) for s in sentences if s.strip()], default=0),
            "shortest_sentence": min([len(s.split()) for s in sentences if s.strip()], default=0)
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error in complexity analysis: {e}")
        return {}

try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
    db = client['grammar_tool']
    col = db['text_analyses']
    
    col.create_index("user")
    col.create_index("timestamp")
    col.create_index([("user", 1), ("timestamp", -1)])
    
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    db = None
    col = None

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
    """Enhanced text analysis endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['user', 'text']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
            if not isinstance(data[field], str):
                return jsonify({"error": f"{field} must be a string"}), 400
        
        if not data['text'].strip():
            return jsonify({"error": "Text cannot be empty"}), 400
        
        text = data['text'].strip()
        user = data['user'].strip()
        
        issues, corrected_text, correction_options = gram_check(text)
        
        readability_scores = calculate_readability(text)
        
        complexity_analysis = analyze_text_complexity(text)
        
        document = {
            "user": user,
            "text": text,
            "timestamp": datetime.utcnow(),
            "analysis": {
                "errors": {
                    "count": len(issues),
                    "details": issues,
                    "by_category": dict(Counter([issue["category"] for issue in issues])),
                    "by_severity": dict(Counter([issue["severity"] for issue in issues])),
                    "by_type": dict(Counter([issue["type"] for issue in issues]))
                },
                "corrections": {
                    "corrected_text": corrected_text,
                    "options": correction_options,
                    "improvement_percentage": calculate_improvement_percentage(text, corrected_text)
                },
                "readability": readability_scores,
                "complexity": complexity_analysis
            },
            "metadata": {
                "processing_time": datetime.utcnow(),
                "version": "2.0"
            }
        }
        
        document_id = None
        if col is not None:
            try:
                result = col.insert_one(document)
                document_id = str(result.inserted_id)
            except Exception as e:
                logger.error(f"Database insertion failed: {e}")
        
        response_data = {
            "success": True,
            "message": "Text analyzed successfully",
            "document_id": document_id,
            "analysis": document["analysis"],
            "original_text": text,
            "user": user
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in posttext: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

def calculate_improvement_percentage(original: str, corrected: str) -> float:
    """Calculate percentage improvement between original and corrected text"""
    if original == corrected:
        return 0.0
    
    original_score = textstat.flesch_reading_ease(original) if original.strip() else 0
    corrected_score = textstat.flesch_reading_ease(corrected) if corrected.strip() else 0
    
    if original_score == 0:
        return 0.0
    
    improvement = ((corrected_score - original_score) / original_score) * 100
    return round(improvement, 2)

@app.route("/gettext", methods=["GET"])
def gettext():
    """Enhanced text retrieval with filtering and pagination"""
    try:
        user = request.args.get('user')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        if not user:
            return jsonify({"error": "User query parameter is required"}), 400
        
        if col is None:
            return jsonify({"error": "Database not available"}), 503
        
        query = {"user": user}
        
        cursor = col.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
        results = list(cursor)
        
        total_count = col.count_documents(query)
        
        if not results:
            return jsonify({"message": "No text found for the user", "total": 0, "results": []}), 404
        
        response = {
            "success": True,
            "user": user,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "results": results
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in gettext: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/analyze/<user>", methods=["GET"])
@app.route("/analyze/<user>/<int:limit>", methods=["GET"])
def get_user_analysis(user: str, limit: int = 10):
    """Enhanced user analysis with detailed statistics"""
    try:
        if col is None:
            return jsonify({"error": "Database not available"}), 503
        
        pipeline = [
            {"$match": {"user": user}},
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
            {"$group": {
                "_id": None,
                "total_texts": {"$sum": 1},
                "total_errors": {"$sum": "$analysis.errors.count"},
                "avg_readability": {"$avg": "$analysis.readability.flesch_reading_ease"},
                "avg_word_count": {"$avg": "$analysis.readability.word_count"},
                "recent_analyses": {"$push": {
                    "text": {"$substr": ["$text", 0, 100]},
                    "timestamp": "$timestamp",
                    "error_count": "$analysis.errors.count",
                    "readability_level": "$analysis.readability.readability_level",
                    "word_count": "$analysis.readability.word_count"
                }}
            }}
        ]
        
        result = list(col.aggregate(pipeline))
        
        if not result:
            return jsonify({"message": "No data found for user"}), 404
        
        stats = result[0]
        
        # Calculate trends and insights
        recent_analyses = stats.get("recent_analyses", [])
        if len(recent_analyses) > 1:
            trend_analysis = calculate_user_trends(recent_analyses)
        else:
            trend_analysis = {}
        
        summary = {
            "user": user,
            "statistics": {
                "total_texts_analyzed": stats.get("total_texts", 0),
                "total_errors_found": stats.get("total_errors", 0),
                "average_readability_score": round(stats.get("avg_readability", 0), 2),
                "average_word_count": round(stats.get("avg_word_count", 0), 2),
                "error_rate": round(stats.get("total_errors", 0) / stats.get("total_texts", 1), 2)
            },
            "trends": trend_analysis,
            "recent_analyses": recent_analyses[:10],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Error in get_user_analysis: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

def calculate_user_trends(analyses: List[Dict]) -> Dict:
    """Calculate user writing trends"""
    try:
        if len(analyses) < 2:
            return {}
        
        # Sort by timestamp
        sorted_analyses = sorted(analyses, key=lambda x: x.get("timestamp", datetime.min))
        
        # Calculate trends
        error_counts = [a.get("error_count", 0) for a in sorted_analyses]
        word_counts = [a.get("word_count", 0) for a in sorted_analyses]
        
        trends = {
            "error_trend": "improving" if error_counts[-1] < error_counts[0] else "declining" if error_counts[-1] > error_counts[0] else "stable",
            "word_count_trend": "increasing" if word_counts[-1] > word_counts[0] else "decreasing" if word_counts[-1] < word_counts[0] else "stable",
            "consistency_score": calculate_consistency_score(error_counts)
        }
        
        return trends
    except Exception as e:
        logger.error(f"Error calculating trends: {e}")
        return {}

def calculate_consistency_score(values: List[int]) -> float:
    """Calculate consistency score (lower variance = higher consistency)"""
    if len(values) < 2:
        return 1.0
    
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    
    # Normalize to 0-1 scale (higher = more consistent)
    consistency = 1 / (1 + variance)
    return round(consistency, 3)

@app.route("/stats/global", methods=["GET"])
def global_stats():
    """Global platform statistics"""
    try:
        if col is None:
            return jsonify({"error": "Database not available"}), 503
        
        pipeline = [
            {"$group": {
                "_id": None,
                "total_users": {"$addToSet": "$user"},
                "total_analyses": {"$sum": 1},
                "total_errors": {"$sum": "$analysis.errors.count"},
                "avg_readability": {"$avg": "$analysis.readability.flesch_reading_ease"}
            }}
        ]
        
        result = list(col.aggregate(pipeline))
        
        if not result:
            return jsonify({"message": "No data available"}), 404
        
        stats = result[0]
        
        global_summary = {
            "total_users": len(stats.get("total_users", [])),
            "total_analyses": stats.get("total_analyses", 0),
            "total_errors_found": stats.get("total_errors", 0),
            "average_readability": round(stats.get("avg_readability", 0), 2),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return jsonify(global_summary), 200
        
    except Exception as e:
        logger.error(f"Error in global_stats: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

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
