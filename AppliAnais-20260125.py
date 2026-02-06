import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- STYLE & UI ---
st.set_page_config(page_title="Ton Coach Magique 🌟", layout="centered")

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

# Configuration API (Vérifiez bien votre secret GEMINI_API_KEY)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-1.5-flash') # Mise à jour vers un modèle stable

if "xp" not in st.session_state: st.session_state.xp = 0
if "messages" not in st.session_state: st.session_state.messages = []
if "cours_texte" not in st.session_state: st.session_state.cours_texte = None
if "nb_q" not in st.session_state: st.session_state.nb_q = 0

st.markdown(f'<div class="fixed-header">🚀 {st.session_state.xp} XP</div>', unsafe_allow_html=True)
st.title("✨ Ton Coach Magique")

# --- 1. LECTURE DU COURS ---
if not st.session_state.cours_texte:
    st.write("### Coucou Anaïs ! Prête pour un petit défi ? 😊")
    # Modification ici : ajout de camera_sidebar=False ou utilisation simple pour mobile
    # Le mode "user" correspond souvent à la caméra arrière sur mobile
    photo = st.camera_input("📸 Prends ton cours en photo", label_visibility="visible")
    
    if not photo:
        photo = st.file_uploader("📂 Ou choisis une photo de ton cahier", type=['jpg', 'png'])

    if photo and st.button("🚀 C'EST PARTI !"):
        try:
            with st.spinner("Je lis ton super cours..."):
                img = Image.open(photo).convert("RGB")
                img.thumbnail((800, 800))
                # Prompt pour extraire le texte
                res = model.generate_content(["Extrais tout le texte de cette image de cours.", img])
                st.session_state.cours_texte = res.text
                st.rerun()
        except Exception as e:
            st.error(f"Oups ! Je n'ai pas réussi à lire la photo : {e}")

# --- 2. LE QUIZZ ---
elif st.session_state.nb_q < 10:
    st.write(f"Question **{st.session_state.nb_q}** sur 10")
    st.progress(st.session_state.nb_q / 10)

    if not st.session_state.messages:
        st.session_state.nb_q = 1
        prompt_init = (f"Tu es le coach personnel d'Anaïs. Voici son cours : {st.session_state.cours_texte}. "
                      "Instructions : "
                      "1. Adresse-toi TOUJOURS directement à elle (dis 'tu'). "
                      "2. Ne mentionne jamais 'le texte' ou 'selon le cours'. "
                      "3. Pose une question sur le contenu. "
                      "4. Écris 'Question n°1'. "
                      "5. Propose 3 choix (A, B, C).")
        q = model.generate_content(prompt_init)
        st.session_state.messages.insert(0, {"role": "assistant", "content": q.text})
        st.rerun()

    st.write("### 🧩 Choisis ta réponse :")
    c1, c2, c3 = st.columns(3)
    rep = None
    if c1.button("A", use_container_width=True): rep = "A"
    if c2.button("B", use_container_width=True): rep = "B"
    if c3.button("C", use_container_width=True): rep = "C"

    if rep:
        st.session_state.nb_q += 1
        with st.spinner("Je vérifie..."):
            last_msg = st.session_state.messages[0]["content"]
            prompt_v = (f"Cours : {st.session_state.cours_texte}. Question : {last_msg}. Réponse d'Anaïs : {rep}. "
                       "Règles : "
                       "- Si c'est juste : sois super joyeux, félicite-la chaleureusement ! "
                       "- Si c'est faux : sois très gentil, ne dis JAMAIS qu'elle a tort. Dis plutôt 'Presque !' ou 'C'est un petit piège'. "
                       "- Explique la réponse en 2 phrases MAXIMUM. "
                       "- Ne cite jamais 'le texte'. "
                       "- Enchaîne sur : 'Question n°{st.session_state.nb_q}', puis la question et les choix A, B, C.")
            
            res = model.generate_content(prompt_v)
            
            # Système de points
            if any(word in res.text.upper() for word in ["BRAVO", "GÉNI", "SUPER", "OUI", "EXCELLENT"]):
                st.session_state.xp += 20
                st.balloons()
            
            st.session_state.messages.insert(0, {"role": "user", "content": f"Ma réponse : {rep}"})
            st.session_state.messages.insert(0, {"role": "assistant", "content": res.text})
            st.rerun()

    # Affichage des messages
    for i, msg in enumerate(st.session_state.messages):
        role = "assistant" if msg["role"]=="assistant" else "user"
        with st.chat_message(role, avatar="🌈" if role=="assistant" else "⭐"):
            col_text, col_audio = st.columns([0.85, 0.15])
            with col_text:
                st.markdown(msg["content"])
            with col_audio:
                if st.button("🔊", key=f"v_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)
        st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state.nb_q >= 10:
    st.balloons()
    st.success(f"Bravo Anaïs ! Tu as terminé tes révisions avec {st.session_state.xp} XP ! 🏆")
    if st.button("Recommencer"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()
