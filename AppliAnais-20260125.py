import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
from gtts import gTTS
import io
import time

# --- STYLE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-header { position: fixed; top: 50px; right: 15px; width: 140px; background: #FF69B4; color: white; padding: 10px; border-radius: 20px; z-index: 9999; text-align: center; border: 2px solid white; font-weight: bold; }
    div[data-testid="stHorizontalBlock"] button { border-radius: 12px !important; height: 3.5em !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion stable
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE OPTIMISÉE ---
if not st.session_state.cours_texte:
    source = st.file_uploader("📂 Charge ta photo du cours", type=['jpg', 'jpeg', 'png'])
    
    if source and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Préparation de l'image (nettoyage)..."):
                img = Image.open(source).convert("RGB")
                
                # Optimisation pour l'écriture sur carreaux
                img.thumbnail((800, 800)) 
                
                prompt = "Ceci est un cours de 6ème écrit à la main. Extrais le texte fidèlement (températures, états de la matière)."
                res = model.generate_content([prompt, img])
                
                st.session_state.cours_texte = res.text
                
                # Petite pause pour laisser l'API respirer
                time.sleep(2)
                
                q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose une question QCM courte (A, B, C). Saute une ligne entre chaque choix.")
                st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
                st.rerun()
        except Exception:
            st.error("Désolé ! L'IA a du mal à lire cette image via l'API. Attends 10 secondes sans cliquer.")

# --- 2. QUIZZ ---
elif st.session_state.nb_q < 10:
    st.progress(st.session_state.nb_q / 10)
    
    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            time.sleep(1)
            prompt = f"Cours : {st.session_state.cours_texte}. Question : {st.session_state.messages[0]['content']}. Réponse : {rep}. Dis si c'est juste. Puis pose la question suivante."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.balloons()
                st.session_state.xp += 20
            st.session_state.messages.insert(0, {"role": "user", "content": f"Réponse {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    st.write("---")
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
