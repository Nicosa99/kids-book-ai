# 🧠 Gemini Project Context: Kids Book Generator

**Stand:** 02. Februar 2026
**Projekt:** Lokaler, VRAM-optimierter Kinderbuch-Generator.
**OS:** Linux
**Hardware:** NVIDIA GTX 1660 Super (6GB VRAM) -> **CRITICAL CONSTRAINT**

## 🏗 Architektur & Philosophie

Das System ist streng **sequenziell** aufgebaut, um Out-of-Memory (OOM) Fehler auf der 6GB Grafikkarte zu vermeiden. Es darf **niemals** Ollama und ComfyUI gleichzeitig laufen.

### Workflow
1.  **Phase 1: Story Agent (`story`)**
    *   **Engine:** Ollama (Llama 3.1 8B, 4-bit quantisiert).
    *   **Aufgabe:** Generiert Titel, 8 Szenen (Text) und konsistente Bild-Prompts.
    *   **Output:** Schreibt direkt in **Airtable**.
    *   **Safety:** Entlädt das Modell am Ende (`keep_alive: 0`) -> VRAM wird frei.

2.  **Phase 2: Art Agent (`art`)**
    *   **Engine:** ComfyUI (Stable Diffusion 1.5 Checkpoint `dreamshaper_8`).
    *   **Aufgabe:** Pollt Airtable nach Szenen mit `Image Status: Pending`.
    *   **Prozess:** Sendet Prompt an ComfyUI API -> Wartet auf WebSocket -> Speichert Bild lokal.
    *   **Update:** Setzt `Image Status: Done` und speichert Pfad in Airtable.

## 🗄 Datenmodell (Airtable)

**Base ID:** `appwJXrFP3qCwXmTn` (in `.env`)

### Tabelle 1: `Books`
*   `Title` (Single Line Text)
*   `Topic` (Single Line Text)
*   `Status` (Single Select: "Ready for Art", "Done")

### Tabelle 2: `Scenes`
*   `Book` (Link to `Books`)
*   `Scene Number` (Number)
*   `Story Text` (Long Text) - *Die Geschichte*
*   `Image Prompt` (Long Text) - *Englischer Prompt für SD*
*   `Image Status` (Single Select: "Pending", "Done")
*   `Local Image Path` (Single Line Text) - *Absoluter Pfad zum generierten Bild*

## 🎨 Prompt Engineering Strategy

Um Konsistenz zu garantieren, nutzt der `llm_engine` eine **Character Freeze** Technik:
1.  **Step 1:** Erfinde Charakter-Details (Farbe, Kleidung).
2.  **Step 2:** Injiziere diese Details strikt in **jeden** Prompt.
3.  **Step 3:** Hänge immer den **Style Suffix** an:
    ` (children book illustration style:1.3), (whimsical:1.1), (hand-drawn:1.1), (vibrant colors:1.2), high quality`

## ⚙️ ComfyUI Settings (Tuned)
Datei: `workflows/comfy_workflow_api.json`
*   **Resolution:** 768x512 (Landscape).
*   **Model:** SD 1.5 (Dreamshaper 8).
*   **Sampler:** DPM++ 2M Karras, 25 Steps, CFG 7.0.
*   **Negative Prompt:** Safety-Net gegen Deformationen.

## 📝 Wichtige Befehle

```bash
# Umgebung aktivieren
source venv/bin/activate

# Story generieren (Ollama muss laufen)
python main.py story "Thema hier"

# Bilder malen (ComfyUI muss laufen, Ollama aus)
python main.py art
```

## 🔮 Future Roadmap
*   **PDF Engine:** Zusammenfügen von Text & Bild.
*   **Style Loras:** Nutzung von `.safetensors` für Aquarell-Look.
*   **Cloud Training:** Fine-Tuning von Llama auf AWS (geplant).
