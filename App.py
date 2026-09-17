import streamlit as st
import pandas as pd
from datetime import date 
from datetime import timedelta

if "run_calc" not in st.session_state:
    st.session_state.run_calc = False
# -----------------------------
# Layout Page Dashboard
# -----------------------------
st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard")
tab_overview = st.container()

# -----------------------------
# Load Functions
# -----------------------------
from Daten_Vorbereitung import load_csv_from_data
from Daten_Vorbereitung import read_csv
from Daten_Vorbereitung import validate_and_prepare_prices
from Daten_Vorbereitung import validate_and_prepare_mix
from Daten_Vorbereitung import add_ee_share
from Daten_Vorbereitung import build_market_analysis_frames

# -----------------------------
# Tab: Übersicht
# -----------------------------
with tab_overview:
# ----------------------------     
    st.write("Die Berechnung und Analyse erfolgt mit Daten zum Strommix und Strompreisen")
    st.header("1) Datenauswahl")
    st.divider()
    st.subheader("Daten")
    st.divider()
    data_source = st.radio(
        "Datenquelle wählen:",
        ["Hinterlegte Daten", "Eigene CSV hochladen"],
        horizontal=True
    )
    uploaded_prices = None
    uploaded_mix = None

    if data_source == "Hinterlegte Daten":
        # Preis
        df_prices_raw = load_csv_from_data("strompreis.csv")
        df_prices = validate_and_prepare_prices(df_prices_raw)
        # Mix
        df_mix_raw = load_csv_from_data("strommix.csv")
        df_mix = validate_and_prepare_mix(df_mix_raw)
        df_mix = add_ee_share(df_mix)

        st.success("hinterlegte Daten wurden automatisch geladen")
    
    else: # data_source == "Eigene CSV hochladen":
        # Preis
        st.info("CSV muss die Spalten 'Zeitstempel' und 'Strompreis' enthalten.")
        uploaded_prices = st.file_uploader(
                "Strompreis-CSV hochladen",
                type=["csv"])
        if uploaded_prices is None:
            st.warning("Bitte Strompreis-Datei hochladen.")
            st.stop()
        df_prices_custom_raw = read_csv(uploaded_prices)
        df_prices_custom = validate_and_prepare_prices(df_prices_custom_raw)
        # Mix
        st.info("mit Spalten 'Zeitstempel' und 'Quelle_Mwh', wobei Quelle bspw. Steinkohle, Wind_Offshore, etc.")
        uploaded_mix = st.file_uploader(
                "Strommix-CSV hochladen",
                type=["csv"])
        if uploaded_mix is None:
            st.warning("Bitte Strommix-Datei hochladen.")
            st.stop()
        df_mix_custom_raw = read_csv(uploaded_mix)
        df_mix_custom = validate_and_prepare_mix(df_mix_custom_raw)

    # einen Dataframe erzeugen
    if data_source == "Hinterlegte Daten":
        df_data_merged = pd.merge(
                df_prices,
                df_mix,
                on="timestamp",
                how="inner"
            )

    else:
        df_data_merged = pd.merge(
                df_prices_custom,
                df_mix_custom,
                on="timestamp",
                how="inner"
            )

###  
    st.divider()
    st.subheader("Zeitraum")
    st.divider()
# ---- # make time window
    min_day = df_data_merged["timestamp"].min().date()
    max_day = df_data_merged["timestamp"].max().date()

    if "start_d" not in st.session_state or st.session_state.start_d < min_day or st.session_state.start_d > max_day:
        st.session_state.start_d = min_day

    if "end_d" not in st.session_state or st.session_state.end_d < min_day or st.session_state.end_d > max_day:
        st.session_state.end_d = max_day

    if st.session_state.start_d >= st.session_state.end_d:
        st.session_state.start_d = min_day
        st.session_state.end_d = max_day

    if "custom_range" not in st.session_state:
        st.session_state.custom_range = False

    # betrachtbar | in merged df
    st.info(f"Betrachtbarer Zeitraum: "
        f"{min_day.strftime('%d.%m.%Y')} bis {max_day.strftime('%d.%m.%Y')}"
    )

    with st.expander("Anderen Zeitraum wählen", expanded=False):
        user_start = st.date_input("Startdatum wählen",
            value = st.session_state.start_d,
            min_value = min_day,
            max_value = max_day - timedelta(days=1),
            key = "pick_start"
        )
        user_end = st.date_input("Enddatum wählen",
            value = st.session_state.end_d,
            min_value = user_start + timedelta(days=1),
            max_value = max_day,
            key = "pick_end"
        )
        # Anwenden der Auswahl
        if user_start != st.session_state.start_d or user_end != st.session_state.end_d:
            st.session_state.start_d = user_start
            st.session_state.end_d = user_end
            st.session_state.custom_range = True
        # Anzeige Zeitraum
    if st.session_state.custom_range:
        st.success(f"Gewählter Zeitraum: "
            f"{st.session_state.start_d.strftime('%d.%m.%Y')} bis "
            f"{st.session_state.end_d.strftime('%d.%m.%Y')}"
        )
        # Daten nach gewählten Zeitraum filtern
        df_data_merged["timestamp"] = pd.to_datetime(df_data_merged["timestamp"], errors="coerce")
        start_ts = pd.Timestamp(st.session_state.start_d)
        end_ts = pd.Timestamp(st.session_state.end_d) + pd.Timedelta(hours=23)
        st.session_state["start_ts"] = start_ts     # as timestamp
        st.session_state["end_ts"] = end_ts
        df_data = df_data_merged[
            (df_data_merged["timestamp"] >= start_ts) &
            (df_data_merged["timestamp"] <= end_ts)
        ].copy()

    else: 
        df_data = df_data_merged.copy()
    st.divider()
    st.subheader("Speicherparameter")
    st.divider()
    cap_mwh = st.number_input("Kapazität (MWh)", min_value=0.5, max_value=500.0, value=40.0, step=0.5)
    p_mw = st.number_input("Leistung (MW) (Lade=Entlade)", min_value=0.5, max_value=500.0, value=20.0, step=0.5)
    rte = st.slider("Round-Trip-Effizienz (η, RTE)", min_value=0.75, max_value=0.999, value=0.9, step=0.05)
    # Daten im Session State ablegen
    st.session_state["rte"]     = rte            # Wirkungsgrad
    st.session_state["cap_mwh"] = cap_mwh        # Kapazität
    st.session_state["p_mw"]    = p_mw           # Leistung
    st.divider()

# ---------------------------- 
    st.divider()
    st.header("2) Berechnung mit folgenden Daten starten:")
    st.divider()
    col_1, col_2 = st.columns(2)
    with col_1:
        if df_data is not None:
            st.success("Gewählte Daten wurden zur Berechnung vorbereitet und validiert "
                )
            st.session_state["df_data"] = df_data 
 
        st.success("Gewählter Zeitraum: "
                    f"{st.session_state.start_d.strftime('%d.%m.%Y')} bis "
                    f"{st.session_state.end_d.strftime('%d.%m.%Y')}"
                )
        st.success("Gewählte Speicherparameter: \n\n"
            f"Wirkungsgrad: {st.session_state.rte}\n\n"
            f"Kapazität: {st.session_state.cap_mwh} MWh\n\n"
            f"Leistung: {st.session_state.p_mw} MW"
        )
            # Reset to default
    with col_2:
        if df_data is not None:
            with st.expander("Datenvorschau"):
                st.dataframe(df_data.head())     
        if st.button("↩ Reset"):
            st.session_state.start_d = min_day
            st.session_state.end_d = max_day
            st.session_state.custom_range = False
            uploaded_prices = None
            uploaded_mix = None
            st.rerun()

    st.divider()
    if st.button("Berechnung starten", ):
        st.session_state.run_calc = True
    st.divider()

# =============================
# Berechnung gestartet: 
# =============================
    if not st.session_state.run_calc:
        st.stop()
###
# Strommarktdaten
# =============================
    market_results = build_market_analysis_frames(df_data)
    st.session_state["market_results"] = market_results
###
# Battery Model
# =============================
    if st.session_state.run_calc:
        from Battery_Model import compute_all_battery_results
        with st.spinner("Batteriemodell wird berechnet..."):
            results = compute_all_battery_results(
            prices=st.session_state["df_data"][["timestamp", "price"]],
            cap_mwh=st.session_state["cap_mwh"],
            p_mw=st.session_state["p_mw"],
            rte=st.session_state["rte"],
            neg_cost=0,
            life_cost=20
            )

        st.session_state["battery_results"] = results
        st.session_state.run_calc = False
        st.success("Berechnung abgeschlossen")
###
# zurück zur Übersicht -> 3) Navigation einblenden
# ---------------------------- 
    with tab_overview:

        st.header("3) Navigation")
        col_markt, col_speicher = st.columns(2)
        with col_markt:
            st.markdown("## 1) Marktdaten")
            st.write("Analyse und Visualisierung von Strommix & Strompreisen am Day-Ahead-Markt")
            st.page_link("pages/1_Marktdaten.py", label="zu Marktdaten")

        with col_speicher:
            st.markdown("## 2) Batteriespeicher")
            st.write("Simulation des Speicherbetriebs und Erlöspotenzial.")
            st.page_link("pages/2_Batteriespeicher.py", label="zu Batteriespeicher")

