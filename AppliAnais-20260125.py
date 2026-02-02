import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-ui { position: fixed; top: 10px; right: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 15px; border: 2px solid #FF69B4; }
    div[data-testid="stHorizontalBlock"] button { height: 3.5em !important; border-radius: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API stable
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

st.markdown(f'<div class="fixed-ui">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. CHARGEMENT DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Étape 1 : Ton cours")
    
    # Retour de la caméra et de l'import photo
    img_cam = st.camera_input("Prends une photo")
    img_file = st.file_uploader("Ou choisis une photo", type=['jpg', 'png'])
    photo = img_cam if img_cam else img_file

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Analyse du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((500, 500)) # Réduction pour éviter la saturation
                res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except:
            st.error("L'IA n'arrive pas à lire la photo pour le moment. 🚧")
            st.info("💡 Astuce : Tape ou colle le texte de ton cours juste en dessous pour commencer sans attendre !")
            
    # Option de secours : Texte direct
    texte_secours = st.text_area("✍️ Ou colle ton cours ici :", height=150)
    if texte_secours and st.button("📝 Utiliser ce texte"):
        st.session_state.cours_texte = texte_secours
        st.rerun()

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < 10:
    # Génération automatique de la première question
    if not st.session_state.messages:
        with st.spinner("Le coach prépare la question..."):
            time.sleep(1) # Pause de sécurité
            q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose une question QCM (A, B, C) avec des sauts de ligne.")
            st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
            st.rerun()

    st.write(f"Question {st.session_state.nb_q} / 10")
    st.progress(st.session_state.nb_q / 10)

    # Zone de réponse
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            prompt = f"Cours : {st.session_state.cours_texte}. Réponse d'Anaïs : {rep}. Bravo si juste, sinon explique. Puis nouvelle question QCM."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.balloons()
                st.session_state.xp += 20
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and st.button("🔊", key=f"v_{i}"):
                tts = gTTS(text=msg["content"], lang='fr')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", autoplay=True)
                
