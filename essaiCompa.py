import streamlit as st
import pandas as pd
from PFtest import plot_feminine_graph, get_feminine_constants
from PMtest import plot_masculine_graph, get_masculine_constants
import matplotlib.pyplot as plt
import tempfile
import os

# Appliquer du CSS pour superposer la sidebar avec la couleur de fond de l'application
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        position: fixed !important;
        width: 300px !important;
        top: 0;
        left: 0;
        height: 100% !important;
        z-index: 9999 !important;
        background: #2E2E2E !important;
        color: white !important;
        box-shadow: 4px 0px 10px rgba(0,0,0,0.2) !important;
    }
    
    [data-testid="stSidebarNav"]::before {
        content: "\2699"; /* Unicode pour engrenage ⚙ */
        font-size: 24px;
        display: block;
        text-align: center;
        padding: 10px;
        cursor: pointer;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True
)

# Fonction pour charger et filtrer les données Excel
def load_excel(key_prefix):
    uploaded_file = st.file_uploader(
        f"Charger un fichier Excel ({key_prefix})", 
        type=["xls", "xlsx", "xlsm"], 
        key=f"{key_prefix}_file_uploader"
    )
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            if "CSV" not in excel_data.sheet_names or "Poste" not in excel_data.sheet_names or "Constante" not in excel_data.sheet_names:
                st.error("Le fichier Excel doit contenir les feuilles 'CSV', 'Poste' et 'Constante'.")
                return None, None, None

            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")

            st.success("Fichier chargé avec succès")
            st.write(f"Aperçu des données chargées ({key_prefix}):")
            st.write(data.head())
            return data, positions, constante_data
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier ({key_prefix}) : {e}")
    else:
        st.warning(f"Veuillez charger un fichier Excel ({key_prefix}).")
    return None, None, None

def filter_duration(player_data, min_duration=3900):
    """Filtre les données des joueurs selon la durée minimale."""
    return player_data[player_data["Durée"] >= min_duration]

def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions, module):
    """Affiche les graphiques sélectionnés de manière interactive."""
    for graph in selected_graphs:
        st.subheader(f"Graphique : {graph}")
        if module == "Pôle Féminin":
            fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
        else:
            fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)

        if fig:
            fig.autofmt_xdate()
            st.pyplot(fig)
        else:
            st.error(f"Graphique {graph} non disponible.")

def display_column(key_prefix, shared_graphs):
    data, positions, constante_data = load_excel(key_prefix)

    if data is not None:
        st.write(f"Données disponibles. Sélectionner un joueur ({key_prefix}):")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox(
            f"Sélectionner un joueur/joueuse ({key_prefix})", 
            players, 
            key=f"{key_prefix}_player"
        )

        module = st.selectbox(
            f"Choisir le module d'analyse ({key_prefix})", 
            ["Pôle Féminin", "Pôle Masculin"], 
            key=f"{key_prefix}_module"
        )

        if module == "Pôle Féminin":
            constants = get_feminine_constants(constante_data)
        else:
            constants = get_masculine_constants(constante_data)

        if selected_player:
            st.write(f"Graphiques pour {selected_player} ({module}):")

            filter_matches = st.checkbox(
                f"Afficher les matchs < 3900 secondes ({key_prefix})", 
                value=False, 
                key=f"{key_prefix}_filter"
            )
            player_data = data[data["Joueur"] == selected_player]
            if not filter_matches:
                player_data = filter_duration(player_data)

            if player_data.empty:
                st.warning(f"Aucune donnée à afficher après le filtrage ({key_prefix}).")
            else:
                if shared_graphs:
                    st.write(f"**Graphiques sélectionnés ({key_prefix}):**")
                    display_selected_graphs(shared_graphs, selected_player, constants, player_data, positions, module)

# Sélection des graphiques partagés dans une sidebar pliable
with st.sidebar.expander("⚙️ Configuration des graphiques", expanded=True):
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
        "Nb Décélération > 2m/s²/min"
    ]

    select_all_general = st.checkbox("Sélectionner tous les graphiques généraux")
    select_all_per_min = st.checkbox("Sélectionner tous les graphiques par minute")

    shared_general_graphs = st.multiselect(
        "Choisir les graphiques généraux", 
        general_graphs, 
        default=general_graphs if select_all_general else []
    )
    shared_per_min_graphs = st.multiselect(
        "Choisir les graphiques par minute", 
        per_min_graphs, 
        default=per_min_graphs if select_all_per_min else []
    )

shared_graphs = shared_general_graphs + shared_per_min_graphs

# Diviser la page en deux colonnes pour une comparaison côte à côte
col1, col2 = st.columns(2)

with col1:
    st.header("Joueur 1")
    display_column("col1", shared_graphs)

with col2:
    st.header("Joueur 2")
    display_column("col2", shared_graphs)
