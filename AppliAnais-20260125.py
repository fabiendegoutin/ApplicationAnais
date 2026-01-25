import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuration de la clé
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "VOTRE_CLE_POUR_TEST_LOCAL"

# 2. Forcer la configuration SANS passer par les versions beta
genai.configure(api_key=API_KEY)

# 3. Initialisation du modèle avec un nom de modèle complet
# Parfois, Streamlit a besoin du préfixe complet pour lever l'ambiguïté
model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')

st.title("🌟 Le Coach d'Anaïs")

# Interface simplifiée pour le test de débogage
uploaded_file = st.file_uploader("Prends une photo", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=300)
    
    if st.button("Lancer le test"):
        try:
            # Test avec une syntaxe très simple
            response = model.generate_content(["Qu'y a-t-il sur cette photo ?", img])
            st.write(response.text)
        except Exception as e:
            # Si l'erreur 404 revient, nous allons afficher la liste des modèles 
            # disponibles pour comprendre ce que voit le serveur
            st.error(f"Erreur : {e}")
            if "404" in str(e):
                st.write("Modèles accessibles sur ce serveur :")
                models = [m.name for m in genai.list_models()]
                st.write(models)
