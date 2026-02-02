import argparse
import sys
import time
from modules.llm_engine import OllamaClient
from modules.image_engine import ComfyClient
from modules.airtable_client import AirtableClient
from modules.utils import setup_logging

logger = setup_logging("Main")

def run_story_mode(topic: str):
    """
    Phase 1: Generiert Story & speichert in Airtable.
    KEINE Bildgenerierung hier -> VRAM bleibt sauber.
    """
    logger.info(f"🚀 --- START: STORY MODUS (Thema: {topic}) ---")
    
    # 1. Init Clients
    llm = OllamaClient()
    airtable = AirtableClient()

    # 2. Generierung
    story_data = llm.generate_story(topic)
    if not story_data:
        logger.error("❌ Keine Story generiert. Abbruch.")
        sys.exit(1)

    title = story_data.get("title", "Unbekannter Titel")
    blocks = story_data.get("blocks", [])

    # 3. Speichern in Airtable
    try:
        # Buch anlegen
        book_id = airtable.create_book(title, topic)
        logger.info(f"📚 Buch '{title}' in Airtable angelegt (ID: {book_id}).")

        # Szenen anlegen
        scene_count = 0
        current_text_buffer = ""
        
        for block in blocks:
            b_type = block.get("type")
            content = block.get("content")

            if b_type == "text":
                current_text_buffer = content # Wir merken uns den Text für die nächste Szene oder speichern ihn separat
                # Vereinfachung: Wir speichern Text oft zusammen mit dem Bildprompt oder als eigene "Szene" ohne Bild?
                # Bessere Logik für Airtable:
                # Wir gehen davon aus, dass ein "text" Block VOR einem "image_prompt" Block kommt.
                # Oder wir speichern einfach alles linear.
                # Hier: Wir speichern jede "Szene" wenn ein Image Prompt kommt.
                pass
            
            elif b_type == "image_prompt":
                scene_count += 1
                # Wir nehmen den letzten Text als Kontext für die Szene, falls vorhanden
                airtable.add_scene(
                    book_id=book_id, 
                    scene_number=scene_count, 
                    text=current_text_buffer, 
                    image_prompt=content
                )
                logger.info(f"   + Szene {scene_count} gespeichert.")
                current_text_buffer = "" # Reset für nächsten Abschnitt

        # Falls noch Text übrig ist ohne Bild (z.B. Ende), könnten wir das auch speichern, 
        # aber unser aktuelles Schema erwartet 'Image Prompt'. 
        # Wir lassen es für MVP einfach.

    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern in Airtable: {e}")
        sys.exit(1)

    # 4. Cleanup
    logger.info("🧹 Bereinige VRAM (Ollama entladen)...")
    llm.unload_model()
    logger.info("✅ Story Modus fertig. Du kannst jetzt 'python main.py art' starten.")

def run_art_mode():
    """
    Phase 2: Holt 'Pending' Szenen aus Airtable & generiert Bilder.
    Ollama ist hier aus, also volle 6GB VRAM für ComfyUI.
    """
    logger.info("🎨 --- START: ART MODUS ---")

    # 1. Init Clients
    airtable = AirtableClient()
    # ComfyClient erst initialisieren, wenn wir wirklich was zu tun haben? 
    # Nein, Check ist billig.
    
    pending_scenes = airtable.get_pending_scenes()
    
    if not pending_scenes:
        logger.info("🤷‍♂️ Keine offenen Szenen in Airtable gefunden. Alles erledigt!")
        return

    logger.info(f"🖌 Habe {len(pending_scenes)} Szenen zum Malen gefunden.")
    
    # Init Comfy nur wenn nötig
    comfy = ComfyClient()

    for record in pending_scenes:
        fields = record.get("fields", {})
        scene_id = record.get("id")
        prompt = fields.get("Image Prompt")
        book_ids = fields.get("Book", [])
        scene_num = fields.get("Scene Number", 0)
        
        # Dateiname generieren (BuchID_SceneX)
        safe_book_id = book_ids[0] if book_ids else "unknown_book"
        filename = f"{safe_book_id}_scene_{scene_num}"
        
        logger.info(f"🎨 Generiere Bild für Szene {scene_num} (ID: {scene_id})...")
        
        # Generierung
        image_path = comfy.generate_image(prompt, filename)
        
        if image_path:
            # Update Airtable
            airtable.update_scene_image(scene_id, str(image_path))
        else:
            logger.error(f"❌ Bild fehlgeschlagen für Szene {scene_id}")

    logger.info("✅ Alle Aufträge abgearbeitet.")

def main():
    parser = argparse.ArgumentParser(description="Low-VRAM Kids Book Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: Story
    parser_story = subparsers.add_parser("story", help="Generiert Text & Prompts (Airtable)")
    parser_story.add_argument("topic", type=str, help="Das Thema des Buches")

    # Subcommand: Art
    parser_art = subparsers.add_parser("art", help="Generiert Bilder für offene Szenen")

    args = parser.parse_args()

    if args.command == "story":
        run_story_mode(args.topic)
    elif args.command == "art":
        run_art_mode()

if __name__ == "__main__":
    main()
