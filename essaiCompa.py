import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PFtest import plot_feminine_graph, get_feminine_constants
from PMtest import plot_masculine_graph, get_masculine_constants
import os
import tempfile
import zipfile
import base64

# -----------------------------
# CSS pour harmoniser l'interface
# -----------------------------
st.markdown(
    """
    <style>
    /* Fond principal */
    body {
        background-color: #F0F2F6;
    }
    /* Sidebar avec une couleur de fond harmonisée */
    [data-testid="stSidebar"] {
        position: fixed !important;
        width: 300px !important;
        top: 0;
        left: 0;
        height: 100% !important;
        z-index: 9999 !important;
        background: #E5E7EB !important;
        color: #333333 !important;
        box-shadow: 4px 0px 10px rgba(0,0,0,0.2) !important;
    }
    [data-testid="stSidebar"] * {
        color: #333333 !important;
    }
    [data-testid="stSidebarNav"]::before {
        content: "\2699"; /* ⚙ */
        font-size: 24px;
        display: block;
        text-align: center;
        padding: 10px;
        cursor: pointer;
        color: #333333;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #F0F2F6 !important;
    }
    </style>
    """, unsafe_allow_html=True
)

# -----------------------------
# Fonction de chargement d'un fichier ZIP
# -----------------------------
def load_zip(key_prefix):
    """
    Charge un fichier ZIP contenant :
      - Un fichier Excel (avec les feuilles 'CSV', 'Poste', 'Constante')
      - Un dossier "Trombi" avec les images des joueurs.
    Le fichier ZIP est extrait dans un répertoire temporaire et renvoie :
      data, positions, constante_data, base_folder
    """
    uploaded_zip = st.file_uploader(f"Charger un fichier ZIP ({key_prefix})", type=["zip"], key=f"{key_prefix}_zip")
    if uploaded_zip is not None:
        try:
            base_folder = tempfile.mkdtemp()
            zip_path = os.path.join(base_folder, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getvalue())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(base_folder)
            # Rechercher le fichier Excel dans le ZIP
            excel_file_path = None
            for root, dirs, files in os.walk(base_folder):
                for file in files:
                    if file.lower().endswith((".xls", ".xlsx", ".xlsm")):
                        excel_file_path = os.path.join(root, file)
                        break
                if excel_file_path:
                    break
            if not excel_file_path:
                st.error("Aucun fichier Excel trouvé dans le ZIP.")
                return None, None, None, None
            excel_data = pd.ExcelFile(excel_file_path)
            required_sheets = {"CSV", "Poste", "Constante"}
            missing = required_sheets - set(excel_data.sheet_names)
            if missing:
                st.error("Feuilles manquantes : " + ", ".join(missing))
                return None, None, None, None
            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")
            st.success("Fichier ZIP chargé avec succès.")
            return data, positions, constante_data, base_folder
        except Exception as e:
            st.error(f"Erreur lors du chargement du ZIP ({key_prefix}) : {e}")
            return None, None, None, None
    else:
        st.info("Veuillez charger un fichier ZIP.")
        return None, None, None, None

# -----------------------------
# Fonction pour afficher le portrait d'un joueur
# -----------------------------
def display_player_photo(selected_player, positions, base_folder):
    """
    Récupère et affiche le portrait du joueur à partir du dossier "Trombi".
    L'image est affichée au format PNG avec transparence.
    """
    if "Trombi" not in positions.columns:
        st.error("La colonne 'Trombi' n'existe pas dans la feuille Poste.")
        return
    selected_norm = str(selected_player).strip().lower()
    positions["Joueur_norm"] = positions["Joueur"].astype(str).str.strip().str.lower()
    player_row = positions[positions["Joueur_norm"] == selected_norm]
    if player_row.empty:
        st.warning("Aucune donnée de portrait pour ce joueur.")
        return
    file_name = player_row.iloc[0]["Trombi"]
    if not file_name:
        st.warning("Aucune photo disponible pour ce joueur.")
        return
    image_path = os.path.join(base_folder, "Trombi", file_name)
    if not os.path.exists(image_path):
        st.error(f"Le fichier image n'existe pas : {image_path}")
        return
    try:
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier image : {e}")
        return
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    html = f'''
    <div style="text-align: center;">
        <img src="data:image/png;base64,{base64_image}" alt="Portrait de {selected_player}" style="max-width:100%; height:auto;">
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# -----------------------------
# Fonction de filtrage et de calcul additionnel (inchangé)
# -----------------------------
def filter_duration(player_data, min_duration=3900):
    return player_data[player_data["Durée"] >= min_duration]

def compute_additional_columns(player_data):
    if "Dist>16kmh" in player_data.columns:
        player_data["Distance > 16km/h"] = player_data["Dist>16kmh"]
    if "Dist>20kmh" in player_data.columns:
        player_data["Distance > 20km/h"] = (player_data["Dist>20kmh"] * 1000)
    if "Dist>20kmh" in player_data.columns and "Durée" in player_data.columns:
        player_data["Distance>20kmh/min"] = (player_data["Dist>20kmh"] * 1000).fillna(0) / (player_data["Durée"].replace(0, 1) / 60)
    if "Distance16" in player_data.columns and "Durée" in player_data.columns:
        player_data["Distance>16kmh/min"] = player_data["Distance16"] / (player_data["Durée"].replace(0, 1) / 60)
    if all(col in player_data.columns for col in ["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²",
                                                   "Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]):
        player_data["Nb Acc/Dec > 2m/s²"] = player_data[["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²",
                                                         "Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1)
    if "Nb Acc/Dec > 2m/s²" in player_data.columns and "Durée" in player_data.columns:
        player_data["Nb Acc/Dec > 2m/s²/min"] = player_data["Nb Acc/Dec > 2m/s²"].fillna(0) / (player_data["Durée"].replace(0, 1) / 60)
    if all(col in player_data.columns for col in ["Nb Acc>4m/s²", "Nb Dec>4m/s²"]):
        player_data["Nb Acc/Dec > 4m/s²"] = player_data[["Nb Acc>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1)
    if "Nb Acc/Dec > 4m/s²" in player_data.columns and "Durée" in player_data.columns:
        player_data["Nb Acc/Dec > 4m/s²/min"] = player_data["Nb Acc/Dec > 4m/s²"].fillna(0) / (player_data["Durée"].replace(0, 1) / 60)
    return player_data

# -----------------------------
# Fonction d'affichage pour la comparaison en colonnes
# -----------------------------
def display_column_comparison(key_prefix, shared_graphs):
    # Charge le fichier ZIP pour la colonne
    data, positions, constante_data, base_folder = load_zip(key_prefix)
    if data is not None:
        st.write(f"Sélectionner un joueur ({key_prefix}):")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox(
            f"Sélectionner un joueur/joueuse ({key_prefix})",
            players,
            key=f"{key_prefix}_player"
        )
        global_module = st.session_state.get("global_module", "Pôle Féminin")
        if global_module == "Pôle Féminin":
            constants = get_feminine_constants(constante_data)
        else:
            constants = get_masculine_constants(constante_data)
        if selected_player:
            st.markdown(f"**{selected_player}**")
            # Afficher le portrait du joueur sous le selectbox
            display_player_photo(selected_player, positions, base_folder)
            st.write(f"Graphiques pour {selected_player} ({global_module}):")
            filter_matches = st.checkbox(
                f"Afficher les matchs < 3900 secondes ({key_prefix})",
                value=False,
                key=f"{key_prefix}_filter"
            )
            player_data = data[data["Joueur"] == selected_player]
            if not filter_matches:
                player_data = filter_duration(player_data)
            if player_data.empty:
                st.warning(f"Aucune donnée après filtrage ({key_prefix}).")
            else:
                if shared_graphs:
                    st.write(f"**Graphiques sélectionnés ({key_prefix}):**")
                    for graph in shared_graphs:
                        st.subheader(f"Graphique : {graph}")
                        if global_module == "Pôle Féminin":
                            fig = plot_feminine_graph(graph, selected_player, constants, player_data, positions)
                        else:
                            fig = plot_masculine_graph(graph, selected_player, constants, player_data, positions)
                        if fig:
                            st.plotly_chart(fig, key=f"{key_prefix}_{selected_player}_{graph}")
                        else:
                            st.error(f"Graphique {graph} non disponible.")
    else:
        st.warning(f"Veuillez charger un fichier ZIP pour {key_prefix}.")

# -----------------------------
# Configuration globale dans la sidebar
# -----------------------------
with st.sidebar.expander("⚙️ Configuration des graphiques", expanded=True):
    global_module = st.selectbox("Choisir le module d'analyse", ["Pôle Féminin", "Pôle Masculin"])
    st.session_state.global_module = global_module
    if global_module == "Pôle Féminin":
        general_graphs = [
            "Distance",
            "Distance>19km/h",
            "Distance > 23km/h",
            "TopSpeed",
            "Accélérations > 2m/s²",
            "Décélérations > 2m/s²",
            "Diagramme empilé"
        ]
        per_min_graphs = [
            "Dist/min",
            "Distance>23kmh/min",
            "Distance > 19kmh/min",
            "Nb Accélération > 2m/s²/min",
            "Nb Décélérations > 2m/s²/min"
        ]
    else:
        general_graphs = [
            "Distance",
            "Distance > 16km/h",
            "Distance > 20km/h",
            "TopSpeed",
            "Nb Acc/Dec > 2m/s²",
            "Nb Acc/Dec > 4m/s²",
            "Diagramme empilé"
        ]
        per_min_graphs = [
            "Dist/min",
            "Distance>20kmh/min",
            "Distance>16kmh/min",
            "Nb Acc/Dec > 2m/s²/min",
            "Nb Acc/Dec > 4m/s²/min"
        ]
    select_all_general = st.checkbox("Sélectionner tous les graphiques généraux")
    select_all_per_min = st.checkbox("Sélectionner tous les graphiques par minute")
    shared_general_graphs = st.multiselect("Choisir les graphiques généraux", general_graphs, default=general_graphs if select_all_general else [])
    shared_per_min_graphs = st.multiselect("Choisir les graphiques par minute", per_min_graphs, default=per_min_graphs if select_all_per_min else [])
shared_graphs = shared_general_graphs + shared_per_min_graphs

# -----------------------------
# Affichage en deux colonnes pour la comparaison
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    st.header("Joueur 1")
    display_column_comparison("col1", shared_graphs)
with col2:
    st.header("Joueur 2")
    display_column_comparison("col2", shared_graphs)
