import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-score { position: fixed; top: 10px; right: 10px; background-color: #FF69B4; color: white; padding: 10px 20px; border-radius: 30px; font-weight: bold; z-index: 1000; }
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

st.markdown(f'<div class="fixed-score">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    if st.button("➕ Nouveau Cours"):
        st.session_state.clear()
        st.rerun()

st.title("✨ Le Coach d'Anaïs")
fichiers = st.file_uploader("📸 Photos du cours :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LANCER LE QUIZZ ---
if st.button("🚀 LANCER LE QUIZZ"):
    if fichiers or st.session_state.cours_texte:
        with st.spinner("Je prépare ta question..."):
            if not st.session_state.cours_texte:
                # OPTIMISATION TOKENS : Lecture unique des images
                imgs = [Image.open(f).convert("RGB") for f in fichiers]
                for img in imgs: img.thumbnail((1024, 1024))
                res = model.generate_content(["Extrais le texte de ces images.", *imgs])
                st.session_state.cours_texte = res.text
            
            prompt = f"Tu es le coach d'Anaïs. Savoir : {st.session_state.cours_texte}. Pose UNE question QCM courte. Structure : Question, puis Choix A, B et C bien séparés par 1 ligne vide."
            q = model.generate_content(prompt)
            st.session_state.messages = [{"role": "assistant", "content": q.text}]
            st.session_state.attente_reponse = True
            st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
        st.markdown(msg["content"])

# --- RÉPONSE ET SCROLL ---
if st.session_state.attente_reponse:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
        with st.spinner("Vérification..."):
            prompt_v = f"Savoir: {st.session_state.cours_texte}. Question: {st.session_state.messages[-2]['content']}. Réponse: {choix}. Dis OUI ou NON au début. Explique courtement et pose une NOUVELLE question QCM bien aérée."
            res = model.generate_content(prompt_v)
            txt = res.text
            
            # DÉCLENCHEMENT DES BALLONS
            if any(mot in txt.upper()[:15] for mot in ["OUI", "BRAVO", "CORRECT"]):
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            # SCROLL FORCÉ : Création d'un élément invisible en fin de page
            st.markdown('<div id="end"></div>', unsafe_allow_html=True)
            st.markdown('<script>document.getElementById("end").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
            st.rerun()

