import pandas as pd
import numpy as np
import io
import csv
from datetime import date 
import os

# Daten aus hinterlegten csv laden
def load_csv_from_data(filename: str) -> pd.DataFrame:
    path = os.path.join("data", filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")

    # Trennzeichen automatisch erkennen
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(4096)
        try:
            sep = csv.Sniffer().sniff(sample, delimiters=";,").delimiter
        except Exception:
            sep = ";"

    return pd.read_csv(path, sep=sep)

# Daten verarbeiten
def read_csv(uploaded_file):
    if uploaded_file is None:
        raise ValueError("Keine Datei hochgeladen")

    raw = uploaded_file.getvalue().decode("utf-8", errors="replace")
    try:
        sep = csv.Sniffer().sniff(raw[:4096], delimiters=";,").delimiter
    except Exception:
        sep = ";"
    return pd.read_csv(io.StringIO(raw), sep=sep)
# deutsches Zahlenformet (1.000,00) in Pandas num. Werte (1000.00)
def to_numeric_de(s):
    if pd.api.types.is_numeric_dtype(s):
        return s
    s = s.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce") # Zahl zu Zahl (float)
# erkennen deutsches Datum 
def recognize_date_de(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip().str.replace("T"," ", regex=False)
    dt = pd.to_datetime(x, format="%d.%m.%Y %H:%M:%S", errors="coerce")
    mask = dt.isna()
    dt.loc[mask] = pd.to_datetime(x[mask], format="%d.%m.%Y %H:%M", errors="coerce")
    mask = dt.isna()
    dt.loc[mask] = pd.to_datetime(x[mask], format="%d.%m.%Y", errors="coerce")
    mask = dt.isna()
    dt.loc[mask] = pd.to_datetime(x[mask], dayfirst=True, errors="coerce")
    return dt
# entfernen Leerzeichen in Spaltentiteln der CSV-Dateien
def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [c.strip() for c in out.columns]
    return out
# Validierung Preise
def validate_and_prepare_prices(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_cols(df)
    if "Zeitstempel" not in df.columns or "Strompreis" not in df.columns:
        raise ValueError("Strompreis-CSV muss Spalten 'Zeitstempel' und 'Strompreis' enthalten.")

    out = df[["Zeitstempel", "Strompreis"]].copy()
    out.rename(columns={"Zeitstempel": "timestamp", "Strompreis": "price"}, inplace=True)
    out["timestamp"] = recognize_date_de(out["timestamp"])
    out["price"] = to_numeric_de(out["price"])
    out = out.dropna(subset=["timestamp", "price"]).sort_values("timestamp").reset_index(drop=True)
    out["date"] = out["timestamp"].dt.date
    return out
# Validierung Strommix
def validate_and_prepare_mix(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_cols(df)
    if "Zeitstempel" not in df.columns:
        raise ValueError("Strommix-CSV muss eine Spalte 'Zeitstempel' enthalten.")

    out = df.copy()
    out.rename(columns={"Zeitstempel": "timestamp"}, inplace=True)
    out["timestamp"] = recognize_date_de(out["timestamp"])
    out = out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    # numeric conversion für alle *_MWh Spalten
    for c in out.columns:
        if c != "timestamp":
            out[c] = to_numeric_de(out[c])
    return out
# EE-Anteile
def add_ee_share(mix: pd.DataFrame) -> pd.DataFrame:
    mix = mix.copy()
    ee_cols = ["Wind_Offshore_MWh", "Wind_Onshore_MWh", "Photovoltaik_MWh"]
    all_cols = [c for c in mix.columns if c != "timestamp"]

    ee_cols_present = [c for c in ee_cols if c in mix.columns]
    all_cols_present = [c for c in all_cols if c in mix.columns]

    mix["total_mwh"] = mix[all_cols_present].sum(axis=1, min_count=1)
    if len(ee_cols_present) > 0:
        mix["ee_mwh"] = mix[ee_cols_present].sum(axis=1, min_count=1)
        mix["ee_share"] = np.where(mix["total_mwh"] > 0, mix["ee_mwh"] / mix["total_mwh"], np.nan)
    else:
        mix["ee_mwh"] = np.nan
        mix["ee_share"] = np.nan
    return mix
# Marktindikatoren
def compute_market_indicators(prices_df: pd.DataFrame) -> dict:
    if "price" not in prices_df.columns:
        raise ValueError("Spalte 'price' fehlt")
    prices = prices_df["price"].values
    return {
        "Stunden": len(prices_df),
        "Ø Preis (€/MWh)": float(np.mean(prices)) if len(prices) else np.nan,
        "Median Preis": float(np.median(prices)),
        "Preis-StdAbw (€/MWh)": float(np.std(prices)) if len(prices) else np.nan,
        "Min Preis (€/MWh)": float(np.min(prices)) if len(prices) else np.nan,
        "Max Preis (€/MWh)": float(np.max(prices)) if len(prices) else np.nan,
        "Negative Preisstunden": int(np.sum(prices < 0)) if len(prices) else 0,
        "P05": float(np.percentile(prices,5)),
        "P95": float(np.percentile(prices,95))
    }
                              
# Für Marktdaten
def prepare_market_features(df):
    market_data = df.copy()
    market_data["year"] = market_data["timestamp"].dt.year
    market_data["month"] = market_data["timestamp"].dt.month
    market_data["hour"] = market_data["timestamp"].dt.hour
    market_data["month_dt"] = (
        market_data["timestamp"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    market_data["ee_share_pct"] = market_data["ee_share"] * 100
    return market_data

# EE-Anteile für Analyse
def add_ee_classes(df):

    out = df.copy()

    bins = list(range(0,101,5))

    labels = [
        f"{bins[i]}–{bins[i+1]}%"
        for i in range(len(bins)-1)
    ]

    out["ee_bin"] = pd.cut(
        out["ee_share_pct"],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=False
    )

    out.loc[out["ee_share_pct"] == 100, "ee_bin"] = labels[-1]
    return out

# EE-Anteile und Preise
def compute_ee_price_stats(df):

    return (
        df.groupby("ee_bin", observed=True)["price"]
        .agg(median="median",
            q10=lambda x: x.quantile(0.10),
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
            q90=lambda x: x.quantile(0.90)
        ).reset_index()
    )
def build_market_analysis_frames(df):
    df = prepare_market_features(df)
    df = add_ee_classes(df)

    ee_price_stats = compute_ee_price_stats(df)
    df_analysis = df

    year_stats = (
        df_analysis.groupby("year", as_index=False)
        .agg(
            mean_price=("price", "mean"),
            median_price=("price", "median"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            ee_share_mean=("ee_share_pct", "mean"),
            std_price=("price", "std")
        )
    )

    month_stats = (
        df_analysis.groupby("month_dt", as_index=False)
        .agg(
            mean_price=("price", "mean"),
            median_price=("price", "median"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            ee_share=("ee_share_pct", "mean")
        )
    )

    day_stats = (
        df_analysis.groupby(
            df_analysis["timestamp"].dt.date,
            as_index=False
        )
        .agg(
            mean_price=("price", "mean"),
            median_price=("price", "median"),
        )
    )

    hour_stats = (
        df_analysis.groupby("hour", as_index=False)
        .agg(
            mean_price=("price", "mean"),
            median_price=("price", "median"),
            mean_ee_share=("ee_share", "mean"),
            mean_ee_pct=("ee_share_pct", "mean")
        )
    )
    metrics = compute_market_indicators(df_analysis)

    return {
        "df_analysis": df_analysis,
        "year_stats": year_stats,
        "month_stats": month_stats,
        "day_stats": day_stats,
        "hour_stats": hour_stats,
        "ee_price_stats": ee_price_stats,
        "metrics": metrics
    }
