import requests
import json
import time
from typing import List, Dict, Optional, Any
from config import OLLAMA_API_GENERATE, OLLAMA_MODEL, VRAM_COOLDOWN_SECONDS
from modules.utils import setup_logging

logger = setup_logging("LLM_Engine")

class OllamaClient:
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self.api_url = OLLAMA_API_GENERATE

    def unload_model(self) -> bool:
        """
        Zwingt Ollama, das Modell sofort aus dem VRAM zu entladen.
        Dies ist KRITISCH für den 6GB VRAM Workflow.
        """
        logger.info(f"🧹 Versuche Modell '{self.model}' aus VRAM zu entfernen...")
        
        payload = {
            "model": self.model,
            "prompt": "",  # Leerer Prompt nötig, damit Request gültig ist
            "keep_alive": 0  # 0 = Sofort entladen
        }
        
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            logger.info("✅ Modell erfolgreich entladen (VRAM frei).")
            
            # Sicherheits-Pause, damit der GPU-Speicher wirklich freigegeben wird
            time.sleep(VRAM_COOLDOWN_SECONDS)
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Fehler beim Entladen des Modells: {e}")
            return False

    def generate_story(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Generiert eine Kindergeschichte basierend auf dem Thema.
        Erwartet striktes JSON Format vom LLM mit flexiblen Content-Blöcken.
        """
        logger.info(f"📖 Generiere Geschichte zum Thema: '{topic}'...")

        # High-Quality System Prompt für 8 Szenen mit Dramaturgie
        system_prompt = (
            "You are an award-winning Children's Book Author and Art Director. "
            "Your goal is to write a captivating, emotionally resonant story (approx. 8 scenes) in GERMAN, suitable for ages 4-8. "
            "Simultaneously, you must provide highly consistent, professional image prompts in ENGLISH for Stable Diffusion.\n\n"
            
            "### STEP 1: CHARACTER DESIGN (Mental Freeze)\n"
            "Create a unique, lovable main character. Define:\n"
            "- Species & Name\n"
            "- Specific Colors (e.g., 'pastel blue body', 'orange beak')\n"
            "- Iconic Item (e.g., 'red striped scarf', 'tiny backpack')\n"
            "-> YOU MUST USE THESE EXACT VISUAL TRAITS IN EVERY SINGLE IMAGE PROMPT.\n\n"
            
            "### STEP 2: NARRATIVE STRUCTURE (8 Scenes)\n"
            "- Scenes 1-2 (Intro): Introduce character and setting. Establish a wish or problem.\n"
            "- Scenes 3-6 (Adventure): The journey, obstacles, meeting friends, or trying solutions.\n"
            "- Scenes 7-8 (Resolution): Success, lesson learned, happy ending.\n\n"
            "WRITING STYLE: Use direct dialogue, sensory words (smell, sound), and gentle humor.\n\n"
            
            "### STEP 3: PROMPT ENGINEERING RULES\n"
            "Structure: [CHARACTER], [ACTION], [SETTING], [LIGHTING], [STYLE]\n"
            "Style Suffix: '(children book illustration style:1.3), (whimsical:1.1), (hand-drawn:1.1), (vibrant colors:1.2), high quality, 8k, masterpiece'\n\n"
            
            "### OUTPUT FORMAT (STRICT JSON)\n"
            "{\n"
            '  "title": "Creative German Title",\n'
            '  "blocks": [\n'
            '    {"type": "text", "content": "German text for Scene 1..."},\n'
            '    {"type": "image_prompt", "content": "[Character defined in Step 1], waking up in [Setting], morning light, [Style Suffix]"},\n'
            '    {"type": "text", "content": "German text for Scene 2..."},\n'
            '    {"type": "image_prompt", "content": "..."}\n'
            '    // ... continue for exactly 8 scenes ...\n'
            "  ]\n"
            "}\n"
            "Output ONLY valid JSON. No markdown."
        )

        prompt = f"Write a complete story about: {topic}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,  # Streaming aktivieren
            "format": "json",
            "options": {
                "temperature": 0.7,
                "num_ctx": 8192  # Erhöhtes Kontext-Fenster für längere Stories
            }
        }

        try:
            print(f"\n🤖 {self.model} schreibt...\n" + "-"*50)
            
            response = requests.post(self.api_url, json=payload, stream=True)
            response.raise_for_status()
            
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        json_line = json.loads(decoded_line)
                        token = json_line.get("response", "")
                        print(token, end="", flush=True)
                        full_response += token
                        
                        if json_line.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            print("\n" + "-"*50 + "\n") # Abschluss
            
            try:
                story_data = json.loads(full_response)
                
                # Validierung
                if "title" in story_data and "blocks" in story_data and isinstance(story_data["blocks"], list):
                    logger.info(f"✅ Geschichte '{story_data['title']}' mit {len(story_data['blocks'])} Blöcken generiert.")
                    return story_data
                else:
                    logger.error(f"⚠️ Ungültiges JSON-Schema: {full_response[:100]}...")
                    return None
                    
            except json.JSONDecodeError as je:
                logger.error(f"❌ JSON Parsing Fehler: {je}. Raw Output: {full_response[:200]}...")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API Fehler bei Story-Generierung: {e}")
            return None