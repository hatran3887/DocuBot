# DocuBot

> Status: In aktiver Entwicklung. Der RAG-Chat läuft. Diese README wird mit dem Projekt weiter aktualisiert.

## Über das Projekt

DocuBot ist ein einbettbarer Kundenservice-Chatbot. Er beantwortet Fragen nur auf Basis des hochgeladenen Handbuchs einer App oder Website. Betreiber laden ihr Handbuch hoch und bekommen einen Chat für ihre Seite. Nutzer stellen Fragen und erhalten Antworten mit Quellenverweis auf die passende Stelle im Handbuch. Findet der Bot keine Antwort, sagt er das ehrlich, statt zu halluzinieren. Jeder Kunde hat eine eigene, getrennte Wissensbasis.

## Wie es funktioniert

1. Kunde wird angelegt und bekommt einen API-Key.
2. Kunde lädt ein Handbuch hoch (`.txt` oder `.md`).
3. Im Hintergrund wird der Text in Chunks geteilt, mit OpenAI eingebettet und in Postgres (pgvector) gespeichert.
4. Bei einer Frage sucht der Bot die ähnlichsten Chunks des Kunden (Cosine-Distanz, HNSW-Index).
5. Die Chunks gehen als Kontext an das Modell. Das Modell antwortet nur aus diesen Quellen und zitiert sie mit `[1]`, `[2]`, ...
6. Passt keine Quelle, kommt eine klare "Keine Antwort gefunden"-Antwort.
7. Optional läuft ein zweites Modell auf denselben Chunks. Beide Antworten werden für einen Vergleich gespeichert.

## Tech-Stack

- **Backend:** FastAPI
- **Datenbank:** PostgreSQL + pgvector (HNSW-Index für die Vektorsuche)
- **ORM & Migrationen:** SQLAlchemy + Alembic
- **Embeddings & Chat:** OpenAI (`text-embedding-3-small`; Chat-Modelle `gpt-4o-mini` und `gpt-4.1-mini`)
- **Chunking:** LangChain Text-Splitters + tiktoken
- **Tracing & Feedback:** Langfuse
- **Prompt Engineering:** Kontext-Restriktion (nur aus Quellen), Zitierpflicht, Sprache der Frage übernehmen
- **Package Management:** uv

## Features

- [x] Upload eines Handbuchs pro Kunde (`.txt`, `.md`)
- [x] Getrennte Wissensbasen pro Kunde (Isolation über API-Key und `client_id`)
- [x] Chat-Endpoint mit RAG-basierter Antwortgenerierung
- [x] Quellenangabe zur beantworteten Stelle im Handbuch
- [x] Kontrollierte "Keine Antwort gefunden"-Logik
- [x] Vergleich von zwei Modellen (A/B) inkl. Kosten, Tokens und Latenz
- [x] Tracing der Anfragen und User-Feedback über Langfuse
- [ ] Weiterer LLM-Provider zum Vergleich (geplant)
- [ ] Embeddbares Chat-Widget / Code-Snippet für die Kundenseite (geplant)

## API-Endpunkte

Alle Endpunkte außer `POST /clients` und `/health` brauchen den Header `X-API-Key`.

| Methode | Pfad | Zweck |
| --- | --- | --- |
| `POST` | `/clients` | Neuen Kunden anlegen, gibt den API-Key zurück |
| `GET` | `/clients/me` | Infos zum aktuellen Kunden |
| `POST` | `/manuals/` | Handbuch hochladen (Verarbeitung läuft im Hintergrund) |
| `GET` | `/manuals/{manual_id}` | Status eines Handbuchs abfragen |
| `POST` | `/search` | Reine Chunk-Suche ohne Antwortgenerierung |
| `POST` | `/chat` | Frage stellen, Antwort mit Quellen bekommen |
| `GET` | `/chat/{conversation_id}/messages` | Verlauf einer Konversation |
| `POST` | `/chat/messages/{message_id}/feedback` | Daumen hoch / runter zu einer Antwort |
| `GET` | `/health` | Healthcheck |

Die interaktive API-Doku liegt nach dem Start unter `/docs`.

## Setup (lokal)

```bash
# Repository klonen
git clone <repo-url>
cd docubot

# uv installieren, falls noch nicht vorhanden (macOS)
brew install uv

# Virtuelle Umgebung erstellen und aktivieren
uv venv
source .venv/bin/activate

# Abhängigkeiten installieren
uv pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env mit eigenem OpenAI-Key, DB-Zugang und Langfuse-Keys befüllen

# Datenbank starten (PostgreSQL mit pgvector via Docker)
docker compose up -d

# Schema anlegen
alembic upgrade head

# Server starten
uvicorn app.main:app --reload
```

Der Server läuft dann auf `http://127.0.0.1:8000`.

## Umgebungsvariablen

Die wichtigsten Werte (siehe `.env.example`):

- `DATABASE_URL` – Verbindung zur PostgreSQL-Datenbank
- `OPENAI_API_KEY` – Key für Embeddings und Chat
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_ENABLED` – Tracing
- `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_BATCH_SIZE` – Embedding-Einstellungen
- `UPLOAD_DIR`, `MAX_UPLOAD_SIZE` – Datei-Upload

## Modellvergleich

Ist der Vergleich aktiv, laufen bei jeder Frage zwei Modelle auf denselben Quellen. Beide Antworten landen mit Kosten, Tokens und Latenz in der Tabelle `answer_comparisons`. Mit `scripts/review.py` kann man die Paare blind bewerten (links/rechts/unentschieden), um Modelle und Prompts zu vergleichen.

## Projektstatus

Dieses Projekt ist Teil eines AI-Engineering-Abschlussprojekts. Der Kern (Upload, Ingestion, RAG-Chat, Quellen, Modellvergleich, Tracing) steht. Als Nächstes folgen ein einbettbares Widget und ein weiterer Provider zum Vergleich.

## Lizenz

TBD
