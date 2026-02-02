import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time
from google.api_core import exceptions

# --- STYLE & UI ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Header fixe avec Score + Barre */
    .fixed-ui {
        position: fixed; top: 50px; right: 15px; width: 160px;
        background: white; padding: 10px; border-radius: 20px;
        z-index: 9999; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 2px solid #FF69B4;
    }
    .xp-badge {
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 5px 15px; border-radius: 15px;
        font-weight: bold; margin-bottom: 5px; font-size: 1.1em;
    }
    /* Boutons A B C affinés */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 12px !important; height: 3em !important; 
        font-size: 1em !important; border: none !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0
if "ballons" not in st.session_state: st.session_state.ballons = False

# SIDEBAR
with st.sidebar:
    total_q = st.slider("Objectif", 1, 20, 10)
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# UI FIXE
progress_val = st.session_state.nb_q / total_q
st.markdown(f'''
    <div class="fixed-ui">
        <div class="xp-badge">🚀 {st.session_state.xp} XP</div>
    </div>
''', unsafe_allow_html=True)

st.title("✨ Le Coach d'Anaïs")

# --- 1. CHARGEMENT DU COURS ---
if not st.session_state.cours_texte:
    source = st.camera_input("📸 Prends ton cours")
    if not source:
        source = st.file_uploader("📂 Ou bibliothèque", type=['jpg', 'png'])

    if source and st.button("🚀 LANCER LE QUIZZ", use_container_width=True):
        try:
            with st.spinner("Lecture du cours... (Patiente 5s)"):
                img = Image.open(source).convert("RGB")
                img.thumbnail((500, 500)) # Compression forte pour éviter l'erreur
                
                # Instruction robuste
                prompt = "Tu es le coach d'Anaïs. Extrais le texte de cette image. Puis pose une première question QCM (A, B, C) avec des lignes vides."
                res = model.generate_content([prompt, img])
                
                st.session_state.cours_texte = res.text
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except Exception as e:
            st.warning("⚠️ L'IA est saturée. Je réessaie automatiquement dans 5 secondes...")
            time.sleep(5)
            st.rerun() # Auto-retry

# --- 2. LE QUIZZ (NOUVEAU EN HAUT) ---
elif st.session_state.nb_q < total_q:
    st.write(f"📊 Question {st.session_state.nb_q} / {total_q}")
    st.progress(progress_val)

    # Zone de réponse
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", key="btn_a"): rep = "A"
    if c2.button("B", key="btn_b"): rep = "B"
    if c3.button("C", key="btn_c"): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        try:
            with st.spinner("Vérification..."):
                prompt_v = f"Cours: {st.session_state.cours_texte}. Question: {st.session_state.messages[0]['content']}. Anaïs a répondu {rep}. Dis si c'est juste. Puis pose la question QCM suivante."
                res = model.generate_content(prompt_v)
                
                if any(w in res.text.upper() for w in ["BRAVO", "JUSTE", "CORRECT"]):
                    st.session_state.xp += 20
                    st.session_state.ballons = True
                
                st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {rep}"})
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except:
            st.error("Délai dépassé. Attends un instant...")
            time.sleep(3)

    if st.session_state.ballons:
        st.balloons()
        st.session_state.ballons = False

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊", key=f"v_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

if st.session_state.nb_q >= total_q:
    st.success(f"🏆 Bravo ! {st.session_state.xp} XP gagnés !")
