import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : Interface colorée et animations
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
    .stButton>button { border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="Tu es le coach d'Anaïs (6ème, TDAH). Tu es encourageant, tu fais des phrases courtes et tu utilises beaucoup d'émoticônes. Ton but est la confiance en soi."
)

# --- INITIALISATION DES VARIABLES ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False
if "nb_questions_posees" not in st.session_state: st.session_state.nb_questions_posees = 0
if "image_debloquee" not in st.session_state: st.session_state.image_debloquee = False

# --- BARRE LATÉRALE (RÉGLAGES) ---
with st.sidebar:
    st.header("⚙️ Réglages")
    max_questions = st.slider("Nombre de questions :", 1, 20, 10)
    if st.button("🗑️ Réinitialiser tout"):
        st.session_state.clear()
        st.rerun()

# Affichage XP
st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- CAPTURE DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Étape 1 : Envoie ton cours")
    photo = st.camera_input("Prends ton cours en photo")
    if not photo:
        photo = st.file_uploader("Ou choisis une image", type=['jpg', 'png'])

    if photo and st.button("🚀 PRÉPARER LE QUIZZ"):
        with st.spinner("Lecture du cours..."):
            img = Image.open(photo).convert("RGB")
            res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
            st.session_state.cours_texte = res.text
            st.success("Cours chargé ! Clique à nouveau pour commencer.")
            st.rerun()

# --- LOGIQUE DU QUIZZ ---
if st.session_state.cours_texte and st.session_state.nb_questions_posees < max_questions:
    if not st.session_state.messages: # Première question
        prompt = f"Basé sur ce cours : {st.session_state.cours_texte}. Pose une première question QCM (A, B, C) simple."
        res = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.session_state.attente_reponse = True

# --- AFFICHAGE DES MESSAGES ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"snd_{i}"):
            tts = gTTS(text=msg["content"], lang='fr')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE DE RÉPONSE ---
if st.session_state.attente_reponse and st.session_state.nb_questions_posees < max_questions:
    st.write(f"Question {st.session_state.nb_questions_posees + 1} / {max_questions}")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A", use_container_width=True): choix = "A"
    if c2.button("B", use_container_width=True): choix = "B"
    if c3.button("C", use_container_width=True): choix = "C"

    if choix:
        st.session_state.nb_questions_posees += 1
        with st.spinner("Vérification..."):
            prompt_v = f"Le cours : {st.session_state.cours_texte}. Question : {st.session_state.messages[-1]['content']}. Réponse choisie : {choix}. Dis si c'est juste ou faux, puis pose la question suivante ou dis que c'est fini."
            res = model.generate_content(prompt_v)
            
            # Gestion XP et Ballons
            if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                st.session_state.xp += 20
                st.balloons()
                
                # Vérification du palier de 200 XP
                if st.session_state.xp >= 200 and not st.session_state.image_debloquee:
                    st.session_state.image_debloquee = True
                    st.snow() # Effet spécial supplémentaire
            
            st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            time.sleep(1)
            st.rerun()

# --- RÉCOMPENSE ---
if st.session_state.image_debloquee:
    st.success("### 🏆 BRAVO ANAÏS ! TU AS ATTEINT 200 XP !")
    st.write("Tu as débloqué un cadeau magique !")
    st.image("https://loremflickr.com/600/400/cute,animal", caption="Voici ton animal totem pour fêter ta réussite !")
    if st.button("Continuer pour le prochain palier"):
        st.session_state.image_debloquee = False # On réinitialise pour le prochain palier de 200
        st.rerun()

if st.session_state.nb_questions_posees >= max_questions:
    st.info("🎯 Quiz terminé ! Bravo pour tes efforts aujourd'hui.")
