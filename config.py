import os
from pathlib import Path
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
WORKFLOWS_DIR = BASE_DIR / "workflows"

# Airtable Settings
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_BOOKS = "Books"
AIRTABLE_TABLE_SCENES = "Scenes"

# Ollama Settings (Text Engine)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_API_GENERATE = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = "llama3.1"

# ComfyUI Settings (Image Engine)
COMFY_URL = "http://127.0.0.1:8188"
COMFY_WS_URL = "ws://127.0.0.1:8188/ws"

# Hardware Constraints
VRAM_COOLDOWN_SECONDS = 10