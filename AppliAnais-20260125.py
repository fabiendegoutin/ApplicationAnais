import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# CSS pour le score rose fixe et l'interface
st.markdown("""
    <style>
    .fixed-score {
        position: fixed; top: 10px; right: 10px;
        background-color: #FF69B4; color: white;
        padding: 10px 20px; border-radius: 30px;
        font-weight: bold; z-index: 1000;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; width: 100%; }
    /* Couleurs des boutons A, B, C */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
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
if "file_key" not in st.session_state: st.session_state.file_key = 0

# Score toujours visible
st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Réglages")
    if st.button("➕ Nouveau cours (Reset)"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.title("✨ Le Coach d'Anaïs")

# Uploader
fichiers = st.file_uploader("📸 Dépose tes photos de cours :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True, key=f"up_{st.session_state.file_key}")

# --- LOGIQUE QUIZZ ---
if st.button("🚀 LANCER LE QUIZZ"):
    if not fichiers and st.session_state.cours_texte is None:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        with st.spinner("Anaïs, je prépare ta question..."):
            if st.session_state.cours_texte is None:
                # OPTIMISATION TOKENS : Lecture unique des images
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                for p in photos: p.thumbnail((1024, 1024))
                res_ocr = model.generate_content(["Extrais le texte de ce cours.", *photos])
                st.session_state.cours_texte = res_ocr.text
            
            # PROMPT STRICT : Une seule question QCM
            prompt = f"""Tu es le coach d'Anaïs. Savoir : {st.session_state.cours_texte}.
            CONSIGNES :
            - Pose UNE SEULE question QCM courte.
            - Propose obligatoirement 3 choix : A, B et C.
            - Saute DEUX lignes entre chaque choix.
            - Ton joyeux et féminisé."""
            res = model.generate_content(prompt)
            st.session_state.messages = [{"role": "assistant", "content": res.text}]
            st.session_state.attente_reponse = True
            st.rerun()

# --- AFFICHAGE ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"].replace("A)", "Choix A,"), lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE RÉPONSE AVEC SCROLL ---
if st.session_state.attente_reponse:
    st.write("---")
    # Ancre pour le scroll automatique
    st.markdown('<div id="reponse"></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
        with st.spinner("Vérification..."):
            prompt_v = f"""Savoir : {st.session_state.cours_texte}.
            Question : {st.session_state.messages[-2]['content']}.
            Réponse : {choix}.
            - Commence par 'CORRECT' ou 'INCORRECT'.
            - Explique courtement.
            - Pose UNE nouvelle question QCM (3 choix A, B, C)."""
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if "CORRECT" in txt.upper()[:15]:
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            # Force le scroll vers l'ancre "reponse"
            st.markdown('<script>document.getElementById("reponse").scrollIntoView();</script>', unsafe_allow_html=True)
            st.rerun()
