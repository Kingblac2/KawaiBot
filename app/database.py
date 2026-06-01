import json
import os
import datetime
from pathlib import Path
from typing import List, Dict

# If running on Vercel, store the json database in /tmp to avoid write-permission errors.
IS_VERCEL = os.environ.get("VERCEL") == "1"

if IS_VERCEL:
    CONVO_FILE = Path("/tmp/conversations.json")
else:
    CONVO_FILE = Path(__file__).resolve().parent.parent / "conversations.json"

# In-memory fallback if file system is completely locked or unavailable
_in_memory_db = []

def init_db():
    try:
        if not CONVO_FILE.exists():
            with open(CONVO_FILE, "w") as f:
                json.dump([], f)
    except Exception as e:
        # Fallback to in-memory initialization
        pass

def save_chat(message: str, response_json: Dict) -> Dict:
    """
    Saves a chat message and response to the database (file or memory).
    """
    init_db()
    
    chat_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": message,
        "intent": response_json.get("intent", "unknown"),
        "risk_level": response_json.get("risk_level", "low"),
        "response": response_json.get("response", ""),
        "reasoning_steps": response_json.get("reasoning_steps", []),
        "react_thought": response_json.get("react_thought", ""),
        "react_action": response_json.get("react_action", ""),
        "react_observation": response_json.get("react_observation", ""),
        "full_data": response_json
    }
    
    # 1. Attempt writing to file
    try:
        data = []
        if CONVO_FILE.exists():
            with open(CONVO_FILE, "r") as f:
                data = json.load(f)
        
        data.append(chat_entry)
        
        with open(CONVO_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        return chat_entry
    except Exception as e:
        # 2. Fallback to in-memory store
        global _in_memory_db
        _in_memory_db.append(chat_entry)
        return chat_entry

def get_history() -> List[Dict]:
    init_db()
    # 1. Try file storage
    try:
        if CONVO_FILE.exists():
            with open(CONVO_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
        
    # 2. Fallback to in-memory store
    return _in_memory_db
