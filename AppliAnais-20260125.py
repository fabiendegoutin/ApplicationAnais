import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- STYLE & UI ---
st.set_page_config(page_title="Le Coach d'Anaïs 🌟", layout="centered")

st.markdown("""
    <style>
    .fixed-header {
        position: fixed; top: 50px; right: 15px; width: 150px;
        background: linear-gradient(135deg, #FF69B4 0%, #DA70D6 100%);
        color: white; padding: 10px; border-radius: 20px;
        font-weight: bold; z-index: 9999; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 2px solid white;
    }
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 15px !important; height: 3.5em !important; font-weight: bold !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #4CAF50 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #2196F3 !important; color: white !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #9C27B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-2.5-flash')

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Le Coach d'Anaïs")

# --- 1. LECTURE ---
if not st.session_state.cours_texte:
    photo = st.camera_input("📸 Prends ton cours")
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo", type=['jpg', 'png'])

    if photo and st.button("🚀 LANCER LE QUIZZ"):
        try:
            with st.spinner("Lecture du cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((600, 600))
                res = model.generate_content(["Extrais le texte de ce cours.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- 2. QUIZZ ---
elif st.session_state.nb_q < 10:
    st.write(f"Question {st.session_state.nb_q}/10")
    st.progress(st.session_state.nb_q / 10)

    if not st.session_state.messages:
        st.session_state.nb_q = 1
        prompt_init = (f"Cours : {st.session_state.cours_texte}. ORDRE CRITIQUE : "
                      f"1. Écris 'Question n°{st.session_state.nb_q}'. "
                      "2. Pose la question clairement. "
                      "3. Saute deux lignes. "
                      "4. Écris les choix A, B, C avec deux sauts de ligne entre chaque. "
                      "5. Finis par 5 sauts de ligne.")
        q = model.generate_content(prompt_init)
        st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
        st.rerun()

    st.write("### 🧩 Ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Vérification..."):
            last_msg = st.session_state.messages[0]["content"]
            prompt_v = (f"Cours : {st.session_state.cours_texte}. Question précédente : {last_msg}. "
                       f"Réponse d'Anaïs : {rep}. Dis si c'est juste, explique, puis : "
                       f"ORDRE CRITIQUE : 1. Écris 'Question n°{st.session_state.nb_q}'. "
                       "2. Pose l'énoncé de la nouvelle question. "
                       "3. Saute deux lignes. 4. Écris les choix A, B, C avec deux sauts de ligne. "
                       "5. Finis par 5 sauts de ligne.")
            res = model.generate_content(prompt_v)
            if "BRAVO" in res.text.upper() or "JUSTE" in res.text.upper():
                st.session_state.xp += 20
                st.balloons()
            st.session_state.messages.insert(0, {"role": "user", "content": f"Choix {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    # Affichage
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar="🌈" if msg["role"]=="assistant" else "⭐"):
            if msg["role"] == "assistant":
                col_text, col_audio = st.columns([0.85, 0.15])
                with col_text:
                    st.markdown(msg["content"])
                with col_audio:
                    if st.button("🔊", key=f"v_{i}"):
                        tts = gTTS(text=msg["content"], lang='fr')
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        st.audio(fp, format="audio/mp3", autoplay=True)
            else:
                st.markdown(msg["content"])
        st.markdown("<br><hr><br>", unsafe_allow_html=True) # Séparateur visuel fort

if st.session_state.xp >= 200:
    st.image("https://img.freepik.com/vecteurs-premium/embleme-medaille-or-laurier-insigne-champion-trophee-recompense_548887-133.jpg", width=100)
