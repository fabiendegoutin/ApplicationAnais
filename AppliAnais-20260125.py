import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- CONFIGURATION VISUELLE ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    /* Barre XP et Progression toujours visibles en haut */
    .status-bar {
        position: fixed; top: 10px; right: 10px; z-index: 1000;
        background: white; padding: 10px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1); border: 2px solid #FF69B4;
    }
    /* Boutons de réponse colorés et larges */
    div[data-testid="stHorizontalBlock"] button { height: 3.5em !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

# Connexion API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialisation
if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

# UI Fixe
st.markdown(f'<div class="status-bar">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- ETAPE 1 : LECTURE DU COURS ---
if not st.session_state.cours_texte:
    st.write("### 📸 Charge ton cours pour commencer")
    # Utilisation d'un uploader simple pour plus de stabilité
    photo = st.file_uploader("Choisis la photo du cahier", type=['jpg', 'jpeg', 'png'], key="uploader")
    
    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours manuscrit..."):
                img = Image.open(photo).convert("RGB")
                # On force une taille très petite pour ne jamais saturer l'API
                img.thumbnail((500, 500)) 
                
                # On demande le texte et la 1ère question en même temps
                prompt = "Ceci est un cours de 6ème. Extrais le texte important et pose une question QCM (A, B, C)."
                res = model.generate_content([prompt, img])
                
                if res.text:
                    st.session_state.cours_texte = res.text
                    st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                    st.rerun()
        except Exception as e:
            st.error("Le service Google est surchargé. Attends 10 secondes sans toucher à rien, puis reclique.")
            time.sleep(5)

# --- ETAPE 2 : LE QUIZZ (NOUVEAU EN HAUT) ---
elif st.session_state.nb_q < 10:
    st.write(f"**Progression : Question {st.session_state.nb_q} / 10**")
    st.progress(st.session_state.nb_q / 10)

    # Zone de boutons de réponse
    st.write("### 🧩 Choisis ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True, key="A"): rep = "A"
    if c2.button("B", use_container_width=True, key="B"): rep = "B"
    if c3.button("C", use_container_width=True, key="C"): rep = "C"

    if rep:
        try:
            st.session_state.nb_q += 1
            with st.spinner("Vérification..."):
                prompt_v = f"Cours: {st.session_state.cours_texte}. L'élève répond {rep}. Dis si c'est juste (BRAVO) et pose la question suivante."
                res = model.generate_content(prompt_v)
                
                if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                    st.balloons()
                    st.session_state.xp += 20
                
                # On insère au début pour que ça s'affiche en haut (pas de scroll)
                st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {rep}"})
                st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
                st.rerun()
        except:
            st.warning("Petite pause de l'IA... Patiente un instant.")
            time.sleep(5)

    st.write("---")
    # Affichage de l'historique (le plus récent en haut)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
