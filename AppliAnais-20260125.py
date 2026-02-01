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

# --- PARAMÈTRES (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Options")
    prenom = st.text_input("Prénom :", value="Anaïs")
    activer_ballons = st.toggle("Activer les ballons 🎈", value=True)
    if st.button("🗑️ Effacer le cours"):
        st.session_state.cours_texte = None
        st.session_state.messages = []
        st.rerun()

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **Score : {st.session_state.xp} XP**")

fichiers = st.file_uploader("📸 Photos de la leçon :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LOGIQUE : EXTRACTION UNIQUE (ÉCONOMIE DE TOKENS) ---
if fichiers and st.session_state.cours_texte is None:
    if st.button("🧠 Mémoriser le cours"):
        with st.spinner("Analyse des images (une seule fois)..."):
            photos = [Image.open(f).convert("RGB") for f in fichiers]
            for p in photos: p.thumbnail((1024, 1024))
            # On demande à l'IA d'extraire tout le texte
            res = model.generate_content(["Extrais tout le texte de ces images. Sois très complet.", photos])
            st.session_state.cours_texte = res.text
            st.success("✅ Cours mémorisé ! Tu peux ranger tes photos.")

# --- BOUTON DE JEU ---
if st.button("🚀 LANCER UNE QUESTION"):
    if st.session_state.cours_texte is None:
        st.warning("Mémorise d'abord ton cours ! 🧠")
    else:
        st.session_state.messages = []
        # On envoie le texte extrait au lieu des images (ÉCONOMIE)
        prompt = f"Cours : {st.session_state.cours_texte}. Pose une question QCM courte (A, B, C) l'une sous l'autre."
        res = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.session_state.attente_reponse = True
        st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- RÉPONSES ---
if st.session_state.attente_reponse:
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
            # On travaille uniquement sur le texte pour économiser les tokens
            prompt_v = f"""Cours : {st.session_state.cours_texte}
            Question : {st.session_state.messages[-2]['content']}
            Réponse choisie : {choix}
            Si juste, commence par 'BRAVO'. Si faux, commence par 'ZUT' et explique. 
            Pose ensuite une nouvelle question QCM (A, B, C) l'une sous l'autre."""
            
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if txt.strip().startswith("BRAVO"):
                st.session_state.xp += 20
                if activer_ballons: # Option ballons
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            st.rerun()
