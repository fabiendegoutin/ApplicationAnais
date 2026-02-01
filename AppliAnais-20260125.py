import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; border: none; width: 100%; }
    .stChatMessage { border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Réglages")
    activer_ballons = st.toggle("Activer les ballons 🎈", value=True)
    if st.button("➕ Nouvelle Leçon / Reset"):
        st.session_state.clear()
        st.rerun()

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **Score : {st.session_state.xp} XP**")

fichiers = st.file_uploader("📸 Dépose tes photos de cours :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LANCEMENT AUTOMATIQUE ---
if st.button("🚀 LANCER LE QUIZZ"):
    if not fichiers and st.session_state.cours_texte is None:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        with st.spinner("Je prépare ta question, Anaïs..."):
            if st.session_state.cours_texte is None:
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                for p in photos: p.thumbnail((1024, 1024))
                res_ocr = model.generate_content(["Extrais le texte de ces images."] + photos)
                st.session_state.cours_texte = res_ocr.text
            
            st.session_state.messages = []
            prompt = f"""Voici les faits : {st.session_state.cours_texte}.
            MISSION : Pose une SEULE question QCM courte à Anaïs.
            CONSIGNES :
            - Saute DEUX lignes vides entre la question et les choix.
            - Saute DEUX lignes vides entre chaque choix A, B et C pour qu'ils ne soient pas collés.
            - Ton joyeux et féminisé."""
            res = model.generate_content(prompt)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.attente_reponse = True
            st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        c_txt, c_aud = st.columns([0.88, 0.12])
        with c_txt:
            st.markdown(msg["content"])
        with c_aud:
            if msg["role"] == "assistant":
                if st.button("🔊", key=f"audio_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE RÉPONSE ---
if st.session_state.attente_reponse:
    # Élément d'ancrage pour le scroll
    st.markdown('<div id="fin-de-page"></div>', unsafe_allow_html=True)
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
        st.session_state.attente_reponse = False
        with st.spinner("Vérification..."):
            prompt_v = f"""Le savoir : {st.session_state.cours_texte}
            Question : {st.session_state.messages[-2]['content']}
            Réponse choisie : {choix}
            1. Si juste : commence par 'BRAVO'.
            2. Si faux : commence par 'ZUT'.
            3. Explique courtement et pose une NOUVELLE question.
            4. IMPORTANT : Saute DEUX lignes vides entre chaque choix A, B, C."""
            
            res = model.generate_content(prompt_v)
            txt = res.text
            
            # Détection de succès élargie pour les ballons
            if any(mot in txt.upper()[:50] for mot in ["BRAVO", "CORRECT", "GÉNIAL"]):
                st.session_state.xp += 20
                if activer_ballons:
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            
            # JavaScript pour forcer le scroll vers l'ancre
            st.markdown('<script>document.getElementById("fin-de-page").scrollIntoView();</script>', unsafe_allow_html=True)
            st.rerun()
