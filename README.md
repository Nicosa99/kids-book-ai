# 📚 Low-VRAM Kids Book Generator

Ein vollautomatisierter, lokaler Workflow zur Erstellung von illustrierten Kinderbüchern mit KI. Optimiert für Consumer-Hardware (z.B. NVIDIA GTX 1660 Super mit 6GB VRAM) durch strikte Ressourcentrennung.

## 🌟 Features

*   **Ressourcenschonend:** Trennung von Text-Generierung (Ollama) und Bild-Generierung (ComfyUI) verhindert "Out of Memory" (OOM) Abstürze.
*   **Qualität:** Nutzung von Llama 3.1 für logische Geschichten und Stable Diffusion 1.5 (getunt) für konsistente Illustrationen.
*   **Datenbank-gestützt:** Airtable dient als "Single Source of Truth" für Buch-Metadaten, Texte und Bild-Status.
*   **Modular:** Erweiterbar für PDF-Generierung, Massenproduktion oder Cloud-Training.

## 🛠 Voraussetzungen

*   **OS:** Linux (empfohlen) oder Windows (WSL2).
*   **GPU:** NVIDIA Grafikkarte (min. 6GB VRAM).
*   **Software:**
    *   [Ollama](https://ollama.com/) (running locally).
    *   [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (running locally).
    *   Python 3.10+.
*   **Cloud Services:**
    *   Airtable Account (Free Plan reicht).

## ⚙️ Installation

1.  **Repository klonen & Umgebung:**
    ```bash
    git clone <dein-repo-url>
    cd kids-book-workflow
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Ollama einrichten:**
    *   Installiere Ollama.
    *   Ziehe das Modell: `ollama pull llama3.1`
    *   Starte den Server (meist automatisch).

3.  **ComfyUI einrichten:**
    *   Installiere ComfyUI.
    *   Lade den Checkpoint `dreamshaper_8.safetensors` in `ComfyUI/models/checkpoints/`.
    *   Starte es im "Low VRAM" Modus (falls nötig):
        ```bash
        python main.py --lowvram --preview-method auto
        ```

4.  **Airtable Setup:**
    *   Erstelle eine Base.
    *   Erstelle Tabelle **Books**: Spalten `Title` (Text), `Topic` (Text), `Status` (Single Select).
    *   Erstelle Tabelle **Scenes**: Spalten `Book` (Link to Books), `Scene Number` (Number), `Story Text` (Long Text), `Image Prompt` (Long Text), `Image Status` (Single Select), `Local Image Path` (Text).
    *   Generiere einen Personal Access Token mit Scopes `data.records:read` und `data.records:write`.

5.  **Konfiguration (.env):**
    Erstelle eine `.env` Datei im Hauptverzeichnis:
    ```ini
    AIRTABLE_API_KEY=dein_token_hier
    AIRTABLE_BASE_ID=deine_base_id_hier
    ```

## 🚀 Benutzung

Der Workflow ist in zwei Phasen unterteilt, um den VRAM zu schonen.

### Phase 1: Der Autor (Story Mode)
Generiert Titel, Text und Bild-Prompts. Speichert alles in Airtable.
Ollama muss laufen.

```bash
./venv/bin/python main.py story "Ein kleiner Pinguin der fliegen will"
```

### Phase 2: Der Illustrator (Art Mode)
Liest offene Szenen aus Airtable und generiert Bilder mit ComfyUI.
**Wichtig:** Ollama sollte entladen sein (passiert automatisch am Ende von Phase 1), ComfyUI muss laufen.

```bash
./venv/bin/python main.py art
```

Die fertigen Bilder landen im Ordner `output/`.

## 📁 Projektstruktur

```
.
├── config.py           # Zentrale Konfiguration
├── main.py             # Haupt-Skript (CLI Entrypoint)
├── modules/
│   ├── airtable_client.py  # Datenbank-Kommunikation
│   ├── llm_engine.py       # Llama 3.1 Wrapper (Story Logic)
│   ├── image_engine.py     # ComfyUI API Wrapper
│   └── utils.py            # Logging & Tools
├── workflows/
│   └── comfy_workflow_api.json # Getunter SD 1.5 Workflow
├── output/             # Zielordner für generierte Bilder
└── docs/               # Dokumentation & Research
```

## 🧠 Prompt Engineering

Das System nutzt eine fortgeschrittene Prompting-Strategie ("Character Freeze"):
1.  Der LLM definiert zuerst visuelle Merkmale des Charakters.
2.  Diese Merkmale werden strikt in jeden Image-Prompt injiziert.
3.  Ein "Style Suffix" sorgt für konsistenten Illustrations-Look.

## 🔮 Roadmap

- [ ] PDF-Export Modul (Text + Bild = Buch).
- [ ] Massen-Produktions-Modus (Themen-Liste abarbeiten).
- [ ] Human-in-the-Loop GUI (Text-Korrektur vor dem Malen).
- [ ] Cloud-Upload der Bilder zu Airtable.
