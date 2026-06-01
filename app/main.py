import logging
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

from app import orchestrator, database

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

# Define frontend static directory relative to this file
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(
    __name__,
    static_folder=str(frontend_dir),
    static_url_path="/static"
)

# Enable CORS
CORS(app)

# Initialize Database JSON
database.init_db()

@app.route("/")
def serve_index():
    if frontend_dir.exists():
        return send_from_directory(app.static_folder, "index.html")
    else:
        return "ViperAI Frontend static folder not found.", 404

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    try:
        data = request.get_json() or {}
        message = data.get("message")
        
        if not message:
            return jsonify({"error": "Message is required."}), 400
            
        response_data = orchestrator.run_chat_pipeline(message)
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error executing chat pipeline."}), 500

@app.route("/api/history", methods=["GET"])
def history_endpoint():
    try:
        history = database.get_history()
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return jsonify({"error": "Could not read chat history database."}), 500

# Standalone execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)
