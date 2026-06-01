import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Gemini API settings (Gemini 3.1 only)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


# Safety Guardrails Lists
BLOCKED_KEYWORDS = [
    "hack wifi", "wifi hack", "bypass admin", "ignore instructions", 
    "reveal admin password", "admin password", "sql injection", 
    "root shell", "exploit database", "bypass guidelines", 
    "ignore previous instructions", "system admin password", 
    "ignore rules", "developer mode", "jailbreak"
]

SENSITIVE_RESPONSE_FILTER = [
    "password_123", "secret_key_abc", "master_admin_token",
    "admin_pass", "system_root_password"
]

# Prompts Paths
PROMPTS_DIR = BASE_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"
SAFETY_CHECK_PATH = PROMPTS_DIR / "safety_check.txt"
INTENT_DETECT_PATH = PROMPTS_DIR / "intent_detect.txt"
RESPONSE_GEN_PATH = PROMPTS_DIR / "response_gen.txt"
REACT_TEMPLATE_PATH = PROMPTS_DIR / "react_template.txt"
