import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION & DESIGN
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎨", layout="centered")

# Style personnalisé pour rendre le chat plus joli
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stButton>button { border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configurez GEMINI_API_KEY dans les secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# INITIALISATION DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Salut ! Je suis ton coach magique. Prête pour un défi ? 🌈"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False

# ==============================
# SIDEBAR COLORÉE
# ==============================
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>✨ Mon Espace</h1>", unsafe_allow_html=True)
    st.divider()
    
    # Affichage du score avec des couleurs
    st.markdown(f"""
        <div style='background-color: #FFEB3B; padding: 20px; border-radius: 15px; text-align: center; color: black;'>
            <h2 style='margin: 0;'>⭐ {st.session_state.xp}</h2>
            <p style='margin: 0;'>Points d'Expérience</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    uploaded_files = st.file_uploader("📥 Dépose tes photos ici", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if st.button("🚀 LANCER LE DÉFI", use_container_width=True, type="primary"):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [] 
            st.session_state.first_run = True 
        else:
            st.warning("Ajoute des photos d'abord ! 📸")

    if st.button("🗑️ Réinitialiser tout", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": "C'est reparti ! 🎈"}]
        st.session_state.quiz_en_cours = False
        st.rerun()

# ==============================
# ZONE DE CHAT
# ==============================
for i, message in enumerate(st.session_state.messages):
    avatar = "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/face/24dp/1x/baseline_face_black_24dp.png" if message["role"] == "user" else "🌟"
    
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        
        # Icône de son style mobile (située sous le message)
        if message["role"] == "assistant":
            # On utilise un expander discret pour simuler l'icône de haut-parleur
            with st.expander("🔊 Écouter la réponse"):
                st.audio(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=fr&q={message['content'].replace(' ', '+')}", format="audio/mp3")

# ==============================
# LOGIQUE DU COACH GEMINI
# ==============================
if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Analyse du cours en cours... 🧠"):
            prompt_init = "Tu es un coach scolaire fun. Analyse ces images et pose UNIQUEMENT la première question d'un quiz interactif (A, B ou C). Une seule question à la fois."
            
            contenu = [prompt_init]
            for f in uploaded_files:
                contenu.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type))
            
            try:
                response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu) #
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.session_state.first_run = False
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

if prompt := st.chat_input("Écris ta réponse ici (A, B, C...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Traitement de la réponse utilisateur (si le dernier message est de l'utilisateur)
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    user_reply = st.session_state.messages[-1]["content"]
    with st.chat_message("assistant", avatar="🌟"):
        with st.spinner("Vérification... ✨"):
            instruction = f"""L'enfant a répondu : '{user_reply}'. 
            1. Dis si c'est bon avec des emojis colorés. 
            2. Donne une explication ultra courte. 
            3. Pose la question suivante (une seule)."""
            
            historique = [msg["content"] for msg in st.session_state.messages]
            historique.append(instruction)
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=historique) #
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.xp += 15
            st.rerun()
