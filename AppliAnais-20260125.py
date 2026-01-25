import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "VOTRE_CLE_API"

genai.configure(api_key=API_KEY)

# On utilise le modèle qui est présent dans votre liste
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.set_page_config(page_title="Le Coach d'Anaïs", page_icon="🎓")

if 'xp' not in st.session_state:
    st.session_state.xp = 0

st.title("🎓 Le Coach Magique d'Anaïs")

# --- CAMERA / PHOTOS ---
photos = st.file_uploader("Prends tes leçons en photo :", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if photos:
    images_pretes = []
    for p in photos:
        img = Image.open(p)
        img.thumbnail((800, 800))
        images_pretes.append(img)
    
    st.image(images_pretes, width=150)

    if st.button("Lancer le défi ! ✨"):
        with st.spinner("L'IA analyse tes photos..."):
            prompt = "Tu es un coach scolaire. Crée un quiz de 3 questions courtes sur ces photos. Donne les réponses à la fin."
            try:
                # Appel standard
                response = model.generate_content([prompt] + images_pretes)
                st.markdown("### 📝 Ton Défi :")
                st.write(response.text)
                st.session_state.xp += 20
                st.balloons()
            except Exception as e:
                st.error(f"Erreur : {e}")

st.sidebar.metric("XP", f"{st.session_state.xp} pts")

