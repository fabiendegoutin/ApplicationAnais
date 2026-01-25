import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration large pour mobile
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Design des boutons pour les doigts d'un enfant
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; background-color: #FFC107; color: black; border: none; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# Connexion sécurisée
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- PERSISTENCE DES DONNÉES ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []

# --- INTERFACE ---
st.title("🌟 Mon Coach Magique")
st.write(f"### ⭐ Score : {st.session_state.xp} XP")

# Zone de capture ultra-simple
st.write("---")
st.write("📸 **Étape 1 : Prends tes photos (une par une ou toutes ensemble)**")
fichiers = st.file_uploader("", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True, key="uploader")

if fichiers:
    # On sauvegarde immédiatement les photos dans un état permanent
    nouvelles_photos = []
    for f in fichiers:
        img = Image.open(f)
        # On force la rotation et le format pour éviter les images noires sur mobile
        img = img.convert("RGB")
        img.thumbnail((1024, 1024)) # Poids plume pour le réseau mobile
        nouvelles_photos.append(img)
    st.session_state.stock_photos = nouvelles_photos
    st.success(f"✅ {len(st.session_state.stock_photos)} page(s) enregistrée(s) !")

# Bouton de lancement
if st.session_state.stock_photos:
    if st.button("🚀 LANCER LE DÉFI MAINTENANT"):
        st.session_state.messages = [] # Reset du chat
        with st.spinner("J'analyse tes leçons..."):
            try:
                prompt = "Tu es le coach scolaire d'Anaïs (6ème). Analyse ces photos de cours. Pose la 1ère question en QCM (A, B ou C). Saute une ligne entre les choix et sois super encourageant !"
                # On envoie le texte ET les photos stockées
                response = model.generate_content([prompt] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- ZONE DE CHAT ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar=("👤" if msg["role"] == "user" else "🌟")):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# Réponse d'Anaïs
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    reponse = st.chat_input("Ta réponse (A, B ou C)...")
    if reponse:
        st.session_state.messages.append({"role": "user", "content": reponse})
        with st.spinner("Vérification..."):
            try:
                instruction = f"Anaïs a répondu '{reponse}'. Vérifie sur les photos. Félicite-la et pose la question suivante."
                res = model.generate_content([instruction] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                
                if any(w in res.text.lower() for w in ["bravo", "juste", "super"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
            except Exception as e:
                st.error(f"Oups : {e}")
