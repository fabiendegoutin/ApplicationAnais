import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : BOUTONS AFFINÉS ET INTERFACE CLAIRE
st.markdown("""
    <style>
    .fixed-score {
        position: fixed; top: 70px; right: 20px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px 22px; border-radius: 50px;
        font-weight: 800; z-index: 9999;
        box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
        border: 2px solid white;
    }
    /* Taille des boutons de réponse réduite */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important;
        height: 3.5em !important; 
        font-size: 1.1em !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    /* Couleurs des boutons */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API avec cadrage strict
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name='models/gemini-2.0-flash',
    system_instruction="""Tu es le coach d'Anaïs (6ème). 
    Tu dois TOUJOURS poser des questions en format QCM avec 3 options : A, B et C.
    IMPORTANT : Saute une ligne entre chaque proposition de réponse pour que ce soit très lisible.
    Ne pose jamais de question ouverte."""
)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

# Sidebar
with st.sidebar:
    st.header("⚙️ Paramètres")
    total_q = st.slider("Nombre de questions", 1, 20, 10)
    if st.button("🔄 Nouveau Quizz"):
        st.session_state.clear()
        st.rerun()

st.markdown(f'<div class="fixed-score">⚡ {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. CHARGEMENT ---
if not st.session_state.cours_texte:
    img_cam = st.camera_input("📸 Prends ton cours")
    img_file = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])
    photo = img_cam if img_cam else img_file

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        with st.spinner("Lecture du cours..."):
            img = Image.open(photo).convert("RGB")
            img.thumbnail((1024, 1024))
            res = model.generate_content(["Extrais le texte de ce cours.", img])
            st.session_state.cours_texte = res.text
            # Première question forcée en QCM
            q = model.generate_content(f"Cours: {st.session_state.cours_texte}. Pose la 1ère question QCM (A, B, C) avec une ligne vide entre chaque choix.")
            st.session_state.messages.append({"role": "assistant", "content": q.text})
            st.rerun()

# --- 2. QUIZZ ---
elif st.session_state.nb_q < total_q:
    st.progress(st.session_state.nb_q / total_q, text=f"Question {st.session_state.nb_q}/{total_q}")

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊 Écouter", key=f"snd_{i}"):
                clean = msg["content"].replace("A)", "Choix A,").replace("B)", "Choix B,").replace("C)", "Choix C,")
                tts = gTTS(text=clean, lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

    # Boutons de réponse affinés
    if st.session_state.messages[-1]["role"] == "assistant":
        st.write("---")
        c1, c2, c3 = st.columns(3)
        choix = None
        if c1.button("A", use_container_width=True): choix = "A"
        if c2.button("B", use_container_width=True): choix = "B"
        if c3.button("C", use_container_width=True): choix = "C"

        if choix:
            st.session_state.nb_q += 1
            with st.spinner("Vérification..."):
                prompt = f"Cours: {st.session_state.cours_texte}. Anaïs a répondu {choix}. Juste ou Faux ? Si juste, dis BRAVO. Pose la question QCM suivante avec une ligne vide entre chaque choix (A, B, C)."
                res = model.generate_content(prompt)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.balloons()
                    st.session_state.xp += 20
                
                st.session_state.messages.append({"role": "user", "content": f"Je choisis la {choix}"})
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.rerun()

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Bravo Anaïs ! Tu as fini avec {st.session_state.xp} XP !")
