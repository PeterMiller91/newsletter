# newslettergen.py
# FINAL – Streamlit Cloud compatible – OpenAI SDK >= 1.x
# Brand: Raus aus dem Gift

import os
import json
from datetime import datetime
from typing import List, Dict

import streamlit as st
import httpx
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
# Styling
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
:root{
  --bg1:#f7f2fb; --bg2:#eadcf7; --card:#ffffff;
  --primary:#8e44ad; --muted:#6b5b73;
  --shadow:0 8px 30px rgba(31,26,36,0.08);
  --radius:18px;
}
.main{background:linear-gradient(135deg,var(--bg1),var(--bg2));}
h1,h2,h3{color:var(--primary);}
.card{background:var(--card);border-radius:var(--radius);padding:1.2rem;box-shadow:var(--shadow);margin-bottom:1rem;}
.small-muted{color:var(--muted);font-size:0.95rem;}
.stButton>button{background:linear-gradient(135deg,#9b59b6,#8e44ad)!important;color:white!important;border-radius:999px!important;font-weight:700!important;}
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# OpenAI Helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def get_client() -> OpenAI:
    api_key = get_api_key()
    if not api_key:
        raise AuthenticationError("OPENAI_API_KEY fehlt.")

    http_client = httpx.Client(proxies=None, timeout=60.0)
    return OpenAI(api_key=api_key, http_client=http_client)


def friendly_error(e: Exception) -> str:
    if isinstance(e, AuthenticationError):
        return "❌ API-Key fehlt oder ist ungültig."
    if isinstance(e, RateLimitError):
        return "⏳ Rate-Limit erreicht."
    if isinstance(e, BadRequestError):
        return "⚠️ Ungültige Anfrage."
    if isinstance(e, APIError):
        return "🚨 OpenAI API-Fehler."
    return f"Unerwarteter Fehler: {e}"


def call_llm(client: OpenAI, model: str, system: str, user: str, temperature: float) -> str:
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )
    return r.choices[0].message.content.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Domain Logic (Abhängigkeiten)
# ──────────────────────────────────────────────────────────────────────────────
THEMES = {
    "Narzisstischer Missbrauch": ["Frauen in Trennung", "Frauen im Heilungsprozess", "Langzeit-Überlebende"],
    "Gaslighting": ["Frauen in Trennung", "Frauen im Heilungsprozess"],
    "No Contact": ["Frauen in Trennung", "Langzeit-Überlebende"],
    "Grenzen setzen": ["Frauen im Heilungsprozess", "Langzeit-Überlebende", "Angehörige"],
    "Selbstwert stärken": ["Frauen im Heilungsprozess", "Langzeit-Überlebende", "Angehörige"],
}

TONES_BY_AUDIENCE = {
    "Frauen in Trennung": ["Sehr sanft", "Klar & stabil"],
    "Frauen im Heilungsprozess": ["Sehr sanft", "Klar & stabil", "Konfrontativ"],
    "Langzeit-Überlebende": ["Klar & stabil", "Konfrontativ"],
    "Angehörige": ["Klar & stabil"],
}

CTAS_BY_TYPE = {
    "Community Newsletter": ["Community beitreten", "Ressourcen erhalten"],
    "Marketing Newsletter": ["Kostenfreies Erstgespräch", "Online-Kurs", "E-Book Download"],
}

DEPTHS = {
    "Sanft & kurz": "kurz, beruhigend, wenige Impulse",
    "Ausgewogen": "ausgewogen, reflektierend, 3–5 Impulse",
    "Tief & transformierend": "tiefgehend, transformierend, klare innere Arbeit",
}


# ──────────────────────────────────────────────────────────────────────────────
# UI Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("# 💜 Newsletter Generator")
st.markdown("### *Raus aus dem Gift*")
st.markdown("<div class='small-muted'>Automatisierte, stimmige Newsletter – ohne Brüche.</div>", unsafe_allow_html=True)
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    if get_api_key():
        st.success("✅ API-Key gefunden")
    else:
        st.error("❌ Kein API-Key")
        st.stop()

    model = st.selectbox("Modell", ["gpt-4o-mini", "gpt-4o"], index=0)
    temperature = st.slider("Kreativität", 0.0, 1.2, 0.7, 0.1)

# ──────────────────────────────────────────────────────────────────────────────
# Inputs (abhängig)
# ──────────────────────────────────────────────────────────────────────────────
newsletter_type = st.selectbox("📧 Newsletter-Typ", ["Community Newsletter", "Marketing Newsletter"])

theme = st.selectbox("🎯 Thema", list(THEMES.keys()))
audience = st.selectbox("👥 Zielgruppe", THEMES[theme])
tone = st.selectbox("💬 Tonalität", TONES_BY_AUDIENCE[audience])
depth = st.selectbox("🧠 Inhalts-Tiefe", list(DEPTHS.keys()))

cta = st.selectbox("🎯 Call-to-Action", CTAS_BY_TYPE[newsletter_type])
extra = st.text_area("📝 Zusätzliche Hinweise (optional)", height=120)

# ──────────────────────────────────────────────────────────────────────────────
# Generate
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("---")

if st.button("✨ Newsletter & Header generieren", use_container_width=True):
    with st.spinner("💜 Generierung läuft …"):
        try:
            client = get_client()

            base_prompt = f"""
Du bist eine traumasensible Content-Expertin für "{BRAND}".

Erstelle einen {newsletter_type}.
Thema: {theme}
Zielgruppe: {audience}
Tonalität: {tone}
Tiefe: {DEPTHS[depth]}
CTA: {cta}

Regeln:
- keine Diagnosen
- validierend, stärkend
- klarer Aufbau
- am Ende passender CTA

Zusatz:
{extra if extra.strip() else "Keine"}

Gib nur den Newsletter-Text zurück.
"""

            content = call_llm(
                client,
                model,
                "Du schreibst sichere, stimmige Newsletter für emotionale Heilung.",
                base_prompt,
                temperature,
            )

            header_prompt = f"""
Erstelle 5 Header + Preheader.
Stil: Hoffnungsvoll & stärkend, warm & validierend, klar & aufdeckend (in dieser Priorität).
Thema: {theme}
Zielgruppe: {audience}

Format exakt:
1) Header: ...
   Preheader: ...
...
5) Header: ...
   Preheader: ...
"""

            headers = call_llm(
                client,
                model,
                "Du bist Expertin für E-Mail-Marketing & traumasensible Kommunikation.",
                header_prompt,
                temperature,
            )

            st.session_state.output = {
                "headers": headers,
                "content": content,
                "cta": cta,
                "meta": {
                    "type": newsletter_type,
                    "theme": theme,
                    "audience": audience,
                    "tone": tone,
                    "depth": depth,
                    "model": model,
                    "generated_at": datetime.now().isoformat(),
                },
            }

            st.success("✅ Fertig!")

        except Exception as e:
            st.error(friendly_error(e))

# ──────────────────────────────────────────────────────────────────────────────
# Output & Export
# ──────────────────────────────────────────────────────────────────────────────
if "output" in st.session_state:
    out = st.session_state.output

    st.markdown("## 🧾 Header & Preheader")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(out["headers"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("## ✍️ Newsletter")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(out["content"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("## 🎯 CTA")
    st.markdown(f"**{out['cta']}**")

    st.download_button(
        "💾 Newsletter (TXT)",
        out["content"],
        file_name="newsletter.txt",
        mime="text/plain",
    )

    st.download_button(
        "📋 Komplett (JSON)",
        json.dumps(out, indent=2, ensure_ascii=False),
        file_name="newsletter.json",
        mime="application/json",
    )
