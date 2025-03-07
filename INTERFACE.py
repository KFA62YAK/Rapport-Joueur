import streamlit as st
import os
import base64
import time

# Configuration de la page : mode wide (large)
st.set_page_config(page_title="Pôle Liévin", page_icon="⚽", layout="wide")

# Injection du CSS global pour supprimer marges/padding, fixer la hauteur, désactiver le scroll
# et forcer le mode light (fond blanc, texte noir)
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
         margin: 0;
         padding: 0;
         height: 100vh;
         overflow: hidden;
         background-color: #ffffff;
         color: #000000;
    }
    /* Container pour le header (image + titre) */
    .header-container {
         position: relative;
         width: 100%;
         height: 40vh;
    }
    .header-container img {
         width: 100%;
         height: 100%;
         object-fit: cover;
    }
    /* Overlay dégradé pour l'effet de fondu sur l'image */
    .header-container::after {
         content: "";
         position: absolute;
         top: 0;
         left: 0;
         width: 100%;
         height: 100%;
         background: linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,1) 100%);
         z-index: 1;
    }
    /* Titre positionné en bas de l'image, au-dessus de l'overlay */
    .header-title {
         position: absolute;
         bottom: 0;
         width: 100%;
         text-align: center;
         z-index: 2;
    }
    .header-title h1 {
         margin: 0;
         padding: 10px 0;
         font-size: 3em;
         color: black;
    }
    /* Stylisation des boutons */
    .stButton>button {
         font-size: 2.2em !important;
         padding: 25px 45px !important;
         margin: 10px !important;
         height: 80px !important;
         width: 100%;
         font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Fonction pour convertir une image en base64
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Chemin complet vers l'image (vérifiez le chemin et l'extension)
image_path = r"IMFD.jpg"
img_base64 = ""
if os.path.exists(image_path):
    img_base64 = get_base64(image_path)
else:
    st.error(f"L'image n'existe pas : {image_path}")

# Affichage du header (image avec effet de fondu et titre)
st.markdown(
    f"""
    <div class="header-container">
         <img src="data:image/jpeg;base64,{img_base64}" alt="Image de fond" />
         <div class="header-title">
              <h1>⚽ Pôle Liévin</h1>
         </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialisation de la navigation multi-pages
if "page" not in st.session_state:
    st.session_state.page = "home"

# Définition de la fonction de la page d'accueil
def show_home():
    # Première ligne : deux colonnes pour deux boutons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 Analyse GPS/Vidéo", key="btn_analyse"):
            st.session_state.page = "analyse"
            st.rerun()
    with col2:
        if st.button("🫀 Analyse FC", key="btn_HRR"):
            st.session_state.page = "HRR"
            st.rerun()
    # Deuxième ligne : centrer le bouton "Comparaison joueur"
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.button("🪪 Comparaison joueur", key="btn_comparaison"):
            st.session_state.page = "comparaison"
            st.rerun()

# Fonctions pour les autres onglets (exécution de scripts externes si disponibles)
def show_analyse():
    st.markdown("<h2>📈 Analyse GPS/Vidéo</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", key="home_from_analyse"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🪪 Comparaison joueur", key="comparaison_from_analyse"):
            st.session_state.page = "comparaison"
            st.rerun()
        if st.button("🫀 Analyse FC", key="HRR_from_analyse"):
            st.session_state.page = "HRR"
            st.rerun()
    with col2:
        time.sleep(1)
        script_path = os.path.join(os.path.dirname(__file__), "INVENT.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")

def show_HRR():
    st.markdown("<h2>🫀 Analyse FC</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", key="home_from_HRR"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("🪪 Comparaison joueur", key="comparaison_from_HRR"):
            st.session_state.page = "comparaison"
            st.rerun()
        if st.button("📈 Analyse GPS/Vidéo", key="analyse_from_HRR"):
            st.session_state.page = "analyse"
            st.rerun()
    with col2:
        time.sleep(1)
        script_path = os.path.join(os.path.dirname(__file__), "ANALYSE.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")

def show_comparaison():
    st.markdown("<h2>🪪 Comparaison Joueur</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        if st.button("🏠 Accueil", key="home_from_comparaison"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📈 Analyse GPS/Vidéo", key="analyse_from_comparaison"):
            st.session_state.page = "analyse"
            st.rerun()
        if st.button("🫀 Analyse FC", key="HRR_from_comparaison"):
            st.session_state.page = "HRR"
            st.rerun()
    with col2:
        script_path = os.path.join(os.path.dirname(__file__), "essaiCompa.py")
        if os.path.exists(script_path):
            try:
                with open(script_path, "r", encoding="utf-8") as file:
                    code = file.read()
                exec(code, globals())
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du script : {e}")
        else:
            st.error(f"Le fichier spécifié n'existe pas : {script_path}")

# Affichage du contenu en fonction de la navigation (directement sous le header)
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "analyse":
    show_analyse()
elif st.session_state.page == "HRR":
    show_HRR()
elif st.session_state.page == "comparaison":
    show_comparaison()

