import os
import json
from datetime import datetime

import streamlit as st

# OpenAI Python SDK (openai>=1.0.0)
try:
    from openai import OpenAI
    from openai import APIError, RateLimitError, AuthenticationError, BadRequestError
except Exception:  # pragma: no cover
    # Fallback: allows app to start and show a clear error in UI
    OpenAI = None
    APIError = RateLimitError = AuthenticationError = BadRequestError = Exception

# Optional: load .env locally (Streamlit Cloud uses Secrets; Netcup/Server uses ENV)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


# ──────────────────────────────────────────────────────────────────────────────
# App Config
# ──────────────────────────────────────────────────────────────────────────────
APP_TITLE = "Newsletter Generator - Raus aus dem Gift"
BRAND = "Raus aus dem Gift"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💜",
    layout="wide",
)

# Modern, calm UI (purple theme) – pure CSS only (works on Streamlit Cloud)
st.markdown(
    """
<style>
:root{
  --bg1:#f7f2fb;
  --bg2:#eadcf7;
  --card:#ffffff;
  --text:#1f1a24;
  --muted:#6b5b73;
  --primary:#8e44ad;
  --primary2:#9b59b6;
  --good:#1e7e34;
  --warn:#b7791f;
  --bad:#c53030;
  --shadow: 0 8px 30px rgba(31, 26, 36, 0.08);
  --radius: 18px;
}

.main{
  background: linear-gradient(135deg, var(--bg1) 0%, var(--bg2) 100%);
}

.block-container{
  padding-top: 2rem;
  padding-bottom: 2rem;
}

h1, h2, h3{
  color: var(--primary);
  font-family: ui-serif, Georgia, "Times New Roman", serif;
}

.small-muted{
  color: var(--muted);
  font-size: 0.95rem;
}

.card{
  background: var(--card);
  border-radius: var(--radius);
  padding: 1.1rem 1.1rem;
  box-shadow: var(--shadow);
  border: 1px solid rgba(142, 68, 173, 0.10);
}

.card + .card{ margin-top: 1rem; }

.pill{
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: rgba(142, 68, 173, 0.10);
  color: var(--primary);
  font-weight: 600;
  font-size: 0.85rem;
}

.stButton>button{
  background: linear-gradient(135deg, var(--primary2) 0%, var(--primary) 100%) !important;
  color: white !important;
  border-radius: 999px !important;
  padding: 0.9rem 1.25rem !important;
  font-weight: 700 !important;
  border: none !important;
  box-shadow: 0 10px 25px rgba(142, 68, 173, 0.22) !important;
  transition: transform 120ms ease, box-shadow 120ms ease !important;
}

.stButton>button:hover{
  transform: translateY(-1px);
  box-shadow: 0 14px 30px rgba(142, 68, 173, 0.28) !important;
}

hr{
  border: none;
  height: 1px;
  background: rgba(142, 68, 173, 0.15);
  margin: 1.25rem 0;
}

code, pre{
  border-radius: 12px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    """
    Robust API-key lookup:
    1) ENV (OPENAI_API_KEY) – best for servers
    2) Streamlit Secrets (OPENAI_API_KEY) – best for Streamlit Cloud
    """
    env_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if env_key:
        return env_key

    # st.secrets may raise StreamlitSecretNotFoundError if no secrets exist
    try:
        secret_key = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()  # type: ignore[attr-defined]
        return secret_key
    except Exception:
        return ""


def get_client():
    """
    Robust OpenAI client initialization
    - ignores system proxy env vars
    - compatible with openai>=1.0.0
    """
    if OpenAI is None:
        raise RuntimeError(
            "OpenAI SDK nicht verfügbar. Bitte installiere openai>=1.0.0"
        )

    api_key = get_api_key()
    if not api_key:
        raise AuthenticationError("Kein OPENAI_API_KEY gefunden.")

    http_client = httpx.Client(proxies=None, timeout=60.0)

    return OpenAI(
        api_key=api_key,
        http_client=http_client,
    )



def friendly_error(e: Exception) -> str:
    # Keep it user-friendly and actionable
    if isinstance(e, AuthenticationError):
        return "Auth-Fehler: API-Key ungültig/fehlt oder keine Berechtigung für das Modell."
    if isinstance(e, RateLimitError):
        return "Rate-Limit erreicht. Bitte kurz warten und erneut versuchen."
    if isinstance(e, BadRequestError):
        return "Ungültige Anfrage (Bad Request). Prüfe Parameter/Modell."
    if isinstance(e, APIError):
        return "OpenAI API-Fehler. Bitte später erneut versuchen."
    return f"Unerwarteter Fehler: {e}"


def build_newsletter_prompt(
    newsletter_typ: str,
    haupt_thema: str,
    spezifisches_thema: str,
    zielgruppe: str,
    ton: str,
    cta_fokus: str,
    zusatz_info: str,
    word_min: int,
    word_max: int,
) -> str:
    return f"""
Du bist eine einfühlsame Content-Spezialistin für die Brand "{BRAND}", die Überlebende narzisstischen Missbrauchs unterstützt.
Schreibe einen {newsletter_typ} auf Deutsch, traumasensibel, klar, nicht triggernd, aber ehrlich.

Parameter:
- Hauptthema: {haupt_thema}
- Spezifisches Thema: {spezifisches_thema}
- Zielgruppe: {zielgruppe}
- Tonalität: {ton}
- CTA Fokus: {cta_fokus}
- Zusätzliche Infos: {zusatz_info if zusatz_info.strip() else "Keine"}

Anforderungen:
- ca. {word_min}–{word_max} Wörter (ungefähr)
- Keine Diagnosen, keine Schuldzuweisungen, kein Victim-Blaming
- Validierung + Hoffnung + konkrete, umsetzbare Schritte
- Struktur:
  1) Persönliche Ansprache
  2) Einleitung (Situation benennen)
  3) Hauptteil (Wissen/Erkenntnisse + 3–5 konkrete Mini-Schritte)
  4) Ermutigung (kurz, warm, stärkend)
  5) Klarer Call-to-Action passend zum Fokus

Gib nur den Newsletter-Text zurück (ohne Meta-Erklärungen).
""".strip()


def build_header_prompt(haupt_thema: str, spezifisches_thema: str, newsletter_typ: str, zielgruppe: str) -> str:
    return f"""
Erstelle 5 Header-Varianten + passende Pre-Header für einen Newsletter.

Kontext:
- Thema: {haupt_thema} – {spezifisches_thema}
- Typ: {newsletter_typ}
- Zielgruppe: {zielgruppe}
- Brand: {BRAND}

Regeln:
- Header max. 60 Zeichen
- Pre-Header max. 90 Zeichen
- Emotional, neugierig, hoffnungsvoll – ohne Trigger & ohne Manipulation
- Keine reißerischen Drohungen

Format exakt:
1) Header: ...
   Pre-Header: ...
2) Header: ...
   Pre-Header: ...
...
5) Header: ...
   Pre-Header: ...
""".strip()


def call_llm(client, model: str, system: str, user: str, temperature: float) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


# ──────────────────────────────────────────────────────────────────────────────
# UI – Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("# 💜 Newsletter Generator")
st.markdown("### *Raus aus dem Gift* – Deine Stimme für Heilung und Empowerment")
st.markdown("<div class='small-muted'>Erstelle traumasensible Newsletter mit klarer Struktur, Headern & Export.</div>", unsafe_allow_html=True)
st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Setup")
    api_key = get_api_key()
    api_ok = bool(api_key)

    if api_ok:
        st.success("✅ API-Key gefunden (ENV/Secrets)")
    else:
        st.error("❌ Kein API-Key gefunden")
        st.info(
            """
**So setzt du den API-Key:**
- **Lokal/Server:** ENV Variable `OPENAI_API_KEY`
- **Streamlit Cloud:** App Settings → **Secrets**
  ```toml
  OPENAI_API_KEY="dein-key"
  ```
            """.strip()
        )

    st.markdown("---")
    st.markdown("### 🧠 Modell & Qualität")
    model = st.selectbox(
        "OpenAI Modell",
        options=["gpt-4o", "gpt-4o-mini"],
        index=0,
        help="Wenn du Kosten/Speed priorisierst: gpt-4o-mini. Wenn Qualität wichtiger ist: gpt-4o.",
    )
    temperature = st.slider("Kreativität (Temperature)", 0.0, 1.2, 0.7, 0.1)
    word_min, word_max = st.slider("Ziel-Länge (Wörter)", 200, 900, (320, 520), 10)

    st.markdown("---")
    st.markdown("### 💡 Über")
    st.caption("Dieses Tool ist keine Diagnose und ersetzt keine professionelle Hilfe. Bei akuter Gefahr: 112.")


if not api_ok:
    st.warning("⚠️ Bitte zuerst den API-Key setzen (Sidebar).")
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# Main Inputs
# ──────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    newsletter_typ = st.selectbox(
        "📧 Newsletter-Typ",
        ["Community Newsletter", "Marketing Newsletter"],
        help="Community: Fokus auf Heilung & Unterstützung | Marketing: Fokus auf Angebote & Conversion",
    )

with col2:
    haupt_thema = st.selectbox(
        "🎯 Übergeordnetes Thema",
        [
            "Narzisstischen Missbrauch erkennen",
            "Heilung und Recovery",
            "No Contact / Grauer Fels",
            "Selbstwert aufbauen",
            "Trauma verstehen",
            "Toxische Beziehungsmuster",
            "Innere Kind-Arbeit",
            "Grenzen setzen lernen",
            "Gaslighting und Manipulation",
            "Neustart nach Missbrauch",
        ],
    )

unterthemen_map = {
    "Narzisstischen Missbrauch erkennen": [
        "Red Flags früh erkennen",
        "Unterschied zwischen Narzissmus und NPD",
        "Love Bombing Phase verstehen",
        "Typische Täterstrategien",
    ],
    "Heilung und Recovery": [
        "Erste Schritte nach dem Ausstieg",
        "Umgang mit Trauma-Triggern",
        "Selbstfürsorge-Rituale",
        "Professionelle Hilfe finden",
    ],
    "No Contact / Grauer Fels": [
        "No Contact durchhalten",
        "Grauer Fels bei Co-Parenting",
        "Rückfälle vermeiden",
        "Flying Monkeys abwehren",
    ],
    "Selbstwert aufbauen": [
        "Negative Glaubenssätze auflösen",
        "Selbstliebe praktizieren",
        "Eigene Bedürfnisse entdecken",
        "Selbstvertrauen stärken",
    ],
    "Trauma verstehen": [
        "Komplexe PTBS erkennen",
        "Körperliche Trauma-Reaktionen",
        "Trauma und Nervensystem",
        "Disassoziation verstehen",
    ],
    "Toxische Beziehungsmuster": [
        "Traumabonding durchbrechen",
        "Co-Abhängigkeit heilen",
        "Wiederholungsmuster erkennen",
        "Gesunde Beziehungen lernen",
    ],
    "Innere Kind-Arbeit": [
        "Das verletzte innere Kind",
        "Reparenting Techniken",
        "Emotionale Bedürfnisse erfüllen",
        "Heilung durch Selbstmitgefühl",
    ],
    "Grenzen setzen lernen": [
        "Nein sagen ohne Schuldgefühle",
        "Gesunde Grenzen kommunizieren",
        "Grenzverletzungen erkennen",
        "Konsequenzen durchsetzen",
    ],
    "Gaslighting und Manipulation": [
        "Gaslighting-Taktiken entlarven",
        "Realität vs. Manipulation",
        "Mentale Klarheit zurückgewinnen",
        "Dokumentation als Schutz",
    ],
    "Neustart nach Missbrauch": [
        "Identität wiederfinden",
        "Neue Lebensziele setzen",
        "Finanzieller Neuanfang",
        "Soziales Netzwerk aufbauen",
    ],
}

spezifisches_thema = st.selectbox("🔍 Spezifisches Thema", unterthemen_map.get(haupt_thema, ["Allgemein"]))

col3, col4 = st.columns(2)

with col3:
    zielgruppe = st.selectbox(
        "👥 Hauptzielgruppe",
        [
            "Frauen in akuter Missbrauchssituation",
            "Frauen kurz nach Trennung",
            "Frauen im Heilungsprozess",
            "Frauen die Rückfälle vermeiden wollen",
            "Angehörige und Unterstützer",
        ],
    )

with col4:
    ton = st.selectbox(
        "💬 Tonalität",
        [
            "Einfühlsam & unterstützend",
            "Empowernd & motivierend",
            "Aufklärend & informativ",
            "Ermutigend & hoffnungsvoll",
            "Validierend & verstehend",
        ],
    )

if newsletter_typ == "Marketing Newsletter":
    cta_fokus = st.selectbox(
        "🎯 Call-to-Action Fokus",
        [
            "Kostenfreies Erstgespräch buchen",
            "Online-Kurs anmelden",
            "Coaching-Programm",
            "Community beitreten",
            "E-Book Download",
            "Webinar Anmeldung",
        ],
    )
else:
    cta_fokus = "Community-Engagement"

zusatz_info = st.text_area(
    "📝 Zusätzliche Informationen (optional)",
    placeholder="z.B. spezielle Inhalte, aktuelle Ereignisse, persönliche Storys, Beispiele, konkrete Situationen…",
    height=110,
)


# ──────────────────────────────────────────────────────────────────────────────
# Generation
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")

gen_col1, gen_col2 = st.columns([2, 1])

with gen_col1:
    generate = st.button("✨ Newsletter generieren", use_container_width=True)

with gen_col2:
    also_headers = st.toggle("Auch Header & Pre-Header generieren", value=True)


if "last_output" not in st.session_state:
    st.session_state.last_output = None

if generate:
    with st.spinner("💜 Dein Newsletter wird erstellt…"):
        try:
            client = get_client(api_key)

            newsletter_prompt = build_newsletter_prompt(
                newsletter_typ=newsletter_typ,
                haupt_thema=haupt_thema,
                spezifisches_thema=spezifisches_thema,
                zielgruppe=zielgruppe,
                ton=ton,
                cta_fokus=cta_fokus,
                zusatz_info=zusatz_info,
                word_min=word_min,
                word_max=word_max,
            )

            newsletter_text = call_llm(
                client=client,
                model=model,
                system="Du bist eine einfühlsame Content-Spezialistin für Trauma-Heilung und Empowerment.",
                user=newsletter_prompt,
                temperature=temperature,
            )

            headers_text = ""
            if also_headers:
                headers_prompt = build_header_prompt(
                    haupt_thema=haupt_thema,
                    spezifisches_thema=spezifisches_thema,
                    newsletter_typ=newsletter_typ,
                    zielgruppe=zielgruppe,
                )
                headers_text = call_llm(
                    client=client,
                    model=model,
                    system="Du bist eine Expertin für E-Mail-Marketing im Bereich Trauma-sensibler Kommunikation.",
                    user=headers_prompt,
                    temperature=min(1.2, max(0.2, temperature + 0.1)),
                )

            st.session_state.last_output = {
                "typ": newsletter_typ,
                "haupt_thema": haupt_thema,
                "spezifisches_thema": spezifisches_thema,
                "zielgruppe": zielgruppe,
                "ton": ton,
                "cta_fokus": cta_fokus,
                "model": model,
                "temperature": temperature,
                "word_range": [word_min, word_max],
                "headers": headers_text,
                "content": newsletter_text,
                "generiert_am": datetime.now().isoformat(),
            }

            st.success("✅ Fertig!")

        except Exception as e:
            st.error(f"❌ {friendly_error(e)}")
            st.info("Tipp: Wenn du kein Zugriff auf das ausgewählte Modell hast, wähle gpt-4o-mini oder prüfe deinen Account/API-Key.")


# ──────────────────────────────────────────────────────────────────────────────
# Output / Export
# ──────────────────────────────────────────────────────────────────────────────
out = st.session_state.last_output

if out:
    st.markdown("## 📬 Ergebnis")

    if out.get("headers"):
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Header & Pre-Header Vorschläge")
        st.markdown(out["headers"])
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### ✍️ Newsletter-Inhalt")
    st.markdown(out["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    dl1, dl2 = st.columns(2)

    full_text = f"""HEADER & PRE-HEADER OPTIONEN:
{out.get("headers","")}

---

NEWSLETTER INHALT:
{out.get("content","")}

---
Generiert am: {datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")}
Konfiguration:
- Typ: {out.get("typ")}
- Hauptthema: {out.get("haupt_thema")}
- Spezifisches Thema: {out.get("spezifisches_thema")}
- Zielgruppe: {out.get("zielgruppe")}
- Tonalität: {out.get("ton")}
- CTA Fokus: {out.get("cta_fokus")}
- Modell: {out.get("model")}
- Temperature: {out.get("temperature")}
- Wörter: {out.get("word_range")}
""".strip()

    with dl1:
        st.download_button(
            "💾 Als Text-Datei speichern",
            data=full_text,
            file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with dl2:
        st.download_button(
            "📋 Als JSON speichern",
            data=json.dumps(out, indent=2, ensure_ascii=False),
            file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
<div style='text-align:center; color:#8e44ad; padding: 14px 0;'>
  <div class='pill'>💜 {brand}</div>
  <div style='margin-top: 10px; font-size: 0.95rem; color: rgba(31,26,36,0.75);'>
    Jeder Newsletter ist ein Schritt Richtung Klarheit, Heilung & Selbstwirksamkeit.
  </div>
</div>
""".format(brand=BRAND),
    unsafe_allow_html=True,
)
