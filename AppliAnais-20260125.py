import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION & CLIENT
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎓")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configurez GEMINI_API_KEY dans les secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# INITIALISATION DE LA SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Coucou ! Prête pour un nouveau défi ? Envoie tes photos et clique sur le bouton ! 📸"}]
if "xp" not in st.session_state: st.session_state.xp = 0
if "quiz_en_cours" not in st.session_state: st.session_state.quiz_en_cours = False

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title("🏆 Score")
    st.metric("Points XP", f"{st.session_state.xp}")
    st.divider()
    
    uploaded_files = st.file_uploader("Photos du cours", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    # BOUTON POUR LANCER LE QUIZ
    if st.button("🚀 LANCER LE DÉFI", use_container_width=True):
        if uploaded_files:
            st.session_state.quiz_en_cours = True
            st.session_state.messages = [] # On nettoie pour le nouveau quiz
            st.session_state.first_run = True # Flag pour envoyer les images
        else:
            st.warning("Ajoute des photos d'abord !")

    if st.button("Réinitialiser"):
        st.session_state.messages = [{"role": "assistant", "content": "C'est reparti !"}]
        st.session_state.quiz_en_cours = False
        st.rerun()

# ==============================
# ZONE DE CHAT & AUDIO
# ==============================
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Bouton audio pour les messages de l'assistant
        if message["role"] == "assistant":
            st.audio(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=fr&q={message['content'].replace(' ', '+')}", format="audio/mp3")

# ==============================
# LOGIQUE DU COACH
# ==============================
# 1. Si on vient de cliquer sur "Lancer le défi"
if st.session_state.quiz_en_cours and getattr(st.session_state, 'first_run', False):
    with st.chat_message("assistant"):
        with st.spinner("Lecture du cours..."):
            prompt_init = "Tu es un coach scolaire. Analyse ces images et pose UNIQUEMENT la première question d'un quiz interactif. Propose des choix A, B, C. Attends ma réponse avant de passer à la suite."
            
            contenu = [prompt_init]
            for f in uploaded_files:
                contenu.append(types.Part.from_bytes(data=f.getvalue(), mime_type=f.type))
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=contenu)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.first_run = False
            st.rerun()

# 2. Gestion des réponses de l'enfant
if prompt := st.chat_input("Ta réponse (A, B, C...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Vérification..."):
            # On envoie l'historique texte pour que Gemini sache où on en est (sans renvoyer les images)
            instruction = f"""Voici la réponse de l'enfant : '{prompt}'. 
            1. Dis si c'est correct ou non. 
            2. Explique pourquoi simplement avec des emojis. 
            3. Pose ensuite la question suivante (une seule).
            Si c'était la dernière, félicite-le chaleureusement."""
            
            # On construit l'historique pour le contexte
            historique_texte = [msg["content"] for msg in st.session_state.messages]
            historique_texte.append(instruction)
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=historique_texte)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.session_state.xp += 15
            st.rerun()
