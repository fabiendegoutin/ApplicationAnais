import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- STYLE & UI ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 150px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px; border-radius: 20px;
        z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 2px solid white;
    }
    .stProgress > div > div > div > div { background-color: #FFD700 !important; }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

# UI Fixe : XP + Barre de progression juste en dessous
with st.container():
    st.markdown(f'''
        <div class="fixed-header">
            🚀 {st.session_state.xp} XP<br>
            <small>Objectif 200</small>
        </div>
    ''', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- RÉCOMPENSE 200 XP ---
if st.session_state.xp >= 200:
    st.success("🌟 INCROYABLE ! Tu as atteint 200 XP !")
    st.image("https://img.freepik.com/vecteurs-premium/embleme-medaille-or-laurier-insigne-champion-trophee-recompense_548887-133.jpg", width=200)

# --- 1. CHARGEMENT ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((600, 600))
                res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < 10:
    # Barre de progression globale en haut de la zone de jeu
    st.write(f"Avancement de la séance : {st.session_state.nb_q}/10")
    st.progress(st.session_state.nb_q / 10)

    if not st.session_state.messages:
        prompt_init = (f"Cours : {st.session_state.cours_texte}. Pose un QCM (A, B, C). "
                      "NE DIS JAMAIS 'selon le texte'. Mets CHAQUE choix à la ligne.")
        q = model.generate_content(prompt_init)
        st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
        st.rerun()

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            prompt_v = (f"Cours : {st.session_state.cours_texte}. Réponse d'Anaïs : {rep}. "
                       "Dis si c'est juste, puis pose la question suivante (SANS 'selon le texte' "
                       "et avec les choix à la ligne).")
            res = model.generate_content(prompt_v)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.session_state.xp += 20
                st.balloons()
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            if msg["role"] == "assistant":
                col_audio, col_text = st.columns([0.15, 0.85])
                with col_audio:
                    if st.button("🔊", key=f"v_{i}"):
                        tts = gTTS(text=msg["content"], lang='fr')
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format="audio/mp3", autoplay=True)
                with col_text:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
