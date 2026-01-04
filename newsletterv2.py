# newslettergen.py
# FINAL – Streamlit Cloud compatible – OpenAI SDK >= 1.x
# Brand: Raus aus dem Gift

import os
import json
from datetime import datetime

import streamlit as st
import httpx

# OpenAI SDK
from openai import OpenAI
from openai import APIError, RateLimitError, AuthenticationError, BadRequestError


# ──────────────────────────────────────────────────────────────────────────────
# App Config
# ──────────────────────────────────────────────────────────────────────────────
APP_TITLE = "Newsletter Generator – Raus aus dem Gift"
BRAND = "Raus aus dem Gift"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💜",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# Styling (modern, calm, purple)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
:root{
  --bg1:#f7f2fb;
  --bg2:#eadcf7;
  --card:#ffffff;
  --primary:#8e44ad;
  --muted:#6b5b73;
  --shadow:0 8px 30px rgba(31,26,36,0.08);
  --radius:18px;
}

.main{background:linear-gradient(135deg,var(--bg1),var(--bg2));}
h1,h2,h3{color:var(--primary);}
.card{
  background:var(--card);
  border-radius:var(--radius);
  padding:1.2rem;
  box-shadow:var(--shadow);
  margin-bottom:1rem;
}
.small-muted{color:var(--muted);font-size:0.95rem;}

.stButton>button{
  background:linear-gradient(135deg,#9b59b6,#8e44ad)!important;
  color:white!important;
  border-radius:999px!important;
  font-weight:700!important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def get_client() -> OpenAI:
    """
    Create OpenAI client WITHOUT proxy interference.
    This avoids the 'proxies' crash on Streamlit / Windows.
    """
    api_key = get_api_key()
    if not api_key:
        raise AuthenticationError("OPENAI_API_KEY fehlt.")

    http_client = httpx.Client(
        proxies=None,
        timeout=60.0,
    )

    return OpenAI(
        api_key=api_key,
        http_client=http_client,
    )


def friendly_error(e: Exception) -> str:
    if isinstance(e, AuthenticationError):
        return "❌ API-Key fehlt oder ist ungültig."
    if isinstance(e, RateLimitError):
        return "⏳ Rate-Limit erreicht. Bitte später erneut versuchen."
    if isinstance(e, BadRequestError):
        return "⚠️ Ungültige Anfrage (Modell oder Parameter prüfen)."
    if isinstance(e, APIError):
        return "🚨 OpenAI API-Fehler."
    return f"Unerwarteter Fehler: {e}"


def call_llm(client: OpenAI, model: str, system: str, user: str, temperature: float) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# ──────────────────────────────────────────────────────────────────────────────
# UI – Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("# 💜 Newsletter Generator")
st.markdown("### *Raus aus dem Gift*")
st.markdown(
    "<div class='small-muted'>Traumasensible Newsletter für Heilung, Klarheit & Selbstwirksamkeit.</div>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Setup")

    if get_api_key():
        st.success("✅ API-Key gefunden")
    else:
        st.error("❌ Kein API-Key gefunden")
        st.stop()

    model = st.selectbox(
        "Modell",
        ["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="Empfohlen: gpt-4o-mini (stabil & günstig)",
    )
    temperature = st.slider("Kreativität", 0.0, 1.2, 0.7, 0.1)
    word_count = st.slider("Wortanzahl (ca.)", 250, 700, 450, 25)

# ──────────────────────────────────────────────────────────────────────────────
# Inputs
# ──────────────────────────────────────────────────────────────────────────────
newsletter_typ = st.selectbox(
    "📧 Newsletter-Typ",
    ["Community Newsletter", "Marketing Newsletter"],
)

thema = st.selectbox(
    "🎯 Thema",
    [
        "Narzisstischer Missbrauch",
        "Heilung & Recovery",
        "Grenzen setzen",
        "No Contact",
        "Selbstwert stärken",
        "Gaslighting erkennen",
    ],
)

zielgruppe = st.selectbox(
    "👥 Zielgruppe",
    [
        "Frauen in Trennung",
        "Frauen im Heilungsprozess",
        "Langzeit-Überlebende",
        "Angehörige",
    ],
)

cta = st.selectbox(
    "🎯 Call-to-Action",
    [
        "Community beitreten",
        "Kostenfreies Erstgespräch",
        "Online-Kurs",
        "E-Book Download",
    ],
)

zusatz = st.text_area(
    "📝 Zusätzliche Hinweise (optional)",
    height=120,
)

# ──────────────────────────────────────────────────────────────────────────────
# Generate
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")

if st.button("✨ Newsletter generieren", use_container_width=True):
    with st.spinner("💜 Newsletter wird erstellt …"):
        try:
            client = get_client()

            prompt = f"""
Du bist eine einfühlsame Content-Expertin für die Marke "{BRAND}".

Schreibe einen {newsletter_typ} auf Deutsch.
Thema: {thema}
Zielgruppe: {zielgruppe}
CTA: {cta}

Regeln:
- ca. {word_count} Wörter
- traumasensibel
- keine Diagnosen
- validierend, stärkend, klar
- 3–5 konkrete Impulse
- klarer, sanfter CTA am Ende

Zusatzinfos:
{zusatz if zusatz.strip() else "Keine"}

Gib nur den Newsletter-Text zurück.
"""

            text = call_llm(
                client=client,
                model=model,
                system="Du schreibst traumasensible Newsletter für Überlebende narzisstischen Missbrauchs.",
                user=prompt,
                temperature=temperature,
            )

            st.session_state.result = {
                "content": text,
                "generated_at": datetime.now().isoformat(),
            }

            st.success("✅ Fertig!")

        except Exception as e:
            st.error(friendly_error(e))

# ──────────────────────────────────────────────────────────────────────────────
# Output
# ──────────────────────────────────────────────────────────────────────────────
if "result" in st.session_state:
    st.markdown("## 📬 Ergebnis")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(st.session_state.result["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "💾 Als Text speichern",
        data=st.session_state.result["content"],
        file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
    )
