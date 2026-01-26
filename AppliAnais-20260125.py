import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# Configuration pour mobile
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Design adapté (gros boutons et couleurs vives)
st.markdown("""
    <style>
    .stButton>button { border-radius: 20px; height: 3.5em; font-size: 1.2rem !important; width: 100%; background-color: #FFC107; color: black; border: none; font-weight: bold; }
    .stChatMessage { border-radius: 15px; font-size: 1.1rem; border: 1px solid #E0E0E0; }
    .stAlert { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# Connexion à l'API
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- INITIALISATION ---
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "stock_photos" not in st.session_state: st.session_state.stock_photos = []
if "questions_count" not in st.session_state: st.session_state.questions_count = 0

# --- INTERFACE PRINCIPALE ---
st.title("🌟 Mon Coach Magique")
col1, col2 = st.columns([1, 1])
with col1:
    st.metric("⭐ Score", f"{st.session_state.xp} XP")
with col2:
    st.metric("📝 Questions", st.session_state.questions_count)

# Zone d'upload (Optimisée Android)
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
    lancer = st.button("🚀 LANCER LE QUIZ")
with col_btn2:
    terminer = st.button("🏁 VOIR MON RÉSUMÉ")

# --- LOGIQUE DU RÉSUMÉ ---
if terminer:
    st.balloons()
    st.info(f"### 🎉 Bravo Anaïs !\nTu as terminé ta séance avec **{st.session_state.xp} XP** ! C'est un super effort. Repose-toi bien maintenant ! ✨")
    if st.button("🔄 Recommencer une séance"):
        st.session_state.xp = 0
        st.session_state.messages = []
        st.session_state.questions_count = 0
        st.rerun()
    st.stop()

# --- LOGIQUE DU QUIZ ---
if lancer and st.session_state.stock_photos:
    st.session_state.messages = []
    st.session_state.questions_count = 0
    with st.spinner("Je prépare ta première question..."):
        try:
            prompt = "Tu es le coach d'Anaïs (6ème, TDAH). Pose une seule question QCM (A, B ou C) basée sur les photos. Sois très encourageant."
            response = model.generate_content([prompt] + st.session_state.stock_photos)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.questions_count += 1
        except Exception as e:
            st.error(f"Erreur : {e}")

# Affichage du chat
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
                    "Si c'est juste : félicite-la (+20 XP). Si c'est faux : explique la bonne réponse "
                    "gentiment. Puis pose la question suivante."
                )
                res = model.generate_content([instruction] + st.session_state.stock_photos)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
                st.session_state.questions_count += 1
                
                if any(w in res.text.lower() for w in ["bravo", "juste", "super", "exact"]):
                    st.balloons()
                    st.session_state.xp += 20
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
