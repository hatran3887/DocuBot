# DocuBot

> ⚠️ Status: In aktiver Entwicklung (Woche 2-3 – Backend & Datenbank Setup). Diese README wird mit fortschreitendem Projekt aktualisiert.

## Über das Projekt

DocuBot ist ein einbettbarer Kundenservice-Chatbot, der Support-Anfragen ausschließlich auf Basis des hochgeladenen Handbuchs einer App oder Website beantwortet. Betreiber laden ihr Handbuch hoch und erhalten ein Code-Snippet für einen schwebenden Chat-Button auf ihrer Seite. Nutzer stellen Fragen und erhalten Antworten inklusive Quellenverweis auf die passende Stelle im Handbuch. Findet der Bot keine Antwort, kommuniziert er das ehrlich, statt zu halluzinieren. Jeder Kunde verfügt über eine getrennte, isolierte Wissensbasis.

## Tech-Stack

- **Backend:** FastAPI
- **Datenbank:** PostgreSQL
- **LLM-Integration:** OpenAI API + mind. ein weiterer Provider zum Vergleich (geplant)
- **RAG:** Embedding & Retrieval des Handbuch-Inhalts (geplant)
- **Prompt Engineering:** mind. 2 Techniken (u. a. Kontext-Restriktion, Few-Shot-Beispiele) (geplant)
- **Package Management:** uv

## Geplante Features (MVP)

- [ ] Upload eines Handbuchs pro Kunde
- [ ] Getrennte Wissensbasen pro Kunde
- [ ] Chat-Endpoint mit RAG-basierter Antwortgenerierung
- [ ] Quellenangabe zur beantworteten Stelle im Handbuch
- [ ] Kontrollierte "Keine Antwort gefunden"-Logik
- [ ] Vergleichstabelle: Modelle/Prompting-Techniken (Kosten, Qualität, Notizen)

## Setup (lokal)

```bash
# Repository klonen
git clone <repo-url>
cd docubot

# uv installieren, falls noch nicht vorhanden (macOS)
brew install uv

# Virtuelle Umgebung erstellen
uv venv

# Umgebung aktivieren
source .venv/bin/activate

# Abhängigkeiten installieren
uv pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env mit eigenen API-Keys und DB-Zugangsdaten befüllen

# Server starten
uvicorn app.main:app --reload
```

## Projektstatus

Dieses Projekt ist Teil eines AI-Engineering-Abschlussprojekts und befindet sich aktuell in der Backend- und Datenbank-Setup-Phase. Weitere Details folgen mit fortschreitendem Entwicklungsstand.

## Lizenz

TBD