import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os

def get_feminine_constants(constante_data):
    """Extrait les constantes spécifiques au pôle féminin à partir d'une feuille Excel."""
    constants = {}
    for _, row in constante_data.iterrows():
        indicator = row["Unnamed: 0"]
        constants[indicator] = {
            "AT": row["AT"],
            "AIL": row["AIL"],
            "MIL": row["MIL"],
            "DC": row["DC"],
            "DL": row["DL"],
            "GB": row["GB"]
        }
    return constants

def compute_additional_columns(player_data):
    """Calcule les colonnes dynamiques nécessaires pour certains graphiques."""
    if all(col in player_data.columns for col in ["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²"]):
        player_data["Accélérations > 2m/s²"] = player_data[["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²"]].sum(axis=1)

    if all(col in player_data.columns for col in ["Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]):
        player_data["Décélérations > 2m/s²"] = player_data[["Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1)

    if "Distance > 19km/h" in player_data.columns:
        player_data["Distance > 19km/h"] = player_data["Distance > 19km/h"]
        
    if "Distance19" in player_data.columns:
        player_data["Distance > 19kmh/min"] = player_data["Distance19"] / (player_data["Durée"] / 60)

    if "Dist>23kmh" in player_data.columns:
        player_data["Distance > 23km/h"] = player_data["Dist>23kmh"] * 1000  # Convertir en mètres

    if all(col in player_data.columns for col in ["Dist>23kmh", "Durée"]):
        player_data["Distance>23kmh/min"] = (player_data["Dist>23kmh"] * 1000) / (player_data["Durée"] / 60)

    if all(col in player_data.columns for col in ["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²", "Durée"]):
        player_data["Nb Accélération > 2m/s²/min"] = player_data[["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²"]].sum(axis=1) / (player_data["Durée"] / 60)
    
    if all(col in player_data.columns for col in ["Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²", "Durée"]):
        player_data["Nb Décélération > 2m/s²/min"] = player_data[["Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1) / (player_data["Durée"] / 60)

    return player_data

def plot_feminine_graph(selected_graph, player_name, constants, data, positions):
    """Affiche les graphiques féminins pour un joueur donné en utilisant Plotly."""
    player_data = data[data["Joueur"] == player_name].copy()
    player_data = compute_additional_columns(player_data)

    # Cas du diagramme empilé
    if selected_graph == "Diagramme empilé":
        if all(col in data.columns for col in ["Distance23%", "Distance19%", "Distance%"]):
            sessions = data["Session Title"].fillna("Session inconnue")
            distance23 = data["Distance23%"].fillna(0)
            distance19 = data["Distance19%"].fillna(0)
            distance = data["Distance%"].fillna(0)

            position_row = positions[positions["Joueur"] == player_name]
            if not position_row.empty:
                position = position_row.iloc[0]["Poste"]
                constant23 = constants.get("Distance23%", {}).get(position, 0)
                constant19 = constants.get("Distance19%", {}).get(position, 0)
                constant = constants.get("Distance%", {}).get(position, 0)

                # Préparation du dataframe pour la barre constante
                df_constante = pd.DataFrame({
                    'Session': ['Constante U17'] * 3,
                    'Type': ['Distance23%', 'Distance19%', 'Distance%'],
                    'Valeur': [constant23, constant19, constant]
                })

                # Préparation du dataframe pour les sessions
                df_sessions = pd.DataFrame({
                    'Session': sessions,
                    'Distance23%': distance23,
                    'Distance19%': distance19,
                    'Distance%': distance
                })
                df_sessions_long = df_sessions.melt(id_vars="Session", 
                                                    value_vars=['Distance23%', 'Distance19%', 'Distance%'],
                                                    var_name='Type', value_name='Valeur')
                df_combined = pd.concat([df_constante, df_sessions_long], ignore_index=True)

                fig = px.bar(df_combined, x='Session', y='Valeur', color='Type', barmode='stack', text_auto=True,
                             title="Répartition des Distances de course en %")
                fig.update_layout(xaxis_title="Match", yaxis_title="Distance (%)", xaxis_tickangle=45)
                return fig
        else:
            st.warning("Les colonnes Distance23%, Distance19% et Distance% sont manquantes dans les données.")
            return None

    # Cas des graphiques en courbe
    if selected_graph in player_data.columns:
        player_data[selected_graph] = player_data[selected_graph].fillna(0)

        # Créer une figure avec go.Figure pour pouvoir ajouter des légendes à chaque trace
        fig = go.Figure()

        # Trace principale : données
        fig.add_trace(go.Scatter(
            x=player_data["Session Title"],
            y=player_data[selected_graph],
            mode="lines+markers",
            name=selected_graph,
            line=dict(color="blue")
        ))

        # Calcul de la régression linéaire
        x = np.arange(len(player_data["Session Title"]))
        y = player_data[selected_graph].values
        slope, intercept = np.polyfit(x, y, 1)
        regression_line = slope * x + intercept

        # Trace de la régression linéaire
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
                # Trace de la ligne constante pour la norme U17
                fig.add_trace(go.Scatter(
                    x=[player_data["Session Title"].iloc[0], player_data["Session Title"].iloc[-1]],
                    y=[constant_val, constant_val],
                    mode="lines",
                    name="U17 National",
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
        st.warning(f"Données manquantes ou non disponibles pour le graphique : {selected_graph}")
        return None

def load_excel_main():
    """Charge les données depuis un fichier Excel."""
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xls", "xlsx", "xlsm"])
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
            st.write("Aperçu des données chargées:")
            st.write(data.head())
            return data, positions, constante_data
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel.")
    return None, None, None

def display_selected_graphs_main(selected_graphs, player_name, constants, player_data, positions):
    """Affiche les graphiques de manière interactive pour un joueur en utilisant Plotly."""
    for graph in selected_graphs:
        st.subheader(f"Graphique : {graph}")
        fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
        if fig:
            st.plotly_chart(fig)
        else:
            st.error(f"Graphique {graph} non disponible.")

def main():
    st.title("Analyse des Performances des Joueurs/Joueuses")

    # Charger les données
    data, positions, constante_data = load_excel_main()
    if data is not None and positions is not None and constante_data is not None:
        st.write("Données disponibles. Sélectionnez un joueur :")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox("Choisir un joueur/joueuse", players)
        constants = get_feminine_constants(constante_data)

        if selected_player:
            st.write(f"Analyse pour : {selected_player}")

            # Calculer les colonnes dynamiques si nécessaires
            player_data = data[data["Joueur"] == selected_player].copy()
            player_data = compute_additional_columns(player_data)

            # Graphiques généraux
            general_graphs = [
                "Distance",
                "Distance > 19km/h",
                "Distance > 23km/h",
                "TopSpeed",
                "Accélérations > 2m/s²",
                "Décélérations > 2m/s²",
                "Diagramme empilé"
            ]

            # Graphiques par minute
            per_min_graphs = [
                "Dist/min",
                "Distance>23kmh/min",
                "Distance > 19kmh/min",
                "Nb Accélération > 2m/s²/min",
                "Nb Décélération > 2m/s²/min"
            ]

            selected_general_graph = st.selectbox("Choisissez un graphique général à afficher", general_graphs)
            selected_per_min_graph = st.selectbox("Choisissez un graphique par minute à afficher", per_min_graphs)

            # Afficher les graphiques
            if not player_data.empty:
                if selected_general_graph:
                    st.subheader("Graphique général")
                    fig = plot_feminine_graph(selected_general_graph, selected_player, constants, player_data, positions)
                    if fig:
                        st.plotly_chart(fig)
                if selected_per_min_graph:
                    st.subheader("Graphique par minute")
                    fig = plot_feminine_graph(selected_per_min_graph, selected_player, constants, player_data, positions)
                    if fig:
                        st.plotly_chart(fig)
    else:
        st.warning("Veuillez charger un fichier Excel pour commencer.")

if __name__ == "__main__":
    main()
