import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots

# Daten aus Session State laden
market = st.session_state.get("market_results")
if market is None:
    st.warning("Keine Daten vorhanden. Bitte zuerst Berechnung starten.")
    st.stop()

df_analysis = market["df_analysis"]
year_stats = market["year_stats"]
month_stats = market["month_stats"]
day_stats = market["day_stats"]
hour_stats = market["hour_stats"]
ee_price_stats = market["ee_price_stats"]
market_stats = market["metrics"]

# Kategorien in strommix.csv
category_cols = [
    "Biomasse_MWh",
    "Wasserkraft_MWh",
    "Wind_Offshore_MWh",
    "Wind_Onshore_MWh",
    "Photovoltaik_MWh",
    "Sonstige_Erneuerbare_MWh",
    "Kernenergie_MWh",
    "Braunkohle_MWh",
    "Steinkohle_MWh",
    "Erdgas_MWh",
    "Pumpspeicher_MWh",
    "Sonstige_MWh",
]
# Kategorien: Ordnung und Farben
CATEGORY_ORDER = [
    "Braunkohle_MWh",
    "Steinkohle_MWh",
    "Erdgas_MWh",
    "Sonstige_MWh",
    "Pumpspeicher_MWh",
    "Kernenergie_MWh",
    "Sonstige_Erneuerbare_MWh",
    "Photovoltaik_MWh",
    "Wind_Offshore_MWh",
    "Wind_Onshore_MWh",
    "Wasserkraft_MWh",
    "Biomasse_MWh",
]
COLOR_MAP = {
    "Braunkohle_MWh": "#8F6635",
    "Steinkohle_MWh": "#000000",
    "Erdgas_MWh": "#B2B2B2",
    "Sonstige_MWh": "#E0E0E0",
    "Pumpspeicher_MWh": "#DB6BBB",
    "Kernenergie_MWh": "#D71717",
    "Sonstige_Erneuerbare_MWh": "#F29000",
    "Photovoltaik_MWh": "#FFD700",
    "Wind_Offshore_MWh": "#0F59C7",
    "Wind_Onshore_MWh": "#669FF4",
    "Wasserkraft_MWh": "#129797",
    "Biomasse_MWh": "#44A22E",
}
    # Rahmen (für weiße Objekte)
WEDGE_PROPS = dict(width=0.45, edgecolor="#DDDDDD", linewidth=1.0)
LABEL_MAP = {c: c.replace("_MWh", "").replace("_", " ") for c in CATEGORY_ORDER}
# =============================
# Page: Marktdaten
# =============================
st.set_page_config(page_title="1) Marktdaten", layout="wide")
st.title("Strommix & Strompreise am Day-Ahead-Markt")
tab_strommix, tab_strompreis, tab_renewables = st.tabs(
            ["Strommix", "Strompreis", "Erneuerbare Energien"])

data = df_analysis
# -----------------------------
# 1. Strommix
# -----------------------------
with tab_strommix:

# Balken-Diagramm: Erzeugung gebündelt und gestapelet    
    st.markdown("## Erzeugungszeitreihe (Monatsbündelung)")
    mode = st.radio("Anzeige", ["gesamt", "gebündelt"], horizontal=True, key="mix_monthly_mode")
    gen_cols = [c for c in CATEGORY_ORDER if c in data.columns]

    if not gen_cols:
        st.warning("Keine passenden Erzeugungsspalten gefunden (erwarte z.B. *_MWh).")
    else:
        monthly = (data.groupby("month_dt")[gen_cols].sum() .reset_index())

        # ----------------------------
        # Kategorisierung für EE-Anteile
        # ----------------------------
        ee_core = ["Photovoltaik_MWh", "Wind_Onshore_MWh", "Wind_Offshore_MWh"]
        ee_core = [c for c in ee_core if c in monthly.columns]

            # Keywords für "EE sonstige" 
        ee_other_keywords = [
            "biomasse", "wasserkraft", "pumpspeicher", "sonstige erneuerbare", "sonstige_erneuerbare"
        ]

        ee_other = []
        for c in gen_cols:
            if c in ee_core:
                continue
            c_low = c.replace("_MWh", "").replace("_", " ").lower()
            if any(k in c_low for k in ee_other_keywords):
                ee_other.append(c)

            # total / shares monatlich
        total_mwh = monthly[gen_cols].sum(axis=1)

        ee_total_mwh = (monthly[ee_core].sum(axis=1) if ee_core else 0) + (monthly[ee_other].sum(axis=1) if ee_other else 0)
        ee_core_mwh = (monthly[ee_core].sum(axis=1) if ee_core else 0)

        ee_total_share = np.where(total_mwh > 0, (ee_total_mwh / total_mwh) * 100, 0.0)
        ee_core_share = np.where(total_mwh > 0, (ee_core_mwh / total_mwh) * 100, 0.0)

        # ----------------------------
        # Diagramm erstellen
        # ----------------------------
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if mode == "gesamt":
            for c in gen_cols:
                fig.add_trace(
                    go.Bar(
                        x=monthly["month_dt"],
                        y=monthly[c],
                        name=LABEL_MAP.get(c, c),
                        marker_color=COLOR_MAP.get(c, "#CCCCCC"),
                    ),
                    secondary_y=False
                )

            title = "Stromerzeugung - alle Technologien (MWh) - monatlich gebündelt"
            fig.update_layout(
                barmode="stack",
                legend=dict(traceorder="normal"),
                title=title,
                hovermode="x unified",
                height=560,
            )
        else: # gebündelt: 3 Gruppen
            conv = [c for c in gen_cols if c not in ee_core and c not in ee_other]

            monthly_grouped = pd.DataFrame({"month_dt": monthly["month_dt"]})
            monthly_grouped["Konventionell + Sonstige"] = monthly[conv].sum(axis=1) if conv else 0
            monthly_grouped["EE sonstige"] = monthly[ee_other].sum(axis=1) if ee_other else 0
            monthly_grouped["EE (PV + Wind)"] = monthly[ee_core].sum(axis=1) if ee_core else 0

            fig.add_trace(
                go.Bar(
                    x=monthly_grouped["month_dt"],
                    y=monthly_grouped["Konventionell + Sonstige"],
                    name="Konventionell + Sonstige",
                    marker_color="#9e9e9e",
                ),
                secondary_y=False
            )
            fig.add_trace(
                go.Bar(
                    x=monthly_grouped["month_dt"],
                    y=monthly_grouped["EE sonstige"],
                    name="EE sonstige",
                    marker_color="#1B5E20",
                ),
                secondary_y=False
            )
            fig.add_trace(
                go.Bar(
                    x=monthly_grouped["month_dt"],
                    y=monthly_grouped["EE (PV + Wind)"],
                    name="EE (PV + Wind)",
                    marker_color="#66BB6A",
                ),
                secondary_y=False
            )

            title = "Monatliche Stromerzeugung – EE gebündelt vs. konventionell (MWh)"

            # Layout / Achsen
        fig.update_layout(
            barmode="stack",
            title=title,
            hovermode="x unified",
            legend_title_text="",
            margin=dict(l=10, r=10, t=60, b=10),
            height=560
        )
        fig.update_xaxes(title_text="Monat")
        fig.update_yaxes(title_text="Erzeugung (MWh)")

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Spaltenzuordnung anzeigen"):
            st.write("**EE (PV + Wind):**", ee_core if ee_core else "—")
            st.write("**EE sonstige:**", ee_other if ee_other else "—")
            st.write("**Konventionell + Sonstige:**", [c for c in gen_cols if c not in ee_core and c not in ee_other] if gen_cols else "—")

### Bar Chart Erzeuger Anteile
    st.subheader("Jährliche Strommix-Anteile")

    mix_long = (data.assign(year=data["timestamp"].dt.year)
        .groupby("year")[category_cols].sum().reset_index()
        .melt(id_vars="year", var_name="Technologie", value_name="MWh")
    )

    mix_long["Anteil"] = (
        mix_long["MWh"] / mix_long.groupby("year")["MWh"].transform("sum") * 100
    )

    fig_mix_share = px.bar(mix_long,
        x="year",
        y="Anteil",
        color="Technologie",
        color_discrete_map=COLOR_MAP,
        barmode="stack",
        labels={"year": "Jahr",
                "Anteil": "Anteil [%]",
                "Technologie": "" },
                category_orders={"Technologie": CATEGORY_ORDER},
        title="Zusammensetzung des Strommixes nach Jahr"
    )

    fig_mix_share.update_layout(
        yaxis_title="Anteil [%]",
        xaxis_title="Jahr",
        legend_title="",
        hovermode="x unified"
    )

    st.plotly_chart(fig_mix_share, use_container_width=True)

# -----------------------------
# 2. Strompreis
# -----------------------------
with tab_strompreis:
### Marktdaten
    st.subheader("Kennzahlen")
    col1, col2, col3 = st.columns(3)

    col1.metric("Ø Strompreis", f"{market_stats['Ø Preis (€/MWh)']:.1f}")

    col2.metric("Preis-StdAbw", f"{market_stats['Preis-StdAbw (€/MWh)']:.1f}")

    col3.metric("Negative Preisstunden", market_stats["Negative Preisstunden"])

### Strompreis-Zeitreihen
    st.subheader("Strompreis-Zeitreihe nach Jahr")

    df = pd.DataFrame({
        "Jahr": data["timestamp"].dt.year,
        "Tag": data["timestamp"].dt.dayofyear,
        "price": data["price"]
    })

    # Tagesmittel (statt Stundenwerte)
    df = df.groupby(["Jahr", "Tag"], as_index=False)["price"].mean()
    years = sorted(df["Jahr"].unique())

    # Farbgebung
    def hex_to_rgba(hex_color, alpha=0.65):
        hex_color = hex_color.lstrip("#")
        return f"rgba({int(hex_color[0:2],16)},{int(hex_color[2:4],16)},{int(hex_color[4:6],16)},{alpha})"

    palette = (px.colors.qualitative.Plotly + px.colors.qualitative.Safe + px.colors.qualitative.Set2)[:len(years)]
    colors = {y: hex_to_rgba(c, 0.65) for y, c in zip(years, palette)}

    fig = go.Figure()
    for y in years:
        d = df[df["Jahr"] == y]
        fig.add_trace(go.Scatter(
            x=d["Tag"],
            y=d["price"],
            mode="lines",
            name=str(y),
            line=dict(color=colors[y], width=2)
        ))
    fig.update_layout(
        title="Entwicklung der Day-Ahead-Strompreise nach Kalenderjahr",
        xaxis_title="Monat",
        yaxis_title="Durchschnittlicher Tagespreis [€/MWh]",
        legend_title="Jahr",
        hovermode="x unified"
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=[15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349],
        ticktext=["Jan", "Feb", "Mrz", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    )

    st.plotly_chart(fig, use_container_width=True)

### Verteilung als Linien-Diagramm Strompreise
    st.subheader("Verteilung der Strompreise nach Jahr")

    fig_density = go.Figure()
    line_colors = {y: hex_to_rgba(c, 0.4)
        for y, c in zip(years, palette) }

    for year, group in data.groupby("year"):
        values = group["price"].dropna()
        if values.empty:
            continue
        y_hist, bins = np.histogram(
            values,
            bins=200,
            density=True
        )

        x_hist = (bins[:-1] + bins[1:]) / 2

        fig_density.add_trace(
            go.Scatter(
                x=x_hist,
                y=y_hist,
                mode="lines",
                name=str(year),
                line=dict(color=line_colors[year], width=3)
            )
        )

    fig_density.update_layout(
        title="Preisverteilung nach Jahr",
        xaxis_title="Strompreis (€/MWh)",
        yaxis_title="Relative Häufigkeit",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_density,
        use_container_width=True
    )
# Tabelle Statistik 
    with st.expander("Preisstatistik nach Jahr", expanded=False):

        stats_df = (data.groupby("year")["price"].agg(
                Mittelwert="mean",
                Median="median",
                Minimum="min",
                Maximum="max",
                Std_Abw="std",
                P05=lambda x: x.quantile(0.05),
                P95=lambda x: x.quantile(0.95)
            ).reset_index().rename(columns={"year": "Jahr"})
        )
        stats_df["90%-Spanne"] = stats_df["P95"] - stats_df["P05"]
        stats_df["Gesamtspanne"] = (stats_df["Maximum"] - stats_df["Minimum"])
        stats_df = stats_df.round(2)
# Tabelle als df erzeugen mit deutschen Zahlenformat
        st.dataframe(
            stats_df.style.format({
                "Mittelwert": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "Median": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "Minimum": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "Maximum": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "Std_Abw": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "P05": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "P95": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "90%-Spanne": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
                "Gesamtspanne": lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."),
            }),
            use_container_width=True,
            hide_index=True
        )

    st.divider()
# =============================
# 3. Erneuerbare Energien – Erzeugung & Anteil
# =============================
with tab_renewables:
    st.subheader("Anteil Erneuerbarer am Strommix")
    monthly_ee = month_stats.copy()
    # Monats-Labels erzeugen (Deutsch)
    month_map = {   "Jan": "Jan", "Feb": "Feb", "Mar": "Mär", "Apr": "Apr",
                    "May": "Mai", "Jun": "Jun", "Jul": "Jul", "Aug": "Aug",
                    "Sep": "Sep", "Oct": "Okt", "Nov": "Nov", "Dec": "Dez"  }
    monthly_ee["month_str"] = monthly_ee["month_dt"].dt.strftime("%b %Y")
    monthly_ee["month_str"] = monthly_ee["month_str"].apply(lambda x: month_map[x.split()[0]] + " " + x.split()[1])
    # Trendlinie
    x = np.arange(len(monthly_ee))
    y = monthly_ee["ee_share"].values
    trend = np.poly1d(np.polyfit(x, y, 1))(x)
    # Plot
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(monthly_ee["month_str"], monthly_ee["ee_share"], label="Ø EE-Anteil pro Monat", color="#85BCF5")
    ax1.plot(monthly_ee["month_str"], trend, label="Trend", color="#FFD700", linestyle="--", linewidth=1)
    # Anpassung Label x-Achse (Mär, Jun, Sep, Dez)
    ticks_idx = [i for i, d in enumerate(monthly_ee["month_dt"])
        if d.month % 3 == 0]
    ticks_labels = [monthly_ee["month_str"].iloc[i] for i in ticks_idx]
    ax1.set_xticks(ticks_idx)
    ax1.set_xticklabels(ticks_labels, rotation=45)
    ax1.set_title("Durchschnittlicher EE-Anteil pro Monat")
    ax1.set_ylabel("EE-Anteil [%]")
    ax1.set_xlabel("Monat")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()  
    st.pyplot(fig1, use_container_width=True)
    st.divider()

### Tagesverlauf EE-Anteile
    st.divider()
    st.subheader("Durchschnittlicher Tagesverlauf des EE-Anteils")

    fig_day = px.line(hour_stats,
        x="hour",
        y="mean_ee_pct",
        markers=True,
        labels={
            "hour": "Stunde des Tages",
            "mean_ee_pct": "EE-Anteil [%]"
        },
        title="Durchschnittlicher EE-Anteil im Tagesverlauf"
    )

    fig_day.update_layout(
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1
        ),
        yaxis_title="EE-Anteil [%]"
    )

    st.plotly_chart(fig_day, use_container_width=True)

### Strompreis und EE-Anteil
    st.divider()
    st.header("Strompreise und EE-Anteile")

# Scatter Preis vs EE-Anteil im ausgewählten Zeitraum
    st.divider()
    st.subheader("Preis vs. EE-Anteil (Scatter) - im ausgewählten Zeitraum")

    fig_scatter = px.scatter(data,
        x="ee_share_pct",
        y="price",
        labels={
            "ee_share_pct": "EE-Anteil [%]",
            "price": "Preis [€/MWh]"
        },
        title="Day-Ahead Preis vs. EE-Anteil"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)
# Heat-Map 
    heat_map = px.density_heatmap(data,
        x="ee_share_pct",
        y="price",
        nbinsx=20,
        nbinsy=50,
        color_continuous_scale="Viridis",
        labels={"ee_share_pct": "EE-Anteil [%]",
                "price": "Strompreis [€/MWh]"},
        title="Preis-Häufigkeit in Abhängigkeit vom EE-Anteil"
    )

    st.plotly_chart(heat_map, use_container_width=True)

# Median mit Quantilband 
    st.subheader("Medianstrompreis mit Quantilbändern")
    fig_quantile = go.Figure()
    agg = ee_price_stats
    # 10-90 Quantil
    fig_quantile.add_trace(go.Scatter(
            x=agg["ee_bin"],
            y=agg["q90"],
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False)
    )
    fig_quantile.add_trace(
        go.Scatter(
            x=agg["ee_bin"],
            y=agg["q10"],
            fill="tonexty",
            fillcolor="rgba(2,85,220,0.2)",
            line=dict(color="rgba(0,0,0,0)"),
            name="10%-90%-Band")
    )
    # 25-75 Quantil
    fig_quantile.add_trace(
        go.Scatter(
            x=agg["ee_bin"],
            y=agg["q75"],
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False
        )
    )
    fig_quantile.add_trace(
        go.Scatter(
            x=agg["ee_bin"],
            y=agg["q25"],
            fill="tonexty",
            fillcolor="rgba(2,85,220,0.35)",
            line=dict(color="rgba(0,0,0,0)"),
            name="25%-75%-Quantil"
        )
    )
    # Median
    fig_quantile.add_trace(
        go.Scatter(
            x=agg["ee_bin"],
            y=agg["median"],
            mode="lines+markers",
            line=dict(color="#0255DC", width=3),
            name="Median")
    )
    fig_quantile.update_layout(
        title="Median-Strompreis mit Quantilband",
        xaxis_title="EE-Anteil-Klasse",
        yaxis_title="Preis (€/MWh)",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_quantile, use_container_width=True)

# Boxplot Strompreise nach EE-Klassen
    st.divider()
    st.subheader("Strompreise nach EE-Anteil-Klassen (Boxplot)")

    bins = list(range(0, 101, 5))
    labels = [f"{bins[i]}–{bins[i+1]}%" for i in range(len(bins)-1)]

    fig_box = px.box(data,
        x="ee_bin", y="price",
        color="ee_bin",
        category_orders={"ee_bin": labels},
        labels={"ee_bin": "EE-Anteil-Klasse",
            "price": "Strompreis (€/MWh)"},
        title="Strompreisverteilung nach EE-Anteil-Klassen"
    )
    fig_box.update_layout(
        showlegend=False,
        xaxis_tickangle=-45,
        height=600
    )
    st.plotly_chart(fig_box, use_container_width=True)
