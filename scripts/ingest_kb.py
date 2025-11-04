import os
import uuid
from dotenv import load_dotenv

load_dotenv(".env")

try:
    from openai import AzureOpenAI
    from azure.core.credentials import AzureKeyCredential
    from pinecone import Pinecone
except Exception as e:
    raise SystemExit(f"Fehlende Bibliotheken: {e}. Installiere mit: pip install openai azure-core pinecone python-dotenv")

# Embedding-Deployment aus .env
EMBED_API_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
EMBED_API_BASE = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT").rstrip("/")
EMBED_DEPLOY = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
EMBED_API_VERSION = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-12-01-preview")

# Pinecone Konfiguration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "aparts-index")
PINECONE_ENV = os.getenv("PINECONE_ENV")

if not (PINECONE_API_KEY and PINECONE_ENV and EMBED_API_KEY and EMBED_API_BASE and EMBED_DEPLOY):
    raise SystemExit("Setze PINECONE_* und AZURE_OPENAI_EMBEDDING_* Variablen in .env")


# Azure OpenAI Client (neue API)
client = AzureOpenAI(
    api_version=EMBED_API_VERSION,
    azure_endpoint=EMBED_API_BASE,
    api_key=EMBED_API_KEY
) 

# Pinecone Setup
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Deine Knowledge Base-Dokumente
docs = [
    {
        "title": "hotel.info",
        "text": "Aparts Oberhausen – Ferienwohnungen und Messeapartments, ideal für Gäste, die Komfort, zentrale Lage und barrierefreie Apartments suchen. Adresse: Neumühler Str. 9, 46149 Oberhausen."
    },
    {
        "title": "contact",
        "text": "Telefon: +49 208 77807218; Mobil: +49 176 31737442; E-Mail: info@aparts-ob.de; Inhaber: Frank Backofen; Managerin: Bianca."
    },
    {
        "title": "arrival",
        "text": "Anfahrt: 50 m vom Bahnhof Oberhausen Sterkrade. Ca. 5 Minuten zum Centro, Theatro, ARENA. Kostenloser Parkplatz auf den ausgewiesenen Flächen hinter dem Ferienhaus."
    },
    {
        "title": "rooms.overview",
        "text": "5 Apartments (3–6 Personen). Alle Apartments mit kompletter Küche, barrierefreiem Bad, großzügigem Wohn‑Schlafraum, King‑Size‑Boxspringbetten, WLAN/LAN, Smart TV, Bettwäsche & Handtücher, Hotel‑Hausschuhe."
    },
    {
        "title": "apartment.1_2",
        "text": "Apt 1 & 2: Erdgeschoss, barrierefrei, 40–50 m², Max. 2 Pers. + 1 Beistellbett, Apt2 mit Terrasse, rollstuhlgerechte Ausstattung, eigener Parkplatz."
    },
    {
        "title": "apartment.3_4",
        "text": "Apt 3 & 4: 1. Etage, ca. 48–52 m², Max. 2 Pers. + 1 Beistellbett, Apt3 extragroße Küche, flexibler Express-Check-In."
    },
    {
        "title": "apartment.5",
        "text": "Apt 5 (LuxusLoft): 95 m², bis 6 Pers. + 2 Beistellbetten, 3 Schlafzimmer, 4 Smart TVs, TOP Wannen- und Duschbad."
    },
    {
        "title": "services",
        "text": "Service: Airport-Transfer (DUS/DTM), Transfer zur Messe, Room Service inkl. Wäschetausch."
    },
    {
        "title": "house_rules",
        "text": "Hausordnung: Ruhezeiten 23:00–7:00, Rauchen innen verboten, Haustiere 1 Hund pro Apartment erlaubt (Reinigungsvormerkung bei Nässe), Schäden melden."
    },
    {
        "title": "checkin_checkout",
        "text": "Check-in ab 15:00 Uhr, Check-out bis 10:30 Uhr. Zugang per Code-Tastatur; Safe mit Schlüsselcodes."
    },
    {
        "title": "wifi_tv",
        "text": "WLAN & LAN in allen Apartments; Smart-TV mit Streaming (Netflix, AmazonPrime). Zugangscode wird vor Anreise per E-Mail mitgeteilt."
    },
    {
        "title": "prices_payment",
        "text": "Startpreise ab 70 € pro Nacht; Bezahlung online oder vor Ort per Karte; Barzahlung nur nach Absprache."
    },
    {
        "title": "cleaning_fees",
        "text": "Reinigungsgebühren bei Mehraufwand: Apt1–4: 54 €; Apt5: 89 €."
    },
    {
        "title": "speech_rules",
        "text": (
            "Aussprache: Namen ausformulieren; Hausnummern in Worten; Postleitzahlen Ziffer-für-Ziffer; Maße und Einheiten ausformulieren; "
            "Telefonnummern Ziffer-für-Ziffer; E-Mails buchstabenweise (at, Punkt); Uhrzeiten in Worten; Geldbeträge in Worten; Daten in deutscher Form."
        )
    },
    {
        "title": "booking_flow",
        "text": "Buchungsreihenfolge: 1) vollständiger Name, 2) Wohnadresse, 3) Handynummer inkl. Vorwahl, 4) E-Mail für Bestätigung, 5) Zahlungswunsch (Karte/bar). Verwende Anrufernummer, wenn vorhanden."
    },
    {
        "title": "fallback",
        "text": "Fallback/Eskalation: 'Entschuldigung, da bin ich mir nicht sicher. Ich verbinde Sie nun mit einem unserer Mitarbeiter.'"
    }
]


upsert_items = []
for doc in docs:
    try:
        response = client.embeddings.create(
            input=[doc["text"]],
            model=EMBED_DEPLOY
        )
    except Exception as e:
        print("Fehler beim Abrufen der Embeddings!")
        print(f"Deployment: {EMBED_DEPLOY}")
        print(f"Endpoint: {EMBED_API_BASE}")
        print(f"API-Version: {EMBED_API_VERSION}")
        print(f"API-Key gesetzt: {'JA' if EMBED_API_KEY else 'NEIN'}")
        print(f"Fehler: {e}")
        print("\nPrüfe im Azure-Portal, ob der Deployment-Name exakt stimmt und das Modell bereitgestellt ist.")
        print("Der Endpoint muss die Basis-URL der Resource sein (ohne /openai/deployments/...)")
        print("API-Key muss zur Embedding-Resource gehören!")
        exit(1)
    vector = response.data[0].embedding
    upsert_items.append({
        "id": str(uuid.uuid4()),
        "values": vector,
        "metadata": {"title": doc["title"], "text": doc["text"]}
    })

print(f"Upserting {len(upsert_items)} Dokumente in Pinecone-Index '{PINECONE_INDEX}'...")
index.upsert(vectors=upsert_items)
print("Fertig.")