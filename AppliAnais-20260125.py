import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration pour mobile
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Style CSS pour l'interface
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; background-color: #FFC107; color: black; border: none; font-weight: bold; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    </style>
""", unsafe_allow_html=True)

# Configuration de l'API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Sélection du modèle parmi ceux disponibles dans votre liste
# On choisit le 2.0-flash pour sa rapidité et sa stabilité
MODEL_NAME = 'models/gemini-2.0-flash'
model = genai.GenerativeModel(MODEL_NAME)

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []

# --- INTERFACE ---
st.title("🌟 Mon Coach Magique")
st.subheader(f"⭐ Score d'Anaïs : {st.session_state.xp} XP")

st.write("---")
fichiers = st.file_uploader("📸 Prends tes leçons en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if fichiers:
    photos_traitees = []
    for f in fichiers:
        img = Image.open(f).convert("RGB")
        img.thumbnail((1024, 1024))
        photos_traitees.append(img)
    st.session_state.stock_photos = photos_traitees
    st.success(f"✅ {len(st.session_state.stock_photos)} page(s) prête(s) !")

# Boutons d'action
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("🚀 LANCER LE QUIZ"):
        st.session_state.messages = []
        with st.spinner("Analyse de tes cours en cours..."):
            try:
                prompt = "Tu es le coach d'Anaïs (6ème, TDAH). Analyse ces photos. Pose une seule question QCM (A, B ou C). Sois super encourageant !"
                response = model.generate_content([prompt] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur avec le modèle {MODEL_NAME} : {e}")

with col_btn2:
    if st.button("🏁 VOIR MON RÉSUMÉ"):
        st.balloons()
        st.info(f"### 🎉 Bravo Anaïs !\nTu as terminé avec **{st.session_state.xp} XP** !")
        if st.button("Recommencer"):
            st.session_state.xp = 0
            st.session_state.messages = []
            st.rerun()

# --- CHAT ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar=("👤" if msg["role"] == "user" else "🌟")):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.button("🔊 Écouter", key=f"audio_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)

# Réponse d'Anaïs
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    reponse = st.chat_input("Ta réponse (A, B ou C)...")
    if reponse:
        st.session_state.messages.append({"role": "user", "content": reponse})
        with st.spinner("Vérification..."):
            try:
                instruction = (
                    f"Anaïs a répondu '{reponse}'. Vérifie sur les photos. "
                    "Si c'est juste : félicite-la (+20 XP). "
                    "Si c'est faux : donne la bonne réponse gentiment et explique-la simplement. "
                    "Puis pose la question suivante."
                )
                res = model.generate_content([instruction] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                
                if any(w in res.text.lower() for w in ["bravo", "juste", "super", "exact", "correct"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
            except Exception as e:
                st.error(f"Oups : {e}")
