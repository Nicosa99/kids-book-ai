import json
import random
import time
import websocket
import uuid
import requests
import shutil
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
from config import COMFY_URL, COMFY_WS_URL, WORKFLOWS_DIR, OUTPUT_DIR
from modules.utils import setup_logging

logger = setup_logging("Image_Engine")

class ComfyClient:
    def __init__(self):
        self.server_address = COMFY_URL
        self.ws_address = COMFY_WS_URL
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def connect(self):
        """Verbindet zum WebSocket."""
        try:
            # ComfyUI erwartet client_id im URL Parameter
            ws_url = f"{self.ws_address}?clientId={self.client_id}"
            self.ws = websocket.WebSocket()
            self.ws.connect(ws_url)
            logger.info("🔌 WebSocket Verbindung zu ComfyUI hergestellt.")
        except Exception as e:
            logger.error(f"❌ Konnte keine WebSocket Verbindung herstellen: {e}")
            raise

    def disconnect(self):
        if self.ws:
            self.ws.close()
            logger.info("🔌 WebSocket Verbindung geschlossen.")

    def load_workflow(self, workflow_name: str = "comfy_workflow_api.json") -> Dict:
        path = WORKFLOWS_DIR / workflow_name
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"❌ Workflow Datei nicht gefunden: {path}")
            raise

    def find_nodes(self, workflow: Dict) -> Tuple[str, str]:
        """
        Analysiert den Graphen und findet dynamisch:
        1. Die KSampler Node (für Seed)
        2. Die Positive Prompt Node (CLIPTextEncode)
        
        Returns: (sampler_id, prompt_node_id)
        """
        sampler_id = None
        prompt_id = None
        
        # 1. Suche KSampler
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "KSampler":
                sampler_id = node_id
                # Finde den Input Link für "positive"
                # Format: "positive": ["6", 0] -> Node ID ist "6"
                positive_input = node_data.get("inputs", {}).get("positive")
                if positive_input and isinstance(positive_input, list):
                    prompt_id = positive_input[0]
                break
        
        if not sampler_id or not prompt_id:
             # Fallback Suche: Falls kein KSampler gefunden (z.B. anderer Sampler Name), suche einfach nach CLIPTextEncode
             logger.warning("⚠️ Standard KSampler Verbindung nicht gefunden. Suche nach erstem CLIPTextEncode...")
             for node_id, node_data in workflow.items():
                 if node_data.get("class_type") == "CLIPTextEncode" and not prompt_id:
                     prompt_id = node_id
                 if node_data.get("class_type") == "KSampler" and not sampler_id:
                     sampler_id = node_id

        if not sampler_id:
            raise ValueError("Kein KSampler im Workflow gefunden.")
        if not prompt_id:
            raise ValueError("Kein Prompt-Node (CLIPTextEncode) gefunden.")
            
        logger.info(f"🔍 Graph Analyse: KSampler ID='{sampler_id}', Prompt Node ID='{prompt_id}'")
        return sampler_id, prompt_id

    def queue_prompt(self, workflow: Dict) -> str:
        """Sendet den Workflow an die API und gibt die Prompt-ID zurück."""
        p = {"prompt": workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        
        try:
            req = requests.post(f"{self.server_address}/prompt", data=data)
            return req.json()["prompt_id"]
        except Exception as e:
            logger.error(f"❌ Fehler beim Senden des Prompts: {e}")
            raise

    def get_history(self, prompt_id: str) -> Dict:
        """Holt die Metadaten des fertiggestellten Jobs."""
        try:
            res = requests.get(f"{self.server_address}/history/{prompt_id}")
            return res.json()[prompt_id]
        except Exception as e:
             logger.error(f"❌ Fehler beim Abrufen der History: {e}")
             return {}

    def download_image(self, filename: str, subfolder: str, folder_type: str, output_name: str):
        """Lädt das Bild von ComfyUI herunter und speichert es lokal im Output-Ordner."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        
        try:
            response = requests.get(f"{self.server_address}/view", params=data)
            
            # Zieldatei
            target_path = OUTPUT_DIR / f"{output_name}.png"
            
            with open(target_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"💾 Bild gespeichert: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Download des Bildes: {e}")
            return None

    def generate_image(self, prompt_text: str, filename_prefix: str) -> Optional[str]:
        """
        Hauptmethode:
        1. Lädt Workflow
        2. Setzt Prompt & Seed
        3. Sendet an ComfyUI
        4. Wartet auf WebSocket Completion
        5. Lädt Bild herunter
        """
        logger.info(f"🎨 Starte Bild-Generierung: '{filename_prefix}'")
        
        workflow = self.load_workflow()
        sampler_id, prompt_node_id = self.find_nodes(workflow)
        
        # Modifikationen am Workflow
        # 1. Prompt setzen
        workflow[prompt_node_id]["inputs"]["text"] = prompt_text
        
        # 2. Random Seed setzen (MAX INT Sicherheitshalber begrenzen)
        seed = random.randint(1, 1000000000)
        workflow[sampler_id]["inputs"]["seed"] = seed
        
        self.connect()
        try:
            prompt_id = self.queue_prompt(workflow)
            
            # WebSocket Loop: Warten bis fertig
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    
                    # Check Executing
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            logger.info("✅ Generierung abgeschlossen (ComfyUI reported finish).")
                            break
            
            # Bildinformationen aus History holen
            history = self.get_history(prompt_id)
            outputs = history['outputs']
            
            # Wir nehmen an, es gibt eine Output Node (meist die letzte)
            # Iteriere über alle Outputs und finde Images
            for node_id in outputs:
                node_output = outputs[node_id]
                if 'images' in node_output:
                    # Nimm das erste Bild
                    img_data = node_output['images'][0]
                    return self.download_image(
                        img_data['filename'], 
                        img_data['subfolder'], 
                        img_data['type'],
                        filename_prefix
                    )
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler im Image-Loop: {e}")
            return None
        finally:
            self.disconnect()
