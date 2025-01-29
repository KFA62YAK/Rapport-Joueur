import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_masculine_constants(constante_data):
    """Extrait les constantes spécifiques au pôle masculin à partir d'une feuille Excel."""
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
    if "Dist>16kmh" in player_data.columns:
        player_data["Distance > 16km/h"] = player_data["Dist>16kmh"]

    if "Dist>20kmh" in player_data.columns:
        player_data["Distance > 20km/h"] = (player_data["Dist>20kmh"] * 1000)

    if "Dist>20kmh" in player_data.columns and "Durée" in player_data.columns:
        player_data["Distance>20kmh/min"] = (player_data["Dist>20kmh"] * 1000).fillna(0) / (player_data["Durée"].replace(0, 1) / 60)

    if "Distance16" in player_data.columns and "Durée" in player_data.columns:
        player_data["Distance>16kmh/min"] = player_data["Distance16"] / (player_data["Durée"].replace(0, 1) / 60)

    if all(col in player_data.columns for col in ["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²", "Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]):
        player_data["Nb Acc/Dec > 2m/s²"] = player_data[["Nb Acc2>3m/s²", "Nb Acc3>4m/s²", "Nb Acc>4m/s²", "Nb Dec2>3m/s²", "Nb Dec3>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1)

    if "Nb Acc/Dec > 2m/s²" in player_data.columns and "Durée" in player_data.columns:
        player_data["Nb Acc/Dec > 2m/s²/min"] = player_data["Nb Acc/Dec > 2m/s²"].fillna(0) / (player_data["Durée"].replace(0, 1) / 60)

    if all(col in player_data.columns for col in ["Nb Acc>4m/s²", "Nb Dec>4m/s²"]):
        player_data["Nb Acc/Dec > 4m/s²"] = player_data[["Nb Acc>4m/s²", "Nb Dec>4m/s²"]].sum(axis=1)

    if "Nb Acc/Dec > 4m/s²" in player_data.columns and "Durée" in player_data.columns:
        player_data["Nb Acc/Dec > 4m/s²/min"] = player_data["Nb Acc/Dec > 4m/s²"].fillna(0) / (player_data["Durée"].replace(0, 1) / 60)

    return player_data

def plot_masculine_graph(selected_graph, player_name, constants, data, positions):
    """Affiche les graphiques masculins pour un joueur donné."""
    player_data = data[data["Joueur"] == player_name].copy()
    player_data = compute_additional_columns(player_data)

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

                fig, ax = plt.subplots(figsize=(10, 6))

                # Barre "Constante U15"
                bar1 = ax.bar("Constante U15", constant20, color="cyan")
                bar2 = ax.bar("Constante U15", constant16, bottom=constant20, color="orange")
                bar3 = ax.bar("Constante U15", constant, bottom=constant20 + constant16, color="green")

                # Ajouter des étiquettes pour la barre "Constante U15"
                for rect in bar1 + bar2 + bar3:
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2.0, rect.get_y() + height / 2.0, f'{height:.1f}', ha='center', va='center')

                # Barres pour chaque session
                bar4 = ax.bar(sessions, distance20, label="Distance>20", color="cyan")
                bar5 = ax.bar(sessions, distance16, bottom=distance20, label="Distance>16", color="orange")
                bar6 = ax.bar(sessions, distance, bottom=distance20 + distance16, label="Distance<16", color="green")

                # Ajouter des étiquettes pour les barres de sessions
                for bar_set in (bar4, bar5, bar6):
                    for rect in bar_set:
                        height = rect.get_height()
                        ax.text(rect.get_x() + rect.get_width() / 2.0, rect.get_y() + height / 2.0, f'{height:.1f}', ha='center', va='center')

                ax.set_title("Répartition de courses en %")
                ax.set_xlabel("Match")
                ax.set_ylabel("Distance (%)")
                ax.legend()
                plt.xticks(rotation=45)

                return fig
        else:
            st.warning("Les colonnes Distance16%, Distance20%, et Distance% sont manquantes dans les données.")
            return None

    if selected_graph in player_data.columns:
        # Remplacer les valeurs nulles par zéro
        player_data[selected_graph] = player_data[selected_graph].fillna(0)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(player_data["Session Title"], player_data[selected_graph], marker="o",color="green", label=selected_graph)
        # Préparation des données pour la régression
        x = np.arange(len(player_data["Session Title"]))
        y = player_data[selected_graph].values

        # Calcul de la régression linéaire (pente et intercept)
        slope, intercept = np.polyfit(x, y, 1)
        regression_line = slope * x + intercept

        # Tracer la droite de régression
        ax.plot(player_data["Session Title"], regression_line, color="navy", linestyle="-", label="Progression générale")


        position_row = positions[positions["Joueur"] == player_name]
        if not position_row.empty:
            position = position_row.iloc[0]["Poste"]
            constant = constants.get(selected_graph, {}).get(position)
            if constant is not None:
                ax.axhline(y=constant, color="red", linestyle="--", label=f"U15 National")
        ax.set_title(f"{selected_graph} {player_name}")
        ax.set_xlabel("Session")
        ax.set_ylabel("Valeur")
        ax.legend()
        return fig
    else:
        st.warning(f"Données manquantes ou non disponibles pour le graphique : {selected_graph}")
        return None

def load_excel():
    """Charge les données depuis un fichier Excel."""
    uploaded_file = st.file_uploader("Charger un fichier Excel", type=["xls", "xlsx", "xlsm"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            if "CSV" not in excel_data.sheet_names or "Poste" not in excel_data.sheet_names or "Constante" not in excel_data.sheet_names:
                st.error("Le fichier Excel doit contenir les feuilles 'CSV', 'Poste', et 'Constante'.")
                return None, None, None

            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")
            constante_data = excel_data.parse("Constante")

            st.success("Fichier chargé avec succès")
            return data, positions, constante_data
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel.")
    return None, None, None

def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions):
    """Affiche les graphiques de manière interactive pour un joueur."""
    for graph in selected_graphs:
        st.subheader(f"Graphique : {graph}")
        fig = plot_masculine_graph(graph, player_name, constants, player_data, positions)
        if fig:
            st.pyplot(fig)

def main():
    st.title("Analyse des Performances des Joueurs Masculins")

    # Charger les données
    data, positions, constante_data = load_excel()
    if data is not None and positions is not None and constante_data is not None:
        constants = get_masculine_constants(constante_data)
        st.write("Données disponibles. Sélectionnez un joueur :")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox("Choisir un joueur/joueuse", players)

        if selected_player:
            st.write(f"Analyse pour : {selected_player}")

            # Calculer les colonnes dynamiques si nécessaires
            player_data = data[data["Joueur"] == selected_player].copy()
            player_data = compute_additional_columns(player_data)

            # Graphiques généraux
            general_graphs = [
                "Distance",
                "Distance > 16km/h",
                "Distance > 20km/h",
                "TopSpeed",
                "Total Acc > 2m/s²",
                "Total Dec > 2m/s²",
                "Diagramme empilé"
            ]

            # Graphiques par minute
            per_min_graphs = [
                "Distance>20kmh/min",
                "Distance>16kmh/min",
                "Acc > 2m/s²/min",
                "Dec > 2m/s²/min"
            ]

            selected_graph = st.selectbox("Choisissez un graphique à afficher", general_graphs + per_min_graphs)

            # Afficher les graphiques
            if not player_data.empty:
                if selected_graph:
                    st.subheader("Graphique sélectionné")
                    fig = plot_masculine_graph(selected_graph, selected_player, constants, data, positions)
                    if fig:
                        st.pyplot(fig)
    else:
        st.warning("Veuillez charger un fichier Excel pour commencer.")

if __name__ == "__main__":
    main()