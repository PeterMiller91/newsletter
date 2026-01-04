import re
import textwrap
import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# =========================
# Environment Variables
# =========================
load_dotenv()  # Lade .env Datei

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Raus aus dem Gift — Newsletter Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Session State
# =========================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "newsletter_raw" not in st.session_state:
    st.session_state.newsletter_raw = ""

if "subject_selected" not in st.session_state:
    st.session_state.subject_selected = ""

if "preheader" not in st.session_state:
    st.session_state.preheader = ""

if "newsletter_body" not in st.session_state:
    st.session_state.newsletter_body = ""

if "cta_variants" not in st.session_state:
    st.session_state.cta_variants = []

if "debug_prompt" not in st.session_state:
    st.session_state.debug_prompt = ""

if "generation_history" not in st.session_state:
    st.session_state.generation_history = []

if "current_version" not in st.session_state:
    st.session_state.current_version = 1

if "api_source" not in st.session_state:
    st.session_state.api_source = "manual"

# =========================
# Theme / CSS - Responsive
# =========================
def apply_theme() -> None:
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            /* Basis-Styles */
            .stApp { 
                background-color: #0E0B16; 
                color: #E0E0E0; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            /* Responsive Text */
            @media (max-width: 768px) {
                h1 { font-size: 1.8rem !important; }
                h2 { font-size: 1.5rem !important; }
                h3 { font-size: 1.3rem !important; }
                .stButton button { font-size: 0.9rem !important; padding: 0.4rem 0.8rem !important; }
                .stTextArea textarea { font-size: 0.95rem !important; }
            }
            
            @media (max-width: 480px) {
                h1 { font-size: 1.6rem !important; }
                h2 { font-size: 1.3rem !important; }
                .stButton button { font-size: 0.85rem !important; padding: 0.3rem 0.6rem !important; }
            }
            
            /* Headings */
            h1, h2, h3, h4 { 
                color: #BB86FC !important; 
                font-weight: 600;
                margin-bottom: 1rem;
            }
            
            /* Form Elements */
            .stTextInput input, 
            .stTextArea textarea, 
            .stSelectbox div[data-baseweb="select"] {
                background-color: #1F1B24 !important; 
                color: white !important;
                border: 1px solid #444 !important;
                border-radius: 8px !important;
                font-size: 1rem;
            }
            
            .stTextArea textarea {
                min-height: 200px;
                resize: vertical;
            }
            
            div[role="listbox"] ul { 
                background-color: #1F1B24 !important; 
                color: white !important;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] { 
                background-color: #15121E; 
            }
            
            /* Buttons - Responsive */
            .stButton button { 
                background-color: #6A1B9A !important; 
                color: white !important; 
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
                font-size: 1rem !important;
                padding: 0.5rem 1rem !important;
                width: 100% !important;
                min-height: 44px !important; /* Touch-friendly */
            }
            
            .stButton button:hover { 
                background-color: #7B2CBF !important; 
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(106, 27, 154, 0.3) !important;
            }
            
            .stButton button:active { 
                transform: translateY(0);
            }
            
            /* Primary Buttons */
            .stButton button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #6A1B9A, #8E24AA) !important;
                font-weight: 600 !important;
            }
            
            /* Secondary Buttons */
            .stButton button:not([data-testid="baseButton-primary"]) {
                background-color: #333344 !important;
                border: 1px solid #555 !important;
            }
            
            /* Pills */
            .pill { 
                display: inline-block; 
                padding: 6px 12px; 
                border-radius: 20px; 
                background: #1F1B24; 
                border: 1px solid #3b3b3b; 
                margin-right: 8px; 
                margin-bottom: 8px; 
                font-size: 0.9rem; 
                color: #E0E0E0;
                transition: all 0.2s ease;
            }
            
            .pill:hover {
                background: #2A2535;
                border-color: #BB86FC;
            }
            
            /* Preview Box */
            .preview-box {
                padding: 1.5rem;
                background-color: #1F1B24;
                border-left: 5px solid #BB86FC;
                border-radius: 12px;
                color: #eee;
                margin-top: 1rem;
                line-height: 1.6;
                font-size: 1rem;
                overflow-wrap: break-word;
                word-wrap: break-word;
            }
            
            /* Metrics */
            .stMetric {
                background-color: #1F1B24;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #333;
            }
            
            /* Badges */
            .success-badge { 
                background-color: #2E7D32; 
                color: white; 
                padding: 4px 10px; 
                border-radius: 12px; 
                font-size: 0.8em; 
                margin-left: 8px; 
                display: inline-block;
            }
            
            .warning-badge { 
                background-color: #FF9800; 
                color: white; 
                padding: 4px 10px; 
                border-radius: 12px; 
                font-size: 0.8em; 
                margin-left: 8px; 
                display: inline-block;
            }
            
            .version-badge { 
                background-color: #6A1B9A; 
                color: white; 
                padding: 4px 12px; 
                border-radius: 12px; 
                font-size: 0.85em; 
                display: inline-block;
                margin-bottom: 10px;
            }
            
            /* Progress Bar */
            .stProgress > div > div > div > div { 
                background-color: #BB86FC; 
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: #1F1B24;
                border-radius: 8px;
                border: 1px solid #333;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: #1F1B24;
                border-radius: 8px 8px 0 0;
                padding: 10px 16px;
            }
            
            /* Responsive Grid */
            @media (max-width: 768px) {
                .stMetric {
                    padding: 8px;
                    font-size: 0.9rem;
                }
                .preview-box {
                    padding: 1rem;
                }
                .pill {
                    font-size: 0.85rem;
                    padding: 5px 10px;
                }
            }
            
            /* Mobile Menu */
            @media (max-width: 768px) {
                section[data-testid="stSidebar"] {
                    width: 100% !important;
                }
            }
            
            /* Text Colors */
            .muted { 
                color: #b6b6b6; 
                font-size: 0.95rem;
            }
            
            .text-success { color: #4CAF50 !important; }
            .text-warning { color: #FF9800 !important; }
            .text-danger { color: #F44336 !important; }
            
            /* Custom Button Styles */
            .btn-extend { 
                background: linear-gradient(135deg, #FF6B6B, #FF8E53) !important; 
            }
            
            .btn-shorten { 
                background: linear-gradient(135deg, #4ECDC4, #44A08D) !important; 
            }
            
            .btn-rewrite { 
                background: linear-gradient(135deg, #4776E6, #8E54E9) !important; 
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            /* Light Mode Styles - Responsive */
            .stApp { 
                background-color: #FDFBF7; 
                color: #333; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            /* Responsive Text */
            @media (max-width: 768px) {
                h1 { font-size: 1.8rem !important; }
                h2 { font-size: 1.5rem !important; }
                h3 { font-size: 1.3rem !important; }
                .stButton button { font-size: 0.9rem !important; padding: 0.4rem 0.8rem !important; }
                .stTextArea textarea { font-size: 0.95rem !important; }
            }
            
            @media (max-width: 480px) {
                h1 { font-size: 1.6rem !important; }
                h2 { font-size: 1.3rem !important; }
                .stButton button { font-size: 0.85rem !important; padding: 0.3rem 0.6rem !important; }
            }
            
            /* Headings */
            h1, h2, h3, h4 { 
                color: #4A148C !important; 
                font-weight: 600;
                margin-bottom: 1rem;
            }
            
            /* Form Elements */
            .stTextInput input, 
            .stTextArea textarea, 
            .stSelectbox div[data-baseweb="select"] {
                background-color: white !important; 
                color: black !important;
                border: 1px solid #ddd !important;
                border-radius: 8px !important;
                font-size: 1rem;
            }
            
            .stTextArea textarea {
                min-height: 200px;
                resize: vertical;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] { 
                background-color: #F3F0FA; 
            }
            
            /* Buttons - Responsive */
            .stButton button { 
                background-color: #6A1B9A !important; 
                color: white !important; 
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
                font-size: 1rem !important;
                padding: 0.5rem 1rem !important;
                width: 100% !important;
                min-height: 44px !important;
            }
            
            .stButton button:hover { 
                background-color: #7B2CBF !important; 
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(106, 27, 154, 0.2) !important;
            }
            
            .stButton button:active { 
                transform: translateY(0);
            }
            
            /* Primary Buttons */
            .stButton button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #6A1B9A, #8E24AA) !important;
                font-weight: 600 !important;
            }
            
            /* Secondary Buttons */
            .stButton button:not([data-testid="baseButton-primary"]) {
                background-color: #EDE7F6 !important;
                color: #4A148C !important;
                border: 1px solid #D1C4E9 !important;
            }
            
            /* Pills */
            .pill { 
                display: inline-block; 
                padding: 6px 12px; 
                border-radius: 20px; 
                background: #fff; 
                border: 1px solid #e6e6e6; 
                margin-right: 8px; 
                margin-bottom: 8px; 
                font-size: 0.9rem; 
                color: #333;
                transition: all 0.2s ease;
            }
            
            .pill:hover {
                background: #F3F0FA;
                border-color: #6A1B9A;
            }
            
            /* Preview Box */
            .preview-box {
                padding: 1.5rem;
                background-color: white;
                border-left: 5px solid #6A1B9A;
                border-radius: 12px;
                box-shadow: 0 2px 15px rgba(0,0,0,0.08);
                color: #111;
                margin-top: 1rem;
                line-height: 1.6;
                font-size: 1rem;
                overflow-wrap: break-word;
                word-wrap: break-word;
            }
            
            /* Metrics */
            .stMetric {
                background-color: white;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #eee;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            /* Badges */
            .success-badge { 
                background-color: #4CAF50; 
                color: white; 
                padding: 4px 10px; 
                border-radius: 12px; 
                font-size: 0.8em; 
                margin-left: 8px; 
                display: inline-block;
            }
            
            .warning-badge { 
                background-color: #FF9800; 
                color: white; 
                padding: 4px 10px; 
                border-radius: 12px; 
                font-size: 0.8em; 
                margin-left: 8px; 
                display: inline-block;
            }
            
            .version-badge { 
                background-color: #6A1B9A; 
                color: white; 
                padding: 4px 12px; 
                border-radius: 12px; 
                font-size: 0.85em; 
                display: inline-block;
                margin-bottom: 10px;
            }
            
            /* Progress Bar */
            .stProgress > div > div > div > div { 
                background-color: #6A1B9A; 
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #eee;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            
            .stTabs [data-baseweb="tab"] {
                background-color: white;
                border-radius: 8px 8px 0 0;
                padding: 10px 16px;
                border: 1px solid #eee;
            }
            
            /* Responsive Grid */
            @media (max-width: 768px) {
                .stMetric {
                    padding: 8px;
                    font-size: 0.9rem;
                }
                .preview-box {
                    padding: 1rem;
                }
                .pill {
                    font-size: 0.85rem;
                    padding: 5px 10px;
                }
            }
            
            /* Mobile Menu */
            @media (max-width: 768px) {
                section[data-testid="stSidebar"] {
                    width: 100% !important;
                }
            }
            
            /* Text Colors */
            .muted { 
                color: #666; 
                font-size: 0.95rem;
            }
            
            .text-success { color: #4CAF50 !important; }
            .text-warning { color: #FF9800 !important; }
            .text-danger { color: #F44336 !important; }
            
            /* Custom Button Styles */
            .btn-extend { 
                background: linear-gradient(135deg, #FF6B6B, #FF8E53) !important; 
            }
            
            .btn-shorten { 
                background: linear-gradient(135deg, #4ECDC4, #44A08D) !important; 
            }
            
            .btn-rewrite { 
                background: linear-gradient(135deg, #4776E6, #8E54E9) !important; 
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

apply_theme()

# =========================
# Helpers
# =========================
def clamp_text(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"

def count_words(s: str) -> int:
    return len(re.findall(r"\b\w+\b", s or ""))

def extract_sections(raw: str) -> dict:
    out = {
        "subjects": [],
        "preheader": "",
        "newsletter": "",
        "ctas": [],
    }
    if not raw:
        return out

    txt = raw.replace("\r\n", "\n").strip()

    # Subjects
    m = re.search(r"BETREFF:\s*(.*?)\n\s*PREHEADER:", txt, flags=re.S | re.I)
    if m:
        subj_block = m.group(1).strip()
        subs = []
        for line in subj_block.split("\n"):
            line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
            if line:
                subs.append(line)
        out["subjects"] = subs[:15]
    
    if not out["subjects"]:
        m = re.search(r"BETREFF:\s*(.*?)\n\s*\n", txt, flags=re.S | re.I)
        if m:
            subj_block = m.group(1).strip()
            subs = []
            for line in subj_block.split("\n"):
                line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
                if line:
                    subs.append(line)
            out["subjects"] = subs[:15]

    # Preheader
    m = re.search(r"PREHEADER:\s*(.*?)\n\s*(---|NEWSLETTER:)", txt, flags=re.S | re.I)
    if m:
        out["preheader"] = m.group(1).strip()
    elif "PREHEADER:" in txt:
        parts = txt.split("PREHEADER:")
        if len(parts) > 1:
            pre_part = parts[1].split("\n")[0].strip()
            out["preheader"] = pre_part

    # Newsletter body
    m = re.search(r"NEWSLETTER:\s*(.*?)(\n\s*CTA_VARIANTEN:|\Z)", txt, flags=re.S | re.I)
    if m:
        out["newsletter"] = m.group(1).strip()
    elif "---" in txt:
        parts = txt.split("---")
        if len(parts) > 1:
            out["newsletter"] = parts[1].strip()

    # CTA variants
    m = re.search(r"CTA_VARIANTEN:\s*(.*)$", txt, flags=re.S | re.I)
    if m:
        cta_block = m.group(1).strip()
        ctas = []
        for line in cta_block.split("\n"):
            line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
            if line:
                ctas.append(line)
        out["ctas"] = ctas[:10]
    elif "CTA_VARIANTEN:" in txt:
        parts = txt.split("CTA_VARIANTEN:")
        if len(parts) > 1:
            cta_block = parts[1].strip()
            ctas = []
            for line in cta_block.split("\n"):
                line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
                if line:
                    ctas.append(line)
            out["ctas"] = ctas[:10]

    return out

def build_system_prompt() -> str:
    return textwrap.dedent(
        """
        Du bist ein Elite-Direct-Response-Copywriter für 'Raus aus dem Gift'.
        Thema: toxische Beziehungen, Trennung, Heilung, Selbstwert, Grenzen.

        Du schreibst nach einem FIXEN Framework, um konstant High-Performance-Newsletter zu liefern.

        OUTPUT (streng einhalten):
        BETREFF:
        1. ...
        2. ...
        ...
        10. ...

        PREHEADER:
        <1 Satz, max. 90 Zeichen>

        ---
        NEWSLETTER:
        <Text in kurzen Absätzen>

        CTA_VARIANTEN:
        1. ...
        2. ...
        3. ...

        REGELN:
        - Du-Ansprache, kurze Sätze, kurze Absätze (max 2 Sätze).
        - Keine Floskeln. Kein Coaching-Geschwurbel. Kein Over-Explaining.
        - Baue visuelle Anker: **Fett** nur für:
          (a) validierende Sätze, (b) Fachbegriffe, (c) konkrete Schritte, (d) CTA.
        - Nutze psychologische Präzision, aber bleib alltagstauglich.
        - Kein medizinischer oder rechtlicher Rat.
        """
    ).strip()

def build_user_prompt(
    reader_state: str,
    topic: str,
    tone_label: str,
    mode: str,
    product_context: str,
    goal_kpi: str,
    audience_level: str,
    length_target: str,
    keywords: str,
    forbidden: str,
    extend_text: bool = False,  # NEU: Parameter für Textverlängerung
    current_text: str = ""      # NEU: Aktueller Text für Verlängerung
) -> str:
    extra_rules = []
    if keywords.strip():
        extra_rules.append(f"Nutze diese Keywords organisch: {keywords.strip()}")
    if forbidden.strip():
        extra_rules.append(f"Vermeide unbedingt diese Wörter/Phrasen: {forbidden.strip()}")

    length_map = {
        "Kurz (≈ 250–400 Wörter)": "Ziel: 250–400 Wörter.",
        "Mittel (≈ 400–650 Wörter)": "Ziel: 400–650 Wörter.",
        "Lang (≈ 650–900 Wörter)": "Ziel: 650–900 Wörter.",
    }
    kpi_map = {
        "Öffnungsrate": "Optimiere maximal auf Öffnungen: Betreff neugierig, klar, ohne Clickbait.",
        "Klickrate": "Optimiere auf Klicks: starker CTA, klare nächste Aktion, wenig Reibung.",
        "Antworten/Engagement": "Optimiere auf Antworten: 1 starke Frage am Ende, emotionaler Trigger.",
        "Verkäufe": "Optimiere auf Conversions: Schmerz → Lösung → proof → CTA, ohne Druck.",
    }

    mode_line = "MODUS: MEHRWERT." if mode == "Mehrwert (Tipp)" else "MODUS: VERKAUF."
    if mode != "Mehrwert (Tipp)":
        mode_line += f" Angebot-Details: {product_context.strip() or '(keine Details gegeben)'}"

    # NEU: Verlängerungs-Prompt
    if extend_text and current_text:
        extend_instruction = f"""
        AKTUELLER TEXT (verlängern/ergänzen):
        {current_text[:800]}...
        
        ANWEISUNG FÜR VERLÄNGERUNG:
        - Behalte den vorhandenen Inhalt, Stil und Ton bei
        - Füge NEUE Inhalte hinzu, die den bestehenden Text ergänzen
        - Vertiefe die bestehenden Punkte mit zusätzlichen Beispielen, Erklärungen oder Geschichten
        - Füge 1-2 neue Absätze ein, die den Wert erhöhen
        - Achte darauf, dass der Text natürlich weiterfließt
        - Ziel: Text um etwa 30-50% verlängern
        """
        current_text_section = extend_instruction
    else:
        current_text_section = ""

    return textwrap.dedent(
        f"""
        BRIEFING:
        - Leserphase: {reader_state}
        - Thema: {topic.strip() or 'Allgemein, aber fokussiert auf Heilung / Grenzen'}
        - Ton: {tone_label}
        - Ziel: {mode_line}
        - Ziel-KPI: {goal_kpi} ({kpi_map.get(goal_kpi, '')})
        - Audience-Level: {audience_level} (Einsteiger = simpel, Fortgeschritten = präziser)
        - Länge: {length_map.get(length_target, '')}

        {current_text_section}

        PSYCHOLOGISCHE ANFORDERUNG:
        - Beginne mit einem Hook, der die exakte Innenwelt der Leserphase trifft.
        - Dann Validierung (Schuld rausnehmen).
        - Dann Reframe (neue Perspektive).
        - Dann ein konkreter Schritt (heute machbar).
        - Dann CTA (passend zur Leserphase).

        {("ZUSATZREGELN:\n- " + "\n- ".join(extra_rules)) if extra_rules else ""}

        WICHTIG:
        - Betreffzeilen: max. 45 Zeichen, unterschiedlich, keine Duplikate.
        - Preheader: max. 90 Zeichen, ergänzt Betreff (nicht wiederholen).
        - CTA_VARIANTEN: 3–5 Varianten, unterschiedlich in Ton & Reibung.

        Gib NUR das geforderte Output-Format zurück.
        """
    ).strip()

def call_openai(api_key: str, model: str, system: str, user: str, temperature: float) -> str:
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""

def rewrite_prompt(kind: str, reader_state: str, tone_label: str, current_text: str = "") -> str:
    variants = {
        "Kürzer": "Kürze radikal. Entferne Wiederholungen. Mehr Punch. Gleiches Framework beibehalten.",
        "Verlängern": "Füge mehr Tiefe, Beispiele und Erklärungen hinzu. Vertiefe die bestehenden Punkte mit zusätzlichen Insights.",
        "Direkter": "Weniger weich. Mehr Klartext. Härtere Sätze. Kein Drama. Mehr Führung.",
        "Sanfter": "Mehr Wärme, mehr Sicherheit. Gleiche Klarheit, aber beruhigender Ton.",
        "Mehr Story": "Baue eine kurze Mini-Story am Anfang ein (3–6 Sätze) statt abstraktem Einstieg.",
        "Mehr Conversion": "Stärkerer Benefit-Stack, mehr Proof/Logik, CTA klarer, aber ohne Druck.",
        "Mehr Empathie": "Betone mehr Verständnis und Validierung. Zeige, dass du die Leserin wirklich verstehst.",
        "Mehr Actionable": "Fokussiere auf konkrete, umsetzbare Schritte. Weniger Theorie, mehr Praxis.",
    }
    instr = variants.get(kind, "Überarbeite den Text sinnvoll.")
    
    if kind == "Verlängern" and current_text:
        instr += f"\n\nAKTUELLER TEXT:\n{current_text[:1000]}\n\nVerlängere diesen Text um etwa 30-50%, füge mehr Tiefe und Beispiele hinzu."
    
    return textwrap.dedent(
        f"""
        Du überarbeitest einen bestehenden Newsletter.
        Leserphase: {reader_state}
        Ton: {tone_label}

        ANWEISUNG:
        {instr}

        Behalte das Output-Format bei (BETREFF / PREHEADER / --- / NEWSLETTER / CTA_VARIANTEN).
        """
    ).strip()

def add_to_history(version_data: dict) -> None:
    st.session_state.generation_history.append(version_data)
    if len(st.session_state.generation_history) > 10:
        st.session_state.generation_history = st.session_state.generation_history[-10:]

# =========================
# Sidebar - Responsive
# =========================
with st.sidebar:
    st.title("⚙️ Einstellungen")
    
    # Theme Toggle mit responsive Layout
    col_theme1, col_theme2 = st.columns([1, 1])
    with col_theme1:
        if st.session_state.dark_mode:
            if st.button("🌞 Hell", use_container_width=True, help="Zum Hellmodus wechseln"):
                st.session_state.dark_mode = False
                st.rerun()
        else:
            if st.button("🌙 Dunkel", use_container_width=True, help="Zum Dunkelmodus wechseln"):
                st.session_state.dark_mode = True
                st.rerun()
    
    with col_theme2:
        if st.button("🔄 Neu laden", use_container_width=True, help="Seite neu laden"):
            st.rerun()
    
    st.markdown("---")
    
    # API Konfiguration
    st.subheader("🔑 API Konfiguration")
    env_api_key = os.getenv("OPENAI_API_KEY")
    
    if env_api_key:
        st.success("✅ API Key aus .env geladen")
        use_env = st.checkbox(".env Key verwenden", value=True, help="API Key aus .env Datei nutzen")
        
        if use_env:
            api_key = env_api_key
            st.session_state.api_source = "env"
        else:
            api_key = st.text_input("Manueller API Key", type="password", 
                                  help="Überschreibt .env Key", value="")
            st.session_state.api_source = "manual"
    else:
        st.warning("⚠️ Kein .env Key gefunden")
        api_key = st.text_input("OpenAI API Key", type="password", 
                              help="Trage deinen Key ein oder erstelle .env Datei")
        st.session_state.api_source = "manual"
    
    # Modelauswahl
    model_choice = st.selectbox(
        "🤖 Modell auswählen",
        ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="GPT-4o ist empfohlen für beste Qualität"
    )
    
    st.markdown("---")
    
    # Performance Einstellungen
    st.subheader("🎯 Performance")
    
    goal_kpi = st.selectbox(
        "Primäre KPI",
        ["Öffnungsrate", "Klickrate", "Antworten/Engagement", "Verkäufe"],
        index=1,
        help="Worauf soll optimiert werden?"
    )
    
    audience_level = st.selectbox(
        "Zielgruppe",
        ["Einsteiger", "Fortgeschritten", "Experte"],
        index=0,
        help="Anspruchsniveau der Leser"
    )
    
    length_target = st.selectbox(
        "Ziel-Länge",
        ["Kurz (≈ 250–400 Wörter)", "Mittel (≈ 400–650 Wörter)", "Lang (≈ 650–900 Wörter)"],
        index=1,
        help="Gewünschte Textlänge"
    )
    
    # Temperature Slider
    temp_value = st.slider(
        "🎨 Kreativität", 
        0.0, 1.0, 0.7, 0.05,
        help="Niedrig = konsistenter, Hoch = kreativer"
    )
    
    st.markdown("---")
    
    # Version History
    if st.session_state.generation_history:
        st.subheader("📜 Versionen")
        for i, version in enumerate(reversed(st.session_state.generation_history[-5:])):
            btn_text = f"v{version['version']} - {version['action'][:15]}..."
            if st.button(btn_text, key=f"hist_{i}", use_container_width=True):
                st.session_state.newsletter_raw = version['raw']
                st.session_state.subject_selected = version['subject']
                st.session_state.preheader = version['preheader']
                st.session_state.newsletter_body = version['body']
                st.session_state.cta_variants = version['ctas']
                st.session_state.current_version = version['version']
                st.rerun()
    
    st.markdown("---")
    
    # Debug Option
    show_debug = st.toggle("🔧 Debug-Modus", value=False, help="Zeigt den Prompt an")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Schnellzugriff")
    
    col_quick1, col_quick2 = st.columns(2)
    with col_quick1:
        if st.button("📋 Kopieren", use_container_width=True, help="Text kopieren"):
            export_text = f"{st.session_state.subject_selected}\n\n{st.session_state.newsletter_body[:500]}..."
            st.code(export_text)
            st.success("Text bereit zum Kopieren!")
    
    with col_quick2:
        if st.button("🔄 Reset", use_container_width=True, help="Alles zurücksetzen"):
            for key in list(st.session_state.keys()):
                if key != "dark_mode":
                    del st.session_state[key]
            st.rerun()

# =========================
# Main UI - Responsive
# =========================
st.title("🛡️ Raus aus dem Gift — Newsletter Engine")
st.caption("Professioneller Generator für wirkungsvolle Newsletter")

# Version Info
if st.session_state.current_version > 1:
    st.markdown(f'<span class="version-badge">Version {st.session_state.current_version}</span>', unsafe_allow_html=True)

# Responsive Columns
col_input, col_output = st.columns([1, 1.25], gap="large")

tone_map = {1: "Sanft & Tröstend", 2: "Verständnisvoll", 3: "Ausgewogen", 4: "Direkt", 5: "Harter Klartext"}

with col_input:
    st.subheader("1️⃣ Briefing erstellen")
    
    # Reader State
    reader_state = st.selectbox(
        "📊 Phase des Lesers",
        ["Akute Krise (Noch in Beziehung)", "Frisch getrennt (No Contact)", "Heilungsphase (Monate später)", "Gemischt"],
        help="In welcher Phase befindet sich deine Leserin?"
    )
    
    # Topic
    topic = st.text_input(
        "🎯 Thema", 
        placeholder="z.B. Grenzen setzen, Co-Parenting, Selbstwert stärken...",
        help="Hauptthema des Newsletters"
    )
    
    # Tone Settings
    st.markdown("**🎭 Ton einstellen**")
    tone_val = st.slider(
        "Härtegrad", 
        1, 5, 3,
        help="1 = sehr sanft, 5 = sehr direkt",
        label_visibility="collapsed"
    )
    tone_label = tone_map[tone_val]
    st.caption(f"Eingestellter Ton: **{tone_label}**")
    
    st.markdown("---")
    
    # Template und Modus
    template_choice = st.selectbox(
        "📋 Vorlage",
        ["Standard", "Schmerzpunkt → Lösung", "Story-basiert", "FAQ-Format", "Liste"],
        index=0,
        help="Wähle eine Strukturvorlage"
    )
    
    mode = st.radio(
        "🎯 Ziel des Newsletters",
        ["📖 Mehrwert (Tipp)", "💰 Verkauf (Pitch)"],
        horizontal=True,
        help="Soll der Newsletter informieren oder verkaufen?"
    )
    
    product_context = ""
    if mode == "💰 Verkauf (Pitch)":
        product_context = st.text_area(
            "🛍️ Angebot-Details",
            placeholder="Was bietest du an? Preis? Vorteile? Jetzt buchen...",
            height=100,
            help="Details zu deinem Angebot"
        )
    
    st.markdown("---")
    
    # Erweiterte Einstellungen
    with st.expander("⚙️ Erweiterte Einstellungen", expanded=False):
        keywords = st.text_input(
            "🔑 Keywords", 
            placeholder="z.B. Gaslighting, Trauma Bond, No Contact",
            help="Wichtige Begriffe, die enthalten sein sollen"
        )
        
        forbidden = st.text_input(
            "🚫 No-Go Wörter", 
            placeholder="z.B. universum, manifestieren, toxisch",
            help="Wörter, die vermieden werden sollen"
        )
        
        # Emotional Triggers
        emotional_triggers = st.multiselect(
            "💖 Emotionale Trigger",
            ["Angst", "Hoffnung", "Neugier", "Wut", "Traurigkeit", "Erleichterung", "Stolz"],
            default=["Hoffnung", "Erleichterung"],
            help="Welche Emotionen sollen angesprochen werden?"
        )
    
    # Action Buttons
    st.markdown("---")
    st.markdown("### 🚀 Aktionen")
    
    col_action1, col_action2, col_action3 = st.columns([1, 1, 1])
    
    with col_action1:
        generate_btn = st.button(
            "⚡ Generieren", 
            type="primary", 
            use_container_width=True,
            help="Neuen Newsletter generieren"
        )
    
    with col_action2:
        clear_btn = st.button(
            "🗑️ Löschen", 
            use_container_width=True,
            help="Alles zurücksetzen"
        )
    
    with col_action3:
        save_btn = st.button(
            "💾 Speichern", 
            use_container_width=True,
            disabled=not st.session_state.newsletter_body,
            help="Als Template speichern"
        )
    
    if clear_btn:
        for key in ["newsletter_raw", "subject_selected", "preheader", "newsletter_body", "cta_variants", "debug_prompt"]:
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.current_version = 1
        st.rerun()
    
    if save_btn and st.session_state.newsletter_body:
        if "saved_templates" not in st.session_state:
            st.session_state.saved_templates = []
        template_data = {
            "subject": st.session_state.subject_selected,
            "preheader": st.session_state.preheader,
            "body": st.session_state.newsletter_body,
            "ctas": st.session_state.cta_variants,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.saved_templates.append(template_data)
        st.success("✅ Als Template gespeichert!")

# =========================
# Generation Function
# =========================
def run_generation(extend=False):
    if not api_key:
        st.error("⚠️ Bitte API Key eingeben oder in .env Datei hinterlegen.")
        return
    
    if not topic.strip() and not extend:
        st.warning("Bitte gib ein Thema an.")
    
    system = build_system_prompt()
    user = build_user_prompt(
        reader_state=reader_state,
        topic=topic,
        tone_label=tone_label,
        mode=mode,
        product_context=product_context,
        goal_kpi=goal_kpi,
        audience_level=audience_level,
        length_target=length_target,
        keywords=keywords,
        forbidden=forbidden,
        extend_text=extend,
        current_text=st.session_state.newsletter_body if extend else ""
    )
    
    # Template-Anweisungen
    if template_choice != "Standard":
        template_instructions = {
            "Schmerzpunkt → Lösung": "Beginne mit klarem Schmerzpunkt, dann konkrete Lösung.",
            "Story-basiert": "Verwende persönliche Geschichte als Einstieg.",
            "FAQ-Format": "Strukturiere als Fragen und Antworten.",
            "Liste": "Präsentiere als nummerierte Liste oder Aufzählung.",
        }
        user += f"\n\nVorlage: {template_choice}\n{template_instructions.get(template_choice, '')}"
    
    st.session_state.debug_prompt = f"SYSTEM:\n{system}\n\nUSER:\n{user}"
    
    with st.spinner("📝 Schreibe Newsletter..."):
        progress_bar = st.progress(0)
        
        try:
            raw = call_openai(api_key, model_choice, system, user, temp_value)
            st.session_state.newsletter_raw = raw
            
            sections = extract_sections(raw)
            st.session_state.preheader = sections["preheader"] or ""
            st.session_state.newsletter_body = sections["newsletter"] or ""
            st.session_state.cta_variants = sections["ctas"] or []
            
            # History
            version_data = {
                "version": st.session_state.current_version,
                "timestamp": datetime.now().isoformat(),
                "action": "Generiert" + (" (verlängert)" if extend else ""),
                "topic": topic,
                "raw": raw,
                "subject": sections["subjects"][0] if sections["subjects"] else "",
                "preheader": sections["preheader"] or "",
                "body": sections["newsletter"] or "",
                "ctas": sections["ctas"] or [],
            }
            add_to_history(version_data)
            
            # Subject
            subjects = sections["subjects"]
            st.session_state.subject_selected = subjects[0] if subjects else ""
            
            # Version
            st.session_state.current_version += 1
            
            progress_bar.progress(100)
            st.success(f"✅ Newsletter {'verlängert' if extend else 'generiert'}!")
            
        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ Fehler: {e}")

if generate_btn:
    run_generation()

# =========================
# Output / Editor - Responsive
# =========================
with col_output:
    if not st.session_state.newsletter_raw:
        # Empty State
        st.subheader("2️⃣ Editor & Vorschau")
        st.info("""
        **🎯 Noch nichts generiert**
        
        1. Links Briefing ausfüllen
        2. **⚡ Generieren** klicken
        3. Ergebnis bearbeiten & exportieren
        
        Tipp: Du kannst deinen API Key auch in einer `.env` Datei speichern!
        """)
        
        # Quick Examples
        with st.expander("🚀 Schnellstart-Beispiele", expanded=False):
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if st.button("🎯 Grenzen setzen", use_container_width=True):
                    st.session_state.subject_selected = "Deine Grenzen sind kein Luxus"
                    st.session_state.preheader = "Warum Grenzen das Fundament deiner Heilung sind"
                    st.session_state.newsletter_body = """Du fragst dich, ob es egoistisch ist, Grenzen zu setzen.

Die Antwort ist einfach: **Nein.**

Grenzen sind kein Luxus. Sie sind das Fundament deiner Sicherheit.

Ohne Grenzen sagst du im Grunde: "Meine Bedürfnisse sind weniger wichtig als deine."

Das ist kein Mitgefühl. Das ist Selbstaufgabe.

**Heutiger Schritt:** Schreibe eine Grenze auf, die du heute setzen wirst.

Muss nicht perfekt sein. Muss nicht für immer sein.

Nur für heute."""
                    st.rerun()
            
            with col_ex2:
                if st.button("💔 No Contact erklärt", use_container_width=True):
                    st.session_state.subject_selected = "Was No Contact wirklich bedeutet"
                    st.session_state.preheader = "Es geht nicht um Bestrafung. Es geht um Atemraum."
                    st.session_state.newsletter_body = """No Contact wird oft falsch verstanden.

Es ist keine Strafe für die andere Person.

Es ist eine **Lebensader** für dich.

Stell dir vor, du hast eine tiefe Wunde. Ständig reißt jemand den Verband ab, um "mal nachzusehen".

Heilung ist unmöglich.

**No Contact ist der Verband.**

Er gibt dir den Raum, den du brauchst. Nicht für immer. Nur so lange, bis du wieder atmen kannst.

Kein Drama. Keine großen Erklärungen.

Einfach: Ich brauche Raum.

**Heutiger Schritt:** Wenn du in No Contact bist, schreibe auf, was sich seitdem verbessert hat.

Auch die kleinen Dinge zählen."""
                    st.rerun()
    
    else:
        st.subheader("2️⃣ Editor & Vorschau")
        
        if show_debug and st.session_state.debug_prompt:
            with st.expander("🔍 Debug-Prompt anzeigen"):
                st.text_area("Prompt", st.session_state.debug_prompt, height=200, label_visibility="collapsed")
        
        sections = extract_sections(st.session_state.newsletter_raw)
        subjects = sections["subjects"] or ([st.session_state.subject_selected] if st.session_state.subject_selected else [])
        
        # Subject Picker
        st.markdown("#### ✉️ Betreff auswählen")
        if subjects:
            chosen = st.selectbox(
                "Wähle einen Betreff",
                options=subjects,
                index=max(0, subjects.index(st.session_state.subject_selected)) if st.session_state.subject_selected in subjects else 0,
                help="Ideale Länge: 45-55 Zeichen"
            )
            st.session_state.subject_selected = chosen
            
            # A/B Testing Buttons
            if len(subjects) >= 2:
                col_ab1, col_ab2 = st.columns(2)
                with col_ab1:
                    st.button(f"🅰️ {subjects[0][:30]}...", 
                            use_container_width=True,
                            help="Als Variante A verwenden")
                with col_ab2:
                    if len(subjects) > 1:
                        st.button(f"🅱️ {subjects[1][:30]}...", 
                                use_container_width=True,
                                help="Als Variante B verwenden")
        else:
            st.warning("Keine Betreffzeilen gefunden")
            st.session_state.subject_selected = st.text_input("Betreff eingeben")
        
        # Preheader
        st.markdown("#### 📄 Preheader")
        preheader_input = st.text_input(
            "Preheader Text",
            value=st.session_state.preheader,
            help="Maximal 90 Zeichen, ergänzt den Betreff",
            max_chars=90
        )
        st.session_state.preheader = preheader_input
        
        # CTA Variants
        st.markdown("#### 🎯 CTA-Varianten")
        if st.session_state.cta_variants:
            st.markdown("".join([f'<span class="pill">{clamp_text(c, 60)}</span>' for c in st.session_state.cta_variants]), unsafe_allow_html=True)
            
            with st.expander("✏️ CTAs bearbeiten"):
                for i, cta in enumerate(st.session_state.cta_variants):
                    new_cta = st.text_input(f"CTA {i+1}", value=cta, key=f"cta_{i}")
                    st.session_state.cta_variants[i] = new_cta
                
                col_cta1, col_cta2 = st.columns(2)
                with col_cta1:
                    if st.button("➕ Neue CTA", use_container_width=True):
                        st.session_state.cta_variants.append("Neue CTA...")
                        st.rerun()
                with col_cta2:
                    if len(st.session_state.cta_variants) > 1:
                        if st.button("🗑️ Letzte löschen", use_container_width=True):
                            st.session_state.cta_variants.pop()
                            st.rerun()
        else:
            st.info("Noch keine CTAs vorhanden")
        
        # Body Editor
        st.markdown("#### ✍️ Newsletter-Text")
        
        # Editor Tools
        col_tools1, col_tools2, col_tools3 = st.columns(3)
        with col_tools1:
            if st.button("📏 Formatieren", use_container_width=True, help="Absätze bereinigen"):
                text = st.session_state.newsletter_body
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                st.session_state.newsletter_body = '\n\n'.join(paragraphs)
                st.rerun()
        
        with col_tools2:
            if st.button("📝 Wortzahl prüfen", use_container_width=True):
                word_count = count_words(st.session_state.newsletter_body)
                st.info(f"Aktuelle Wortzahl: {word_count} Wörter")
        
        with col_tools3:
            if st.button("🔍 Vorschau aktualisieren", use_container_width=True):
                st.rerun()
        
        # Text Area
        edited_body = st.text_area(
            "Text bearbeiten (Markdown unterstützt)",
            value=st.session_state.newsletter_body,
            height=350,
            help="Verwende **fett** für wichtige Stellen"
        )
        st.session_state.newsletter_body = edited_body
        
        # Quality Metrics
        word_count = count_words(st.session_state.newsletter_body)
        subject_len = len(st.session_state.subject_selected or "")
        pre_len = len(st.session_state.preheader or "")
        paragraphs = len([p for p in (st.session_state.newsletter_body or "").split("\n\n") if p.strip()])
        avg_words = word_count / max(paragraphs, 1)
        
        st.markdown("#### 📊 Qualitätsanalyse")
        
        # Responsive Metrics Grid
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
        
        with col_metrics1:
            st.metric("📝 Wörter", word_count)
        with col_metrics2:
            status_color = "🟢" if subject_len <= 45 else "🟡" if subject_len <= 55 else "🔴"
            st.metric("✉️ Betreff", f"{subject_len}/45", delta=status_color)
        with col_metrics3:
            status_color = "🟢" if pre_len <= 90 else "🔴"
            st.metric("📄 Preheader", f"{pre_len}/90", delta=status_color)
        with col_metrics4:
            st.metric("📑 Absätze", paragraphs)
        
        # Length Warning & Extend Button
        st.markdown("#### 🔧 Textlänge anpassen")
        
        if word_count < 250:
            st.warning(f"⚠️ Text ist sehr kurz ({word_count} Wörter). Für Newsletter empfehlen sich 250+ Wörter.")
            
            col_extend1, col_extend2 = st.columns([2, 1])
            with col_extend1:
                if st.button("📈 Text verlängern", 
                           type="primary", 
                           use_container_width=True,
                           help="Text um 30-50% verlängern mit mehr Tiefe"):
                    if api_key:
                        run_generation(extend=True)
                    else:
                        st.error("Bitte API Key eingeben")
            with col_extend2:
                if st.button("📉 Weitere kürzen", 
                           use_container_width=True,
                           help="Noch mehr kürzen"):
                    rewrite_kind = "Kürzer"
                    if api_key:
                        system = build_system_prompt()
                        user = rewrite_prompt(rewrite_kind, reader_state, tone_label, st.session_state.newsletter_body)
                        st.session_state.debug_prompt = f"SYSTEM:\n{system}\n\nUSER:\n{user}"
                        
                        with st.spinner("Kürze Text..."):
                            try:
                                raw = call_openai(api_key, model_choice, system, user, 0.5)
                                sections2 = extract_sections(raw)
                                if sections2["newsletter"]:
                                    st.session_state.newsletter_body = sections2["newsletter"]
                                    st.session_state.current_version += 1
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
        elif word_count > 900:
            st.info(f"ℹ️ Text ist lang ({word_count} Wörter). Gut für ausführliche Newsletter.")
        else:
            st.success(f"✅ Textlänge ist gut ({word_count} Wörter).")
            
            col_length1, col_length2 = st.columns(2)
            with col_length1:
                if st.button("📈 Text erweitern", 
                           use_container_width=True,
                           help="Mehr Tiefe und Beispiele hinzufügen"):
                    if api_key:
                        run_generation(extend=True)
                    else:
                        st.error("Bitte API Key eingeben")
            with col_length2:
                if st.button("📉 Text kürzen", 
                           use_container_width=True,
                           help="Auf das Wesentliche reduzieren"):
                    rewrite_kind = "Kürzer"
                    if api_key:
                        system = build_system_prompt()
                        user = rewrite_prompt(rewrite_kind, reader_state, tone_label, st.session_state.newsletter_body)
                        with st.spinner("Kürze Text..."):
                            try:
                                raw = call_openai(api_key, model_choice, system, user, 0.5)
                                sections2 = extract_sections(raw)
                                if sections2["newsletter"]:
                                    st.session_state.newsletter_body = sections2["newsletter"]
                                    st.session_state.current_version += 1
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
        
        # Preview
        st.markdown("#### 👁️ Vorschau")
        with st.container():
            st.markdown('<div class="preview-box">', unsafe_allow_html=True)
            
            st.markdown(f"**✉️ Betreff:** {st.session_state.subject_selected}")
            st.markdown(f"<span class='muted'><b>📄 Preheader:</b> {st.session_state.preheader}</span>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border: 1px solid #444; margin: 1rem 0;'>", unsafe_allow_html=True)
            
            st.markdown(st.session_state.newsletter_body)
            
            if st.session_state.cta_variants:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**🎯 Call-to-Action:**")
                for cta in st.session_state.cta_variants[:3]:
                    st.markdown(f"• {cta}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Rewrite Options
        st.markdown("#### 🛠️ Text optimieren")
        
        rewrite_options = {
            "📈 Verlängern": "Mehr Tiefe, Beispiele und Erklärungen",
            "📉 Kürzen": "Auf das Wesentliche reduzieren",
            "🎯 Direkter": "Klare, direkte Sprache",
            "💖 Sanfter": "Mehr Empathie und Wärme",
            "📖 Story": "Persönliche Geschichte einbauen",
            "💰 Conversion": "Verkauf optimieren",
            "🤝 Empathie": "Mehr Verständnis zeigen",
            "⚡ Actionable": "Mehr praktische Schritte"
        }
        
        # Responsive Button Grid
        cols = st.columns(4)
        rewrite_kind = None
        
        for i, (key, label) in enumerate(rewrite_options.items()):
            with cols[i % 4]:
                if st.button(key, use_container_width=True, help=label):
                    rewrite_kind = key.replace("📈 ", "").replace("📉 ", "").replace("🎯 ", "").replace("💖 ", "").replace("📖 ", "").replace("💰 ", "").replace("🤝 ", "").replace("⚡ ", "")
        
        if rewrite_kind:
            if not api_key:
                st.error("⚠️ Bitte API Key eingeben.")
            else:
                # Save to history
                version_data = {
                    "version": st.session_state.current_version,
                    "timestamp": datetime.now().isoformat(),
                    "action": f"Rewrite: {rewrite_kind}",
                    "topic": topic,
                    "raw": st.session_state.newsletter_raw,
                    "subject": st.session_state.subject_selected,
                    "preheader": st.session_state.preheader,
                    "body": st.session_state.newsletter_body,
                    "ctas": st.session_state.cta_variants,
                }
                add_to_history(version_data)
                
                system = build_system_prompt()
                user = rewrite_prompt(rewrite_kind, reader_state, tone_label, st.session_state.newsletter_body)
                
                with st.spinner(f"Optimiere: {rewrite_kind}..."):
                    try:
                        raw = call_openai(api_key, model_choice, system, user, 0.6)
                        st.session_state.newsletter_raw = raw
                        sections2 = extract_sections(raw)
                        if sections2["subjects"]:
                            st.session_state.subject_selected = sections2["subjects"][0]
                        if sections2["preheader"]:
                            st.session_state.preheader = sections2["preheader"]
                        if sections2["newsletter"]:
                            st.session_state.newsletter_body = sections2["newsletter"]
                        st.session_state.cta_variants = sections2["ctas"] or []
                        st.session_state.current_version += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Fehler: {e}")
        
        # Export
        st.markdown("#### 📦 Exportieren")
        
        export_text = textwrap.dedent(
            f"""
            BETREFF: {st.session_state.subject_selected}
            
            PREHEADER: {st.session_state.preheader}
            
            ---
            {st.session_state.newsletter_body}
            
            {'CTA_VARIANTEN:' + chr(10) + chr(10).join([f"- {c}" for c in st.session_state.cta_variants]) if st.session_state.cta_variants else ''}
            
            ---
            Generiert mit Raus aus dem Gift Newsletter Engine
            Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}
            Version: {st.session_state.current_version - 1}
            """
        ).strip()
        
        # JSON Export
        export_json = json.dumps({
            "subject": st.session_state.subject_selected,
            "preheader": st.session_state.preheader,
            "body": st.session_state.newsletter_body,
            "ctas": st.session_state.cta_variants,
            "word_count": word_count,
            "generated_at": datetime.now().isoformat(),
            "version": st.session_state.current_version - 1,
            "briefing": {
                "topic": topic,
                "reader_state": reader_state,
                "tone": tone_label,
                "mode": mode,
                "kpi": goal_kpi
            }
        }, indent=2, ensure_ascii=False)
        
        # HTML Export
        html_body = st.session_state.newsletter_body
        html_body = html_body.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_body)
        
        export_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{st.session_state.subject_selected}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #6A1B9A; padding-bottom: 10px; margin-bottom: 20px; }}
        .preheader {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .content {{ margin-bottom: 30px; }}
        .cta {{ background-color: #6A1B9A; color: white; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0; }}
        .footer {{ font-size: 12px; color: #999; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{st.session_state.subject_selected}</h1>
        <div class="preheader">{st.session_state.preheader}</div>
    </div>
    <div class="content">
        <p>{html_body}</p>
    </div>
    {f'<div class="cta">{st.session_state.cta_variants[0] if st.session_state.cta_variants else "Jetzt weiterlesen"}</div>' if st.session_state.cta_variants else ''}
    <div class="footer">
        Raus aus dem Gift Newsletter • {datetime.now().strftime('%d.%m.%Y')}
    </div>
</body>
</html>"""
        
        # Export Buttons Grid
        col_export1, col_export2, col_export3, col_export4 = st.columns(4)
        
        with col_export1:
            st.download_button(
                "📄 TXT herunterladen",
                export_text,
                file_name="newsletter.txt",
                use_container_width=True
            )
        
        with col_export2:
            st.download_button(
                "📝 Markdown herunterladen",
                export_text,
                file_name="newsletter.md",
                use_container_width=True
            )
        
        with col_export3:
            st.download_button(
                "🌐 HTML herunterladen",
                export_html,
                file_name="newsletter.html",
                use_container_width=True
            )
        
        with col_export4:
            st.download_button(
                "🔧 JSON herunterladen",
                export_json,
                file_name="newsletter.json",
                use_container_width=True
            )
        
        # Copy to Clipboard
        if st.button("📋 In Zwischenablage kopieren", use_container_width=True):
            st.code(export_text[:300] + "..." if len(export_text) > 300 else export_text)
            st.success("✅ Text bereit zum Kopieren (Strg+C)")
        
        st.caption(f"🔄 Version {st.session_state.current_version - 1} • 🔑 API: {st.session_state.api_source.upper()} • 🚀 Gestartet mit: `streamlit run generator.py`")

# =========================
# Responsive Footer
# =========================
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns([1, 2, 1])
with col_footer2:
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem; color: #888;">
        <small>
        🛡️ <strong>Raus aus dem Gift Newsletter Engine</strong> v2.0 • 
        Responsive Design • 
        Mit ❤️ für wirkungsvolle Kommunikation
        </small>
        </div>
        """,
        unsafe_allow_html=True
    )