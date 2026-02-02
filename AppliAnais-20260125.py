import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
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

st.subheader(f"🚀 Score : {st.session_state.xp} XP")
st.title("✨ Le Coach d'Anaïs")

fichiers = st.file_uploader("📸 Photos du cours :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# --- LOGIQUE QUIZZ ---
if st.button("🚀 LANCER LE QUIZZ"):
    if fichiers or st.session_state.cours_texte:
        with st.spinner("Lecture du cours..."):
            if st.session_state.cours_texte is None:
                # OPTIMISATION TOKENS : Lecture unique
                imgs = [Image.open(f).convert("RGB") for f in fichiers]
                for img in imgs: img.thumbnail((1024, 1024))
                res = model.generate_content(["Extrais le texte de ces images.", *imgs])
                st.session_state.cours_texte = res.text
            
            prompt = f"""Tu es le coach d'Anaïs. Savoir : {st.session_state.cours_texte}.
            CONSIGNES :
            - Pose UNE SEULE question QCM.
            - Propose UNIQUEMENT 3 choix : A, B et C. JAMAIS de D.
            - Saute DEUX lignes vides entre chaque proposition pour Anaïs.
            - Ton joyeux et féminisé."""
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
    # Ancre invisible pour le scroll
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
            prompt_v = f"""Savoir : {st.session_state.cours_texte}. 
            Question : {st.session_state.messages[-2]['content']}. 
            Réponse d'Anaïs : {choix}.
            - Dis si c'est juste, explique courtement.
            - Pose une NOUVELLE question avec UNIQUEMENT 3 choix (A, B, C).
            - Saute DEUX lignes vides entre chaque proposition."""
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if any(word in txt.upper()[:30] for word in ["BRAVO", "CORRECT", "JUSTE"]):
                st.session_state.xp += 20
                # On tente quand même les ballons, au cas où !
                st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            # Tentative de scroll automatique par injection JS
            st.markdown('<script>document.getElementById("scroll-anchor").scrollIntoView({behavior: "smooth"});</script>', unsafe_allow_html=True)
            st.rerun()
