import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PFtest import plot_feminine_graph, get_feminine_constants
from PMtest import plot_masculine_graph, get_masculine_constants
import os

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
# Fonction de chargement d'un fichier Excel pour une colonne donnée
# -----------------------------
def load_excel(key_prefix):
    uploaded_file = st.file_uploader(
        f"Charger un fichier Excel ({key_prefix})", 
        type=["xls", "xlsx", "xlsm"], 
        key=f"{key_prefix}_file_uploader"
    )
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            required_sheets = {"CSV", "Poste", "Constante"}
            missing_sheets = required_sheets - set(excel_data.sheet_names)
            if missing_sheets:
                st.error(f"Le fichier doit contenir les feuilles {', '.join(required_sheets)}. Manquantes : {', '.join(missing_sheets)}")
                return None, None, None
            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")
            st.success("Fichier chargé avec succès")
            st.write("Aperçu des données:")
            st.write(data.head())
            return data, positions, constante_data
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier ({key_prefix}) : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel.")
    return None, None, None

def filter_duration(player_data, min_duration=3900):
    """Filtre les données selon la durée minimale."""
    return player_data[player_data["Durée"] >= min_duration]

def compute_additional_columns(player_data):
    """Calcule les colonnes dynamiques nécessaires pour certains graphiques."""
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
# Fonctions de tracé
# -----------------------------
def plot_masculine_graph(selected_graph, player_name, constants, data, positions):
    """Trace les graphiques masculins pour un joueur donné en utilisant Plotly."""
    player_data = data[data["Joueur"] == player_name].copy()
    player_data = compute_additional_columns(player_data)
    # Diagramme empilé
    if selected_graph == "Diagramme empilé":
        if all(col in data.columns for col in ["Distance16%", "Distance20%", "Distance%"]):
            sessions = data["Session Title"].fillna("Session inconnue")
            distance16 = data["Distance16%"].fillna(0)
            distance20 = data["Distance20%"].fillna(0)
            distance = data["Distance%"].fillna(0)
            position_row = positions[positions["Joueur"] == player_name]
            if not position_row.empty:
                position = position_row.iloc[0]["Poste"]
                constant20 = constants.get("Distance20%", {}).get(position, 0)
                constant16 = constants.get("Distance16%", {}).get(position, 0)
                constant = constants.get("Distance%", {}).get(position, 0)
                df_constante = pd.DataFrame({
                    'Session': ['Constante U15']*3,
                    'Type': ['Distance>20', 'Distance>16', 'Distance<16'],
                    'Valeur': [constant20, constant16, constant]
                })
                df_sessions = pd.DataFrame({
                    'Session': sessions,
                    'Distance>20': distance20,
                    'Distance>16': distance16,
                    'Distance<16': distance
                })
                df_sessions_long = df_sessions.melt(id_vars="Session", value_vars=['Distance>20', 'Distance>16', 'Distance<16'],
                                                      var_name='Type', value_name='Valeur')
                df_combined = pd.concat([df_constante, df_sessions_long], ignore_index=True)
                fig = px.bar(df_combined, x='Session', y='Valeur', color='Type', barmode='stack', text_auto=True,
                             title="Répartition de courses en %")
                fig.update_layout(xaxis_title="Match", yaxis_title="Distance (%)", xaxis_tickangle=45)
                return fig
        else:
            st.warning("Les colonnes Distance16%, Distance20% et Distance% sont manquantes.")
            return None
    # Graphiques en courbe (avec régression et ligne constante)
    if selected_graph in player_data.columns:
        player_data[selected_graph] = player_data[selected_graph].fillna(0)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=player_data["Session Title"],
            y=player_data[selected_graph],
            mode="lines+markers",
            name=selected_graph,
            line=dict(color="blue")
        ))
        x = np.arange(len(player_data["Session Title"]))
        y = player_data[selected_graph].values
        slope, intercept = np.polyfit(x, y, 1)
        regression_line = slope * x + intercept
        fig.add_trace(go.Scatter(
            x=player_data["Session Title"],
            y=regression_line,
            mode="lines",
            name="Progression générale",
            line=dict(color="navy")
        ))
        position_row = positions[positions["Joueur"] == player_name]
        if not position_row.empty:
            position = position_row.iloc[0]["Poste"]
            constant_val = constants.get(selected_graph, {}).get(position)
            if constant_val is not None:
                fig.add_trace(go.Scatter(
                    x=[player_data["Session Title"].iloc[0], player_data["Session Title"].iloc[-1]],
                    y=[constant_val, constant_val],
                    mode="lines",
                    name="U15 National",
                    line=dict(color="red", dash="dash")
                ))
        fig.update_layout(
            title=f"{selected_graph} - {player_name}",
            xaxis_title="Session",
            yaxis_title="Valeur",
            xaxis_tickangle=45
        )
        return fig
    else:
        st.warning(f"Données manquantes pour le graphique : {selected_graph}")
        return None

def plot_feminine_graph(selected_graph, player_name, constants, data, positions):
    """Trace les graphiques pour le pôle féminin en utilisant Plotly (similaire à la logique masculine)."""
    return plot_masculine_graph(selected_graph, player_name, constants, data, positions)

# -----------------------------
# Affichage en deux colonnes pour la comparaison
# -----------------------------
def display_column_comparison(key_prefix, shared_graphs):
    # Chaque colonne charge son fichier Excel dans son bloc de mise en forme
    data, positions, constante_data = load_excel(key_prefix)
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
        st.warning(f"Veuillez charger un fichier Excel pour {key_prefix}.")

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
            "Distance>20kmh/min",
            "Distance>16kmh/min",
            "Nb Acc/Dec > 2m/s²/min",
            "Nb Acc/Dec > 4m/s²/min"
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

# -----------------------------
# Comparaison en deux colonnes avec chargement de fichiers distincts
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    st.header("Joueur 1")
    display_column_comparison("col1", shared_graphs)
with col2:
    st.header("Joueur 2")
    display_column_comparison("col2", shared_graphs)
