import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎓")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configurez GEMINI_API_KEY dans les secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# GESTION DE LA SESSION (MÉMOIRE)
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Coucou ! Envoie-moi une photo de ton cours pour commencer ! 📸"}
    ]

if "xp" not in st.session_state: st.session_state.xp = 0
# Cette variable va mémoriser si on a déjà traité les images en cours
if "images_traitees" not in st.session_state: st.session_state.images_traitees = False

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title("🏆 Score")
    st.metric("Points XP", f"{st.session_state.xp}")
    st.divider()
    
    uploaded_files = st.file_uploader(
        "Ajouter une photo du cours", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        key="file_uploader" # On ajoute une clé pour pouvoir le manipuler
    )
    
    if st.button("Réinitialiser tout"):
        st.session_state.messages = [{"role": "assistant", "content": "C'est reparti !"}]
        st.session_state.images_traitees = False
        st.rerun()

# ==============================
# ZONE DE CHAT
# ==============================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Réponds ici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            
            # 1. Construction du prompt
            instruction = f"Tu es un coach scolaire. Réponds à l'enfant. S'il y a des images, utilise-les pour créer un quiz. Réponse de l'enfant : {prompt}"
            contenu_multimodal = [instruction]
            
            # 2. OPTIMISATION AUTOMATIQUE DES TOKENS
            # On n'envoie les images que SI elles sont dans l'uploader ET qu'elles n'ont pas encore été traitées
            # OU si c'est le tout premier message avec ces images.
            if uploaded_files and not st.session_state.images_traitees:
                for f in uploaded_files:
                    contenu_multimodal.append(
                        types.Part.from_bytes(data=f.getvalue(), mime_type=f.type)
                    )
                # On marque les images comme "envoyées" pour le prochain tour
                st.session_state.images_traitees = True
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contenu_multimodal
                )
                
                reponse_texte = response.text
                st.markdown(reponse_texte)
                st.session_state.messages.append({"role": "assistant", "content": reponse_texte})
                st.session_state.xp += 10
                
            except Exception as e:
                st.error(f"Erreur : {e}")
