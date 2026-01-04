import streamlit as st
import openai
from datetime import datetime
import json

# Page Config
st.set_page_config(
    page_title="Newsletter Generator - Raus aus dem Gift",
    page_icon="💜",
    layout="wide"
)

# Custom CSS für feminines, beruhigendes Design
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f0f6 0%, #e8dff5 100%);
    }
    .stButton>button {
        background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        color: white;
        border-radius: 25px;
        padding: 15px 30px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 15px rgba(155, 89, 182, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(155, 89, 182, 0.4);
    }
    h1 {
        color: #8e44ad;
        font-family: 'Georgia', serif;
        text-align: center;
        padding: 20px 0;
    }
    h2, h3 {
        color: #9b59b6;
        font-family: 'Georgia', serif;
    }
    .stSelectbox, .stTextArea {
        background-color: white;
        border-radius: 10px;
    }
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #28a745;
        margin: 20px 0;
    }
    .header-option {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #9b59b6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# API Key aus Streamlit Secrets laden
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    api_key_loaded = True
except Exception as e:
    api_key = None
    api_key_loaded = False

# Header
st.markdown("# 💜 Newsletter Generator")
st.markdown("### *Raus aus dem Gift* - Deine Stimme für Heilung und Empowerment")
st.markdown("---")

# Sidebar für Informationen
with st.sidebar:
    st.markdown("### ⚙️ API Status")
    if api_key_loaded:
        st.success("✅ API Key erfolgreich geladen")
    else:
        st.error("❌ API Key nicht gefunden")
        st.info("""
        **So konfigurierst du deinen API Key:**
        
        1. Erstelle eine Datei `.streamlit/secrets.toml` im Projektordner
        2. Füge folgende Zeile hinzu:
        ```
        OPENAI_API_KEY = "dein-api-key-hier"
        ```
        3. Starte die App neu
        
        **Für Streamlit Cloud:**
        - Gehe zu App Settings → Secrets
        - Füge dort den API Key hinzu
        """)
    
    st.markdown("---")
    st.markdown("### 💡 Über diese App")
    st.info("Erstelle wirkungsvolle Newsletter für deine Community. Unterstütze Überlebende narzisstischen Missbrauchs mit authentischen, heilenden Inhalten.")

# Nur fortfahren wenn API Key vorhanden
if not api_key_loaded:
    st.warning("⚠️ Bitte konfiguriere zuerst deinen OpenAI API Key in den Streamlit Secrets (siehe Sidebar).")
    st.stop()

# Hauptkonfiguration
col1, col2 = st.columns(2)

with col1:
    newsletter_typ = st.selectbox(
        "📧 Newsletter-Typ",
        ["Community Newsletter", "Marketing Newsletter"],
        help="Community: Fokus auf Heilung & Unterstützung | Marketing: Fokus auf Angebote & Conversion"
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
            "Neustart nach Missbrauch"
        ]
    )

# Spezifische Unterthemen basierend auf Hauptthema
unterthemen_map = {
    "Narzisstischen Missbrauch erkennen": [
        "Red Flags früh erkennen",
        "Unterschied zwischen Narzissmus und NPD",
        "Love Bombing Phase verstehen",
        "Typische Täterstrategien"
    ],
    "Heilung und Recovery": [
        "Erste Schritte nach dem Ausstieg",
        "Umgang mit Trauma-Triggern",
        "Selbstfürsorge-Rituale",
        "Professionelle Hilfe finden"
    ],
    "No Contact / Grauer Fels": [
        "No Contact durchhalten",
        "Grauer Fels bei Co-Parenting",
        "Rückfälle vermeiden",
        "Flying Monkeys abwehren"
    ],
    "Selbstwert aufbauen": [
        "Negative Glaubenssätze auflösen",
        "Selbstliebe praktizieren",
        "Eigene Bedürfnisse entdecken",
        "Selbstvertrauen stärken"
    ],
    "Trauma verstehen": [
        "Komplexe PTBS erkennen",
        "Körperliche Trauma-Reaktionen",
        "Trauma und Nervensystem",
        "Disassoziation verstehen"
    ],
    "Toxische Beziehungsmuster": [
        "Traumabonding durchbrechen",
        "Co-Abhängigkeit heilen",
        "Wiederholungsmuster erkennen",
        "Gesunde Beziehungen lernen"
    ],
    "Innere Kind-Arbeit": [
        "Das verletzte innere Kind",
        "Reparenting Techniken",
        "Emotionale Bedürfnisse erfüllen",
        "Heilung durch Selbstmitgefühl"
    ],
    "Grenzen setzen lernen": [
        "Nein sagen ohne Schuldgefühle",
        "Gesunde Grenzen kommunizieren",
        "Grenzverletzungen erkennen",
        "Konsequenzen durchsetzen"
    ],
    "Gaslighting und Manipulation": [
        "Gaslighting-Taktiken entlarven",
        "Realität vs. Manipulation",
        "Mentale Klarheit zurückgewinnen",
        "Dokumentation als Schutz"
    ],
    "Neustart nach Missbrauch": [
        "Identität wiederfinden",
        "Neue Lebensziele setzen",
        "Finanzieller Neuanfang",
        "Soziales Netzwerk aufbauen"
    ]
}

spezifisches_thema = st.selectbox(
    "🔍 Spezifisches Thema",
    unterthemen_map.get(haupt_thema, ["Allgemein"])
)

# Zusätzliche Parameter
col3, col4 = st.columns(2)

with col3:
    zielgruppe = st.selectbox(
        "👥 Hauptzielgruppe",
        [
            "Frauen in akuter Missbrauchssituation",
            "Frauen kurz nach Trennung",
            "Frauen im Heilungsprozess",
            "Frauen die Rückfälle vermeiden wollen",
            "Angehörige und Unterstützer"
        ]
    )

with col4:
    ton = st.selectbox(
        "💬 Tonalität",
        [
            "Einfühlsam & unterstützend",
            "Empowernd & motivierend",
            "Aufklärend & informativ",
            "Ermutigend & hoffnungsvoll",
            "Validierend & verstehend"
        ]
    )

# CTA Fokus
if newsletter_typ == "Marketing Newsletter":
    cta_fokus = st.selectbox(
        "🎯 Call-to-Action Fokus",
        [
            "Kostenfreies Erstgespräch buchen",
            "Online-Kurs anmelden",
            "Coaching-Programm",
            "Community beitreten",
            "E-Book Download",
            "Webinar Anmeldung"
        ]
    )
else:
    cta_fokus = "Community-Engagement"

# Zusätzliche Notizen
zusatz_info = st.text_area(
    "📝 Zusätzliche Informationen (optional)",
    placeholder="z.B. spezielle Inhalte, aktuelle Ereignisse, persönliche Stories die eingebunden werden sollen...",
    height=100
)

# Generate Button
st.markdown("---")
if st.button("✨ Newsletter generieren", use_container_width=True):
    with st.spinner("💜 Dein Newsletter wird erstellt... Dies kann einen Moment dauern."):
        try:
            # OpenAI Client initialisieren
            client = openai.OpenAI(api_key=api_key)
            
            # Prompt für Newsletter-Erstellung
            newsletter_prompt = f"""
Du bist eine einfühlsame Content-Spezialistin für die Brand "Raus aus dem Gift", die Opfer narzisstischen Missbrauchs unterstützt.

Erstelle einen {newsletter_typ} mit folgenden Parametern:
- Hauptthema: {haupt_thema}
- Spezifisches Thema: {spezifisches_thema}
- Zielgruppe: {zielgruppe}
- Tonalität: {ton}
- CTA Fokus: {cta_fokus}
- Zusätzliche Infos: {zusatz_info if zusatz_info else 'Keine'}

Der Newsletter soll:
1. Authentisch und traumasensibel sein
2. Validierung und Hoffnung vermitteln
3. Praktische Schritte oder Erkenntnisse bieten
4. Die Leserin empowern
5. Ca. 300-500 Wörter umfassen

Strukturiere den Newsletter mit:
- Persönlicher Ansprache
- Einleitung (Problem/Situation benennen)
- Hauptteil (Wissen, Erkenntnisse, Strategien)
- Ermutigung und Hoffnung
- Klarer Call-to-Action

Schreibe auf Deutsch, authentisch und mit Herz.
"""

            # Newsletter generieren
            newsletter_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist eine einfühlsame Content-Spezialistin für Trauma-Heilung und Empowerment von Frauen nach narzisstischem Missbrauch."},
                    {"role": "user", "content": newsletter_prompt}
                ],
                temperature=0.7
            )
            
            newsletter_content = newsletter_response.choices[0].message.content
            
            # Prompt für Header und Pre-Header
            header_prompt = f"""
Erstelle 5 virale, aufmerksamkeitsstarke Header-Varianten und passende Pre-Header für folgenden Newsletter:

Thema: {haupt_thema} - {spezifisches_thema}
Typ: {newsletter_typ}
Zielgruppe: {zielgruppe}

Die Header sollen:
- Emotional ansprechen ohne zu triggern
- Neugier wecken
- Hoffnung vermitteln
- Authentisch und nicht manipulativ sein
- Maximal 60 Zeichen haben

Die Pre-Header sollen:
- Den Header ergänzen
- Einen Benefit oder Insight andeuten
- Maximal 90 Zeichen haben

Format:
Header 1: [Text]
Pre-Header 1: [Text]

[Wiederhole für 2-5]
"""

            header_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist eine Expertin für E-Mail-Marketing im Bereich Trauma-Heilung und Empowerment."},
                    {"role": "user", "content": header_prompt}
                ],
                temperature=0.8
            )
            
            headers_content = header_response.choices[0].message.content
            
            # Ergebnisse anzeigen
            st.success("✅ Newsletter erfolgreich erstellt!")
            
            # Header Optionen
            st.markdown("## 📬 Header & Pre-Header Vorschläge")
            st.markdown('<div class="header-option">', unsafe_allow_html=True)
            st.markdown(headers_content)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Newsletter Content
            st.markdown("## ✍️ Newsletter-Inhalt")
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(newsletter_content)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download Optionen
            st.markdown("---")
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                full_content = f"""
HEADER & PRE-HEADER OPTIONEN:
{headers_content}

---

NEWSLETTER INHALT:
{newsletter_content}

---
Generiert am: {datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")}
Konfiguration:
- Typ: {newsletter_typ}
- Hauptthema: {haupt_thema}
- Spezifisches Thema: {spezifisches_thema}
- Zielgruppe: {zielgruppe}
- Tonalität: {ton}
"""
                st.download_button(
                    label="💾 Als Text-Datei speichern",
                    data=full_content,
                    file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
            
            with col_dl2:
                st.download_button(
                    label="📋 Als JSON speichern",
                    data=json.dumps({
                        "typ": newsletter_typ,
                        "haupt_thema": haupt_thema,
                        "spezifisches_thema": spezifisches_thema,
                        "zielgruppe": zielgruppe,
                        "ton": ton,
                        "cta_fokus": cta_fokus,
                        "headers": headers_content,
                        "content": newsletter_content,
                        "generiert_am": datetime.now().isoformat()
                    }, indent=2, ensure_ascii=False),
                    file_name=f"newsletter_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"❌ Fehler bei der Newsletter-Erstellung: {str(e)}")
            st.info("Bitte überprüfe deinen API Key und stelle sicher, dass du Zugriff auf GPT-4 hast.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9b59b6; padding: 20px;'>
    <p>💜 Erstellt mit Liebe für die "Raus aus dem Gift" Community</p>
    <p style='font-size: 0.9em;'>Jeder Newsletter ist ein Schritt zur Heilung und Empowerment</p>
</div>
""", unsafe_allow_html=True)
