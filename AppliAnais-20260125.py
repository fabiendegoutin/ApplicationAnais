import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

# Connexion API avec le nom de modèle "Latest"
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Utilisation du nom complet requis par l'API v1beta
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

if "xp" not in st.session_state: st.session_state.xp = 0
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "messages" not in st.session_state: st.session_state.messages = []

# Score affiché proprement
st.sidebar.title(f"🚀 Score : {st.session_state.xp} XP")

st.title("✨ Le Coach d'Anaïs")

# --- ÉTAPE 1 : LECTURE ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Le coach déchiffre ton écriture..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((600, 600))
                
                # Premier appel pour extraire le texte
                res = model.generate_content(["Extrais le texte de ce cours de 6ème.", img])
                
                if res.text:
                    st.session_state.cours_texte = res.text
                    st.success("C'est bon ! Le quizz commence.")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            # Affichage de l'erreur réelle pour nous aider si ça persiste
            st.error(f"Détail technique : {e}")
            st.info("💡 Conseil : Vérifie que ta clé API est bien valide dans les Secrets.")

# --- ÉTAPE 2 : QUIZZ ---
elif len(st.session_state.messages) < 10:
    # Génération de la question
    if not st.session_state.messages:
        q = model.generate_content(f"Cours : {st.session_state.cours_texte}. Pose un QCM (A, B, C).")
        st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
        st.rerun()

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        with st.spinner("Vérification..."):
            prompt = f"Cours : {st.session_state.cours_texte}. Réponse : {rep}. Bravo si juste, puis nouvelle question."
            res = model.generate_content(prompt)
            if "BRAVO" in res.text.upper():
                st.session_state.xp += 20
                st.balloons()
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
