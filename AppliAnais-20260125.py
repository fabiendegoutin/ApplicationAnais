import streamlit as st
from google import genai
from google.genai import types

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(page_title="Mon Coach Magique", page_icon="🎓")

# Initialisation du client Gemini
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Configurez GEMINI_API_KEY dans les secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ==============================
# GESTION DU CHAT ET DE LA SESSION
# ==============================
# On initialise l'historique des messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Coucou ! Je suis ton coach. Envoie-moi une photo de ton cours pour commencer le défi ! 📸"}
    ]

# ==============================
# SIDEBAR (Score et Photos)
# ==============================
with st.sidebar:
    st.title("🏆 Score")
    if "xp" not in st.session_state: st.session_state.xp = 0
    st.metric("Points XP", f"{st.session_state.xp}")
    
    st.divider()
    # Zone de téléchargement dans la barre latérale pour libérer l'espace chat
    uploaded_files = st.file_uploader(
        "Ajouter une photo du cours", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

# ==============================
# ZONE DE CHAT
# ==============================
# Affichage des messages existants
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur (Chat Input)
if prompt := st.chat_input("Réponds ici..."):
    # 1. Afficher le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Préparer la réponse de Gemini
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis..."):
            
            # Construction du contenu (Texte + Images si présentes)
            instruction = f"""Tu es un coach bienveillant pour un enfant. 
            Si l'utilisateur envoie des photos, crée un quiz de 3 questions.
            Si l'utilisateur répond, corrige-le avec douceur et emojis.
            Réponse de l'enfant : {prompt}"""
            
            contenu_multimodal = [instruction]
            
            # On ajoute les images seulement si elles viennent d'être chargées
            if uploaded_files:
                for f in uploaded_files:
                    contenu_multimodal.append(
                        types.Part.from_bytes(data=f.getvalue(), mime_type=f.type)
                    )

            try:
                # Appel API Gemini
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contenu_multimodal
                )
                
                reponse_texte = response.text
                st.markdown(reponse_texte)
                
                # Sauvegarde dans l'historique
                st.session_state.messages.append({"role": "assistant", "content": reponse_texte})
                st.session_state.xp += 10 # Gain de points pour chaque interaction
                
            except Exception as e:
                st.error(f"Oups, petite erreur : {e}")

# Bouton pour recommencer à zéro
if st.sidebar.button("Réinitialiser la discussion"):
    st.session_state.messages = [{"role": "assistant", "content": "C'est reparti ! Envoie-moi tes photos."}]
    st.rerun()
