import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# ==============================
# CONFIGURATION & STYLE LARGE
# ==============================
st.set_page_config(page_title="Coach Magique 🌟", page_icon="🌈", layout="wide")

st.markdown("""
    <style>
    /* Force la taille du texte pour mobile */
    html, body, [class*="st-"] { font-size: 18px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 15px; border: 1px solid #ddd; }
    /* Gros boutons pour les pouces */
    .stButton>button { 
        border-radius: 30px; 
        height: 70px !important; 
        font-size: 20px !important; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    /* Zone de téléchargement plus visible */
    .stFileUploader section { background-color: #fff9e6; border: 2px dashed #ffc107; border-radius: 20px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# ==============================
# MÉMOIRE DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou Anaïs ! 👋 Prends en photo toutes les pages de ton cours de 6ème et on commence !"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False
if "mes_photos" not in st.session_state: st.session_state.mes_photos = []

# ==============================
# INTERFACE D'ACCUEIL (MULTI-PAGES)
# ==============================
st.markdown("<h1 style='text-align: center;'>🌟 Mon Coach Magique</h1>", unsafe_allow_html=True)

if not st.session_state.quiz_en_cours:
    st.write(f"### ⭐ Ton score : {st.session_state.xp} XP")
    
    # Le secret pour Android : le file_uploader permet de choisir "Appareil photo"
    # et d'utiliser la caméra arrière une fois ouvert.
    fichiers = st.file_uploader(
        "📸 CLIQUE ICI POUR PRENDRE TES PHOTOS", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        help="Tu peux prendre une photo, puis recommencer pour la page suivante !"
    )
    
    if fichiers:
        st.session_state.mes_photos = [Image.open(f) for f in fichiers]
        st.success(f"✅ {len(fichiers)} page(s) enregistrée(s) !")
        
        # On affiche les miniatures pour vérifier
        cols = st.columns(len(fichiers) if len(fichiers) < 4 else 4)
        for idx, img in enumerate(st.session_state.mes_photos):
            cols[idx % 4].image(img, caption=f"Page {idx+1}", use_container_width=True)

        if st.button("🚀 LANCER LE DÉFI MAINTENANT", type="primary"):
            st.session_state.quiz_en_cours = True
            st.session_state.first_run = True
            st.rerun()

# ==============================
# ZONE DU QUIZ
# ==============================
if st.session_state.quiz_en_cours:
    st.markdown(f"**📖 Étude de {len(st.session_state.mes_photos)} page(s) de cours**")
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"], avatar=("👤" if msg["role"] == "user" else "🌟")):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                if st.button("🔊 Écouter", key=f"btn_{i}"):
                    tts = gTTS(text=msg["content"], lang='fr')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp, format="audio/mp3", autoplay=True)

    if prompt := st.chat_input("Ta réponse (A, B ou C)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# ==============================
# LOGIQUE IA (VERROUILLÉE SUR IMAGES)
# ==============================
if st.session_state.quiz_en_cours:
    # Si le dernier message est de l'utilisateur ou si c'est le début
    dernier_role = st.session_state.messages[-1]["role"]
    
    if st.session_state.first_run or dernier_role == "user":
        with st.chat_message("assistant", avatar="🌟"):
            with st.spinner("Je réfléchis... ✨"):
                if st.session_state.first_run:
                    consigne = "Tu es le coach d'Anaïs (6ème). Analyse TOUTES les pages fournies. Pose la 1ère question QCM (A, B, C) sur le cours. Saute une ligne entre chaque choix."
                    st.session_state.first_run = False
                else:
                    rep = st.session_state.messages[-1]["content"]
                    consigne = f"Anaïs a répondu '{rep}'. Vérifie sur les photos. Félicite-la (Bravo Anaïs !) et pose le prochain QCM basé sur les photos. Saute des lignes."
                
                # Envoi des images + consigne
                contenu = [consigne] + st.session_state.mes_photos
                response = model.generate_content(contenu)
                
                if "bravo" in response.text.lower():
                    st.balloons()
                    st.session_state.xp += 20
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
