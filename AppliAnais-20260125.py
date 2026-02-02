import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS : BADGE ROSE FIXE ET BOUTONS COLORÉS
st.markdown("""
    <style>
    .fixed-score {
        position: fixed;
        top: 60px;
        right: 15px;
        background-color: #FF69B4;
        color: white;
        padding: 12px 20px;
        border-radius: 30px;
        font-weight: bold;
        z-index: 9999;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        border: 2px solid white;
        font-size: 1.2em;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False

# AFFICHAGE DU SCORE ROSE FIXE
st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# Uploader pour photos
fichiers = st.file_uploader("📸 Prends ton cours en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LOGIQUE QUIZZ ---
if st.button("🚀 LANCER LE QUIZZ"):
    if fichiers or st.session_state.cours_texte:
        with st.spinner("Je prépare tes questions de 6ème..."):
            if not st.session_state.cours_texte:
                imgs = [Image.open(f).convert("RGB") for f in fichiers]
                for img in imgs: img.thumbnail((1024, 1024))
                res = model.generate_content(["Extrais le texte de ces images.", *imgs])
                st.session_state.cours_texte = res.text
            
            prompt = f"""Tu es le coach d'Anaïs, élève de 6ème. Savoir : {st.session_state.cours_texte}.
            CONSIGNES :
            - Vocabulaire simple.
            - UNE question QCM (A, B, C).
            - Saute 2 lignes entre chaque choix."""
            q = model.generate_content(prompt)
            st.session_state.messages = [{"role": "assistant", "content": q.text}]
            st.session_state.attente_reponse = True
            st.rerun()

# --- CHAT AVEC AUDIO RÉPÉTABLE ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
        col_text, col_audio = st.columns([0.85, 0.15])
        with col_text:
            st.markdown(msg["content"])
        with col_audio:
            if msg["role"] == "assistant":
                # Bouton audio qui peut être cliqué plusieurs fois
                if st.button("🔊", key=f"audio_btn_{i}"):
                    clean_text = msg["content"].replace("A)", "Choix A,").replace("B)", "Choix B,").replace("C)", "Choix C,")
                    tts = gTTS(text=clean_text, lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# --- RÉPONSE ---
if st.session_state.attente_reponse:
    st.markdown('<div id="scroll-anchor"></div>', unsafe_allow_html=True)
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
        with st.spinner("Vérification..."):
            prompt_v = f"""Savoir : {st.session_state.cours_texte}. Question : {st.session_state.messages[-2]['content']}. Réponse : {choix}.
            Dis 'Ta réponse est juste' ou 'Ta réponse est incorrecte'. Niveau 6ème.
            Pose une NOUVELLE question QCM (A, B, C uniquement) bien aérée."""
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if any(w in txt.upper()[:30] for w in ["JUSTE", "BRAVO", "CORRECT"]):
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.markdown('<script>document.getElementById("scroll-anchor").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
            st.rerun()
