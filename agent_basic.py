"""
BASIC Voice Assistant - LiveKit Agent (Variant 1)
- Simple Q&A agent with Azure OpenAI + Pinecone Knowledge Base
- No call forwarding, no SMS, no WhatsApp
- DSGVO-compliant: Azure Speech (STT/TTS), Azure OpenAI, Silero VAD
- Pinecone for company knowledge base
- German language support
- Use case: Basic customer service queries only
"""

import os
import re
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import asyncio
import base64  # ggf. für spätere REST-Fallbacks

from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext, JobContext
from livekit.agents.llm import function_tool
from livekit.agents.worker import WorkerOptions
from livekit.plugins import azure, openai, silero
# Deepgram optional nutzbar (du nutzt primär DSGVO/Azure-Pipeline)
try:
    from livekit.plugins import deepgram  # noqa: F401
    HAS_DEEPGRAM = True
except Exception:
    HAS_DEEPGRAM = False

# SIP Outdial via SDK
from livekit.api import LiveKitAPI

# ---- Logging ----
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("dsgvo-telephony-agent")

# --------------------------------------------------------------------------------------
# Konfiguration / ENV
# --------------------------------------------------------------------------------------
SIP_TRUNK_NAME = os.getenv("LIVEKIT_SIP_TRUNK", "agents")
DEFAULT_FORWARD_NUMBER = os.getenv("DEFAULT_FORWARD_NUMBER")  # +49... oder sip:...
RING_TIMEOUT_SECONDS = 25  # gefordert

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # whatsapp:+14155238886
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO")      # whatsapp:+49...

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _azure_base(url: str) -> str:
    """Nimmt eine evtl. lange Azure-URL (mit /openai/deployments/...) und gibt die Basis-URL zurück."""
    if not url:
        return url
    # erwartetes Muster: https://<name>.openai.azure.com/...
    m = re.match(r"^(https://[^/]+\.openai\.azure\.com)", url.strip())
    return m.group(1) if m else url.strip().rstrip("/")

def _get_azure_llm_config() -> Dict[str, str]:
    """Liest LLM-Konfiguration aus ENV und normalisiert Endpoint."""
    return {
        "model": os.getenv("LLM_CHOICE", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")),
        "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
        "azure_endpoint": _azure_base(os.getenv("AZURE_OPENAI_ENDPOINT", "")),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
    }

def _get_azure_stt_tts_config() -> Dict[str, str]:
    return {
        "speech_key": os.getenv("AZURE_SPEECH_KEY", ""),
        "speech_region": os.getenv("AZURE_SPEECH_REGION", "germanywestcentral"),
    }

def _get_azure_embed_config() -> Dict[str, str]:
    """Embeddings: nutzt eigene Embedding-ENV, fällt auf LLM-ENV zurück; normalisiert Endpoint."""
    return {
        "api_key": os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY", ""),
        "endpoint": _azure_base(os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT", "")),
        "api_version": os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        "deployment": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    }

def _pinecone_connect():
    """Verbindet zu Pinecone; unterstützt v3 und (fallback) ältere Clients."""
    api_key = os.getenv("PINECONE_API_KEY")
    env = os.getenv("PINECONE_ENV")
    index_name = os.getenv("PINECONE_INDEX")
    if not (api_key and env and index_name):
        raise RuntimeError("Pinecone nicht konfiguriert (PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX).")

    try:
        # v3 client
        from pinecone import Pinecone  # type: ignore
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        return index
    except Exception:
        # v2 fallback
        import pinecone  # type: ignore
        pinecone.init(api_key=api_key, environment=env)
        index = pinecone.Index(index_name)
        return index

async def _azure_embed(texts: List[str]) -> List[List[float]]:
    """Holt Embeddings über AzureOpenAI; erwartet, dass Deployment existiert."""
    from openai import AzureOpenAI  # OpenAI SDK >=1.43
    cfg = _get_azure_embed_config()
    if not (cfg["api_key"] and cfg["endpoint"] and cfg["deployment"]):
        raise RuntimeError("Azure Embeddings nicht konfiguriert (API-Key/Endpoint/Deployment).")

    client = AzureOpenAI(
        api_key=cfg["api_key"],
        api_version=cfg["api_version"],
        azure_endpoint=cfg["endpoint"],
    )
    # Azure erwartet bei .create model=<DEPLOYMENTNAME>
    r = client.embeddings.create(model=cfg["deployment"], input=texts)
    return [d.embedding for d in r.data]

def _lang_default() -> str:
    """Standardsprache Telefonie."""
    return "de-DE"

def _valid_target(target: str) -> bool:
    """E.164 (+49...) oder einfache SIP-URI zulassen."""
    return bool(
        re.match(r"^\+\d{6,15}$", target)
        or re.match(r"^sip:[^@\s]+@[^@\s]+\.[^@\s]+$", target)
    )

async def _wait_for_new_remote_participant(session, start_count: int, timeout_s: int) -> bool:
    """Wartet bis ein neuer Remote-Teilnehmer im Room auftaucht (einfaches Polling)."""
    try:
        for _ in range(timeout_s):
            if len(session.room.remote_participants) > start_count:
                return True
            await asyncio.sleep(1)
    except Exception:
        pass
    return False

async def _send_whatsapp(body: str, to_override: Optional[str] = None) -> str:
    """Whatsapp per Twilio senden (nur bei Nichterreichbarkeit)."""
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM):
        return "WhatsApp nicht konfiguriert (Twilio ENV fehlt)."
    to = to_override or TWILIO_WHATSAPP_TO
    if not to:
        return "WhatsApp-Zielnummer fehlt."
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    data = {"From": TWILIO_WHATSAPP_FROM, "To": to, "Body": body}
    async with httpx.AsyncClient(timeout=20.0, auth=auth) as client:
        r = await client.post(url, data=data)
        if r.status_code not in (200, 201):
            return f"WhatsApp-Fehler {r.status_code}: {r.text}"
    return "WhatsApp gesendet."

# --------------------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------------------

class TelephonyAssistant(Agent):
    """
    DSGVO-konformer Voice Assistant (deutsch als Standard, mehrsprachig möglich).
    Beinhaltet Tools + Warm-Transfer-Flow (SDK) inkl. WhatsApp-Fallback.
    """

    def __init__(self):
        # Immer „Clara“ für die Außenwirkung – unabhängig von Worker-/SIP-/Agentnamen
        agent_display_name = "Clara"

        prompt_path = "prompt.txt"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_instructions = f.read()
            # Leitplanken hinzufügen, falls Prompt das nicht schon tut:
            base_instructions += (
                "\n\nWICHTIG:\n"
                "- Stelle dich IMMER als Clara vor.\n"
                "- Wenn jemand nach deinem Namen fragt, antworte: „Ich heiße Clara.“\n"
                "- Nenne niemals interne System-/Agentennamen oder Worker-Bezeichnungen.\n"
                "- Wenn der Anrufer eine Weiterleitung wünscht ODER du das Anliegen nach zwei kurzen Versuchen nicht lösen kannst, "
                "rufe das Tool request_human_transfer auf."
            )
        else:
            base_instructions = (
                "Du bist ein hilfreicher deutscher Assistent namens Clara. "
                "Sprich standardmäßig Deutsch in klaren, kurzen Sätzen für Telefongespräche. "
                "Wenn die Anruferin klar eine andere Sprache nutzt, kannst du in diese wechseln. "
                "Gib niemals System- oder Zugangsdaten preis. "
                "WICHTIG: Stelle dich IMMER als Clara vor. Wenn jemand nach deinem Namen fragt, "
                "antworte exakt: „Ich heiße Clara.“ Nenne niemals interne System-/Agentennamen. "
                "Wenn der Anrufer eine Weiterleitung wünscht ODER du das Anliegen nach zwei kurzen Versuchen nicht lösen kannst, "
                "rufe das Tool request_human_transfer auf."
            )

        super().__init__(instructions=base_instructions)

    # ---- Tools ----

    @function_tool
    async def get_current_time(self, context: RunContext, tz: str = "Europe/Berlin") -> str:
        """Gibt die aktuelle Zeit in ISO (inkl. TZ) zurück (Deutsch)."""
        try:
            now = datetime.now(ZoneInfo(tz))
        except Exception:
            now = datetime.utcnow()
        return now.isoformat()

    @function_tool
    async def query_kb(self, context: RunContext, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fragt Pinecone mit Azure-Embeddings ab."""
        try:
            vectors = await _azure_embed([query])
            vec = vectors[0]
            index = _pinecone_connect()
            res = index.query(vector=vec, top_k=top_k, include_metadata=True)
            matches = res.get("matches") if isinstance(res, dict) else getattr(res, "matches", [])
            hits: List[Dict[str, Any]] = []
            for m in matches or []:
                meta = m.get("metadata", {}) if isinstance(m, dict) else getattr(m, "metadata", {}) or {}
                text = meta.get("text", "")
                score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
                hits.append({"score": score, "text": text, "metadata": meta})
            return hits
        except Exception as e:
            return [{"error": f"KB-Fehler: {e}"}]

    def _caller_phone_from_session(self) -> Optional[str]:
        try:
            meta_raw = self.session.room.local_participant.metadata
            meta = meta_raw if isinstance(meta_raw, dict) else json.loads(meta_raw or "{}")
            return meta.get("caller_phone") or meta.get("from") or meta.get("caller")
        except Exception:
            return None

    @function_tool
    async def send_to_webhook(self, context: RunContext, payload: dict) -> str:
        """Sende strukturierte Payload an externen Webhook (URL via .env N8N_WEBHOOK_URL)."""
        url = os.getenv("N8N_WEBHOOK_URL")
        if not url:
            return "Webhook nicht konfiguriert (N8N_WEBHOOK_URL fehlt)."
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=payload)
                return r.text if r.status_code == 200 else f"Fehler: Status {r.status_code}"
        except Exception as e:
            return f"Webhook-Fehler: {e}"
        
    @function_tool
    async def book_appointment(self, context: RunContext, customer_name: str, datetime_iso: str, phone: Optional[str], service: str) -> str:
        """Bucht Termin via send_to_webhook; nutzt Caller aus Session, wenn phone None."""
        if not phone:
            phone = self._caller_phone_from_session() or "unbekannt"
        payload = {"action": "book_appointment", "customer_name": customer_name, "datetime": datetime_iso, "phone": phone, "service": service}
        return await self.send_to_webhook(context, payload)

    @function_tool
    async def parse_relative_time_to_iso(self, context: RunContext, text: str, tz: str = "Europe/Berlin") -> str:
        """Einfacher Parser: 'morgen um 14 Uhr' -> ISO."""
        now = datetime.now(ZoneInfo(tz))
        txt = text.lower()
        try:
            if "morgen" in txt:
                m = re.search(r"(\d{1,2})(?:[:\.](\d{2}))?", txt)
                if m:
                    h = int(m.group(1)); minute = int(m.group(2) or 0)
                    target = (now + timedelta(days=1)).replace(hour=h, minute=minute, second=0, microsecond=0)
                    return target.isoformat()
        except Exception:
            return ""
        return ""

    # ===================== NEU: Warm-Transfer (SDK) + Timeout + WhatsApp =====================

    async def _sdk_add_sip_participant(self, room_name: str, destination: str, trunk_name: str) -> None:
        """LiveKit SDK: Outdial -> Ziel als SIP-Teilnehmer in diesen Room holen."""
        async with LiveKitAPI() as lk:
            sip_obj = getattr(lk, "sip", None)
            if sip_obj is None:
                raise AttributeError("LiveKitAPI.sip nicht verfügbar")
            create_fn = getattr(sip_obj, "create_sip_participant", None)
            if create_fn is None:
                raise AttributeError("create_sip_participant nicht verfügbar")
            await create_fn({
                "room_name": room_name,
                "trunk": trunk_name,
                "destination": destination,
            })

    async def _warm_transfer_with_timeout(self, destination: str, timeout_s: int) -> bool:
        """True, wenn Zielteilnehmer beitritt; False bei Timeout / nicht erreicht."""
        room_name = self.session.room.name
        start_count = len(self.session.room.remote_participants)
        await self._sdk_add_sip_participant(room_name, destination, SIP_TRUNK_NAME)
        return await _wait_for_new_remote_participant(self.session, start_count, timeout_s)

    # @function_tool  # DISABLED IN BASIC VARIANT - No call forwarding
    async def request_human_transfer(self, context: RunContext, reason: str = "") -> str:
        """
        DISABLED IN BASIC AGENT - No call forwarding in this variant.
        Use agent_forward_sms.py or agent_forward_whatsapp.py for forwarding features.
        """
        dest = DEFAULT_FORWARD_NUMBER
        if not dest or not _valid_target(dest):
            return "Weiterleitung nicht möglich (Zielnummer ungültig oder fehlt)."

        await self.session.generate_reply(instructions="Einen Moment bitte, ich stelle Sie jetzt mit einem Kollegen durch.")
        try:
            joined = await self._warm_transfer_with_timeout(dest, RING_TIMEOUT_SECONDS)
        except Exception as e:
            await self.session.generate_reply(
                instructions="Die Durchstellung ist leider fehlgeschlagen. Soll ich eine Nachricht aufnehmen?"
            )
            return f"Weiterleitung fehlgeschlagen: {e}"

        if joined:
            await self.session.generate_reply(instructions="Vielen Dank. Ich übergebe jetzt das Gespräch.")
            # Optional: nach Übergabe Raum verlassen
            # await self.session.leave()
            return "Weiterleitung erfolgreich: Ziel ist im Gespräch."
        else:
            caller = self._caller_phone_from_session() or "unbekannt"
            msg = f"Clara: Ziel nicht erreicht innerhalb {RING_TIMEOUT_SECONDS}s. Bitte Rückruf an {caller} veranlassen."
            _ = await _send_whatsapp(msg)
            await self.session.generate_reply(
                instructions="Es geht leider niemand ran. Ich habe das Team informiert; Sie werden gleich zurückgerufen."
            )
            return "Weiterleitung: Timeout -> WhatsApp gesendet, Anrufer informiert."

    # ---- Lifecycle ----

    async def on_enter(self):
        """Begrüßung auf Deutsch, kurz & freundlich – IMMER als „Clara".""" 
        greeting = (
            "Guten Tag und herzlich willkommen beim Aparts in Oberhausen. "
            "Sie sprechen mit Clara, Ihrer virtuellen Assistentin. Wie kann ich Ihnen helfen?"
        )
        try:
            await self.session.generate_reply(instructions=greeting)
        except Exception as e:
            log.warning(f"Greeter konnte nicht sprechen: {e}")

# --------------------------------------------------------------------------------------
# Entrypoint (Telefonie first, keine Raum-Autocreation; nutzt ctx.room vom SIP-Ingress)
# --------------------------------------------------------------------------------------

async def entrypoint(ctx: JobContext):
    """
    Haupt-Einstiegspunkt:
    - Verbindet den Worker
    - Wartet auf eingehenden Teilnehmer (SIP)
    - Startet die Session im vom Ingress erzeugten Raum (ctx.room)
    """
    await ctx.connect()

    # SIP: auf Teilnehmer warten
    participant = await ctx.wait_for_participant()
    log.info(f"Phone call connected from participant: {participant.identity}")

    # Audio-/LLM-Pipeline (Azure STT für DSGVO-Compliance)
    speech_cfg = _get_azure_stt_tts_config()
    llm_cfg = _get_azure_llm_config()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=azure.STT(
            speech_key=speech_cfg["speech_key"],
            speech_region=speech_cfg["speech_region"],
            language="de-DE",
        ),
        llm=openai.LLM.with_azure(
            model=llm_cfg["model"],
            azure_deployment=llm_cfg["azure_deployment"],
            azure_endpoint=llm_cfg["azure_endpoint"],
            api_version=llm_cfg["api_version"],
            api_key=llm_cfg["api_key"],
        ),
        tts=azure.TTS(
            speech_key=speech_cfg["speech_key"],
            speech_region=speech_cfg["speech_region"],
            voice="de-DE-KatjaNeural",
        ),
        turn_detection="semantic",
    )

    # Start im aktuellen Raum (kein Auto-Create; SIP-Routing bestimmt den Raum)
    await session.start(agent=TelephonyAssistant(), room=ctx.room)

# --------------------------------------------------------------------------------------
# CLI / Worker starten – Dispatch: INDIVIDUAL
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    worker_name = ""  # bleibt leer, wie von dir gewünscht
    # HINWEIS: agent_name bleibt leer, damit deine bestehende Dispatch-Rule greifen kann

    opts = WorkerOptions(entrypoint_fnc=entrypoint)
    opts.ws_url = os.getenv("LIVEKIT_URL", opts.ws_url)
    opts.api_key = os.getenv("LIVEKIT_API_KEY", opts.api_key)
    opts.api_secret = os.getenv("LIVEKIT_API_SECRET", opts.api_secret)
    opts.agent_name = worker_name

    log.info(f"🚀 Starte LiveKit Voice Agent Worker (agent_name='{opts.agent_name}') …")
    agents.cli.run_app(opts)

# ...ganz am Ende der Datei, nach allen Klassendefinitionen...
TelephonyAssistant.send_to_webhook.__openai_schema__ = {
    "name": "send_to_webhook",
    "description": "Sende strukturierte Payload an externen Webhook (URL via .env N8N_WEBHOOK_URL).",
    "parameters": {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "additionalProperties": False
            }
        },
        "required": ["payload"],
        "additionalProperties": False
    }
}
