import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def get_feminine_constants(constante_data):
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
    """Affiche les graphiques féminins pour un joueur donné."""
    player_data = data[data["Joueur"] == player_name].copy()
    player_data = compute_additional_columns(player_data)

    if selected_graph == "Diagramme empilé":
        if all(col in data.columns for col in ["Distance23%", "Distance19%", "Distance%"]):
            sessions = data["Session Title"].fillna("Session inconnue")
            distance23 = data["Distance23%"].fillna(0)
            distance19 = data["Distance19%"].fillna(0)
            distance = data["Distance%"].fillna(0)

            position_row = positions[positions["Joueur"] == player_name]
            if not position_row.empty:
                position = position_row.iloc[0]["Poste"]
                constant23 = constants["Distance23%"].get(position, 0)
                constant19 = constants["Distance19%"].get(position, 0)
                constant = constants["Distance%"].get(position, 0)

                fig, ax = plt.subplots(figsize=(10, 6))

                # Barre "Constante U17"
                bar1 = ax.bar("Constante U17", constant23, color="blue")
                bar2 = ax.bar("Constante U17", constant19, bottom=constant23, color="orange")
                bar3 = ax.bar("Constante U17", constant, bottom=constant23 + constant19, color="green")

                # Ajouter des étiquettes pour la barre "Constante U17"
                for rect in bar1 + bar2 + bar3:
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width() / 2.0, rect.get_y() + height / 2.0, f'{height:.1f}', ha='center', va='center')

                # Barres pour chaque session
                bar4 = ax.bar(sessions, distance23, label="Distance23%", color="light blue")
                bar5 = ax.bar(sessions, distance19, bottom=distance23, label="Distance19%", color="orange")
                bar6 = ax.bar(sessions, distance, bottom=distance23 + distance19, label="Distance%", color="green")

                # Ajouter des étiquettes pour les barres de sessions
                for bar_set in (bar4, bar5, bar6):
                    for rect in bar_set:
                        height = rect.get_height()
                        ax.text(rect.get_x() + rect.get_width() / 2.0, rect.get_y() + height / 2.0, f'{height:.1f}', ha='center', va='center')

                ax.set_title("Répartition des course en %")
                ax.set_xlabel("Match")
                ax.set_ylabel("Distance (%)")
                ax.legend()
                plt.xticks(rotation=45)

                return fig
        else:
            st.warning("Les colonnes Distance23%, Distance19%, et Distance% sont manquantes dans les données.")
            return None

    if selected_graph in player_data.columns:
        # Remplacer les valeurs nulles par zéro
        player_data[selected_graph] = player_data[selected_graph].fillna(0)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(player_data["Session Title"], player_data[selected_graph], marker="o", label=selected_graph)

        position_row = positions[positions["Joueur"] == player_name]
        if not position_row.empty:
            position = position_row.iloc[0]["Poste"]
            constant = constants.get(selected_graph, {}).get(position)
            if constant is not None:
                ax.axhline(y=constant, color="red", linestyle="--", label=f"U17 National ")
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
            if "CSV" not in excel_data.sheet_names or "Poste" not in excel_data.sheet_names:
                st.error("Le fichier Excel doit contenir les feuilles 'CSV' et 'Poste'.")
                return None, None

            data = excel_data.parse("CSV")
            positions = excel_data.parse("Poste")

            st.success("Fichier chargé avec succès")
            return data, positions
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.warning("Veuillez charger un fichier Excel.")
    return None, None

def display_selected_graphs(selected_graphs, player_name, constants, player_data, positions):
    """Affiche les graphiques de manière interactive pour un joueur."""
    for graph in selected_graphs:
        st.subheader(f"Graphique : {graph}")
        fig = plot_feminine_graph(graph, player_name, constants, player_data, positions)
        if fig:
            st.pyplot(fig)

def display_data_table(player_data):
    """Affiche un tableau des données pour un joueur donné."""
    st.subheader("Tableau des données")
    st.dataframe(player_data)

def main():
    st.title("Analyse des Performances des Joueurs/Joueuses")

    # Charger les données
    data, positions = load_excel()
    if data is not None and positions is not None:
        st.write("Données disponibles. Sélectionnez un joueur :")
        players = data["Joueur"].drop_duplicates().tolist()
        selected_player = st.selectbox("Choisir un joueur/joueuse", players)
        constants = get_feminine_constants()

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
                "Diagramme empilé",
                "Tableau des données"
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
                if selected_general_graph == "Tableau des données":
                    display_data_table(player_data)
                elif selected_general_graph:
                    st.subheader("Graphique général")
                    fig = plot_feminine_graph(selected_general_graph, selected_player, constants, player_data, positions)
                    if fig:
                        st.pyplot(fig)

                if selected_per_min_graph:
                    st.subheader("Graphique par minute")
                    fig = plot_feminine_graph(selected_per_min_graph, selected_player, constants, player_data, positions)
                    if fig:
                        st.pyplot(fig)
    else:
        st.warning("Veuillez charger un fichier Excel pour commencer.")

if __name__ == "__main__":
    main()
