import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach Magique d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; border: none; width: 100%; }
    .stChatMessage { border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# Connexion API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "attente_reponse" not in st.session_state: st.session_state.attente_reponse = False
if "file_uploader_key" not in st.session_state: st.session_state.file_uploader_key = 0

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Réglages")
    activer_ballons = st.toggle("Activer les ballons 🎈", value=True)
    if st.button("➕ Nouvelle Leçon / Reset"):
        # On vide tout et on change la clé de l'uploader pour effacer les fichiers
        st.session_state.clear()
        st.session_state.file_uploader_key += 1
        st.rerun()

# --- INTERFACE ---
st.title(f"✨ Le Coach d'Anaïs")
st.write(f"🚀 **Score : {st.session_state.xp} XP**")

# Utilisation d'une clé dynamique pour forcer la remise à zéro de l'uploader
fichiers = st.file_uploader("📸 Dépose tes photos de cours :", 
                            type=['jpg', 'jpeg', 'png'], 
                            accept_multiple_files=True,
                            key=f"uploader_{st.session_state.file_uploader_key}")

# --- LANCEMENT AUTOMATIQUE ---
if st.button("🚀 LANCER LE QUIZZ"):
    if not fichiers and st.session_state.cours_texte is None:
        st.warning("Ajoute une photo d'abord ! 📸")
    else:
        with st.spinner("Je prépare ta question..."):
            if st.session_state.cours_texte is None:
                photos = [Image.open(f).convert("RGB") for f in fichiers]
                for p in photos: p.thumbnail((1024, 1024))
                res_ocr = model.generate_content(["Extrais le texte de ces images."] + photos)
                st.session_state.cours_texte = res_ocr.text
            
            st.session_state.messages = []
            prompt = f"""Tu es un coach joyeux et enthousiaste ! Savoir : {st.session_state.cours_texte}.
            MISSION : Pose une question QCM courte.
            CONSIGNES :
            - Utilise un ton dynamique avec des points d'exclamation !
            - Ne cite JAMAIS le cours.
            - Saute DEUX lignes vides entre chaque option A, B et C."""
            res = model.generate_content(prompt)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
            st.session_state.attente_reponse = True
            st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "🌈" if msg["role"] == "assistant" else "⭐"
    with st.chat_message(msg["role"], avatar=avatar):
        c_txt, c_aud = st.columns([0.88, 0.12])
        with c_txt:
            st.markdown(msg["content"])
        with c_aud:
            if msg["role"] == "assistant":
                if st.button("🔊", key=f"audio_{i}"):
                    audio_text = msg["content"].replace("A)", "Choix A,").replace("B)", "Choix B,").replace("C)", "Choix C,")
                    tts = gTTS(text=audio_text, lang='fr', slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

# --- ZONE RÉPONSE ---
if st.session_state.attente_reponse:
    st.write("---")
    c1, c2, c3 = st.columns(3)
    choix = None
    if c1.button("A"): choix = "A"
    if c2.button("B"): choix = "B"
    if c3.button("C"): choix = "C"

    if choix:
        st.session_state.messages.append({"role": "user", "content": f"Choix {choix}"})
        st.session_state.attente_reponse = False
        with st.spinner("Vérification..."):
            prompt_v = f"""Savoir : {st.session_state.cours_texte}
            Question : {st.session_state.messages[-2]['content']}
            Réponse choisie : {choix}
            - Si juste : commence par 'BRAVO ! C'est super !'.
            - Si faux : commence par 'Oups ! Presque !'. Explique en 2 phrases MAX.
            - Pose ensuite une nouvelle question.
            - Saute UNE ligne entre chaque option A, B et C."""
            
            res = model.generate_content(prompt_v)
            txt = res.text
            
            if any(word in txt.upper()[:50] for word in ["BRAVO", "SUPER", "GÉNIAL"]):
                st.session_state.xp += 20
                if activer_ballons:
                    st.balloons()
            
            st.session_state.messages.append({"role": "assistant", "content": txt})
            st.session_state.attente_reponse = True
            
            st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)
            st.rerun()
