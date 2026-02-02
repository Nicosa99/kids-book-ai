from pyairtable import Api
from typing import List, Dict, Optional
import logging
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_BOOKS, AIRTABLE_TABLE_SCENES

logger = logging.getLogger("AirtableClient")

class AirtableClient:
    def __init__(self):
        if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
            logger.error("❌ Airtable Credentials fehlen in .env oder config.py!")
            raise ValueError("Airtable Credentials missing")
        
        self.api = Api(AIRTABLE_API_KEY)
        self.table_books = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_BOOKS)
        self.table_scenes = self.api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_SCENES)

    def create_book(self, title: str, topic: str) -> str:
        """Erstellt einen neuen Bucheintrag und gibt die Record ID zurück."""
        logger.info(f"📚 Erstelle Buch in Airtable: {title}")
        try:
            record = self.table_books.create({
                "Title": title,
                "Topic": topic,
                "Status": "Ready for Art" # Status setzen
            })
            return record["id"]
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Buches: {e}")
            raise

    def add_scene(self, book_id: str, scene_number: int, text: str, image_prompt: str):
        """Fügt eine Szene zu einem Buch hinzu."""
        try:
            self.table_scenes.create({
                "Book": [book_id], # Verknüpfung zum Buch
                "Scene Number": scene_number,
                "Story Text": text,
                "Image Prompt": image_prompt,
                "Image Status": "Pending"
            })
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Szene {scene_number}: {e}")

    def get_pending_scenes(self) -> List[Dict]:
        """Holt alle Szenen, die noch kein Bild haben (Status 'Pending')."""
        try:
            # Wir filtern nach Szenen, wo 'Image Status' == 'Pending'
            # Hinweis: Airtable Formeln können komplex sein, hier nutzen wir client-seitige Filterung oder formula parameter
            formula = "{Image Status} = 'Pending'"
            records = self.table_scenes.all(formula=formula)
            logger.info(f"🔍 Gefundene Szenen zum Malen: {len(records)}")
            return records
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Szenen: {e}")
            return []

    def update_scene_image(self, scene_id: str, image_path: str):
        """Setzt den Pfad zum Bild und markiert die Szene als fertig."""
        try:
            self.table_scenes.update(scene_id, {
                "Local Image Path": image_path,
                "Image Status": "Done"
            })
            logger.info(f"✅ Szene {scene_id} in Airtable aktualisiert.")
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Szene: {e}")
