import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time
from google.api_core import exceptions

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS pour une interface douce et scannable
st.markdown("""
    <style>
    .fixed-score {
        position: fixed; top: 60px; right: 15px;
        background-color: #FF69B4; color: white;
        padding: 12px 20px; border-radius: 30px;
        font-weight: bold; z-index: 9999;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        border: 2px solid white;
    }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; }
    .question-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #FF69B4; }
    </style>
""", unsafe_allow_html=True)

# Connexion API sécurisée
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        system_instruction="Tu es le coach d'Anaïs (12 ans, TDAH). Ton ton est joyeux, encourageant et très simple. Tu ne poses qu'UNE question QCM à la fois. Utilise des emojis comme ✨, 🌈, 🚀."
    )
except:
    st.error("Clé API manquante ou invalide.")

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "recompense_prete" not in st.session_state: st.session_state.recompense_prete = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Réglages")
    max_q = st.slider("Nombre de questions :", 1, 20, 10)
    if st.button("🔄 Changer de cours / Reset"):
        st.session_state.clear()
        st.rerun()

st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Étape 1 : Prends ton cours")
    img_input = st.camera_input("Prends une photo bien nette !")
    if not img_input:
        img_input = st.file_uploader("Ou choisis une image", type=['jpg', 'jpeg', 'png'])

    if img_input and st.button("🚀 C'EST PARTI !"):
        try:
            with st.spinner("Je lis ton cours avec mes yeux de robot..."):
                img = Image.open(img_input).convert("RGB")
                img.thumbnail((1000, 1000)) # Réduction de l'image pour économiser les tokens
                res = model.generate_content(["Extrais le texte de ce cours de 6ème de façon simple.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except exceptions.ResourceExhausted:
            st.warning("Le coach fait une petite pause (limite API). Attends 30 secondes ! ☕")

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < max_q:
    # Génération auto de la première question
    if not st.session_state.messages:
        try:
            res = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose une première question QCM (A, B, C) joyeuse.")
            st.session_state.messages.append({"role": "assistant", "content": res.text})
        except: st.error("Oups, l'IA a eu un petit hoquet. Réessaie !")

    # Affichage
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"audio_{i}"):
                txt = msg["content"].replace("A)", "Choix A").replace("B)", "Choix B").replace("C)", "Choix C")
                tts = gTTS(text=txt, lang='fr', slow=False) # slow=False pour plus de peps
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

    # Réponse
    st.write(f"📊 Question {st.session_state.nb_q + 1} / {max_q}")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A", use_container_width=True): choix = "A"
    if c2.button("B", use_container_width=True): choix = "B"
    if c3.button("C", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_q += 1
        try:
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Anaïs a répondu {choix} à la question : {st.session_state.messages[-1]['content']}. Si c'est juste, dis 'BRAVO !' et donne 20 XP. Pose la question suivante."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.balloons()
                    st.session_state.xp += 20
                    if st.session_state.xp % 200 == 0:
                        st.session_state.recompense_prete = True
                
                st.session_state.messages.append({"role": "user", "content": f"Ma réponse : {choix}"})
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.rerun()
        except exceptions.ResourceExhausted:
            st.error("Le coach sature ! Attends un peu avant de cliquer. 😊")

# --- 3. RÉCOMPENSE & FIN ---
if st.session_state.recompense_prete:
    st.snow()
    st.success("### 🏆 PALIER ATTEINT ! 200 XP !")
    # Image d'animal mignon (le tag 'cute,animal' change à chaque fois)
    st.image(f"https://loremflickr.com/600/400/cute,animal?lock={st.session_state.xp}", caption="Tu es une véritable championne ! Voici ton cadeau !")
    if st.button("Continuer l'aventure 🚀"):
        st.session_state.recompense_prete = False
        st.rerun()

if st.session_state.nb_q >= max_q:
    st.info("🎯 Séance terminée ! Bravo pour ton travail Anaïs. On se voit pour le prochain cours ?")
