import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd

# Sidebar 
if (st.session_state.get("run_calc", False)
    and "start_d" in st.session_state
    and "end_d" in st.session_state):
    st.sidebar.divider()
    # Zeitraum
    st.sidebar.subheader("Zeitraum")
    st.sidebar.info(f"{st.session_state.start_d.strftime('%d.%m.%Y')} "
        f"bis "
        f"{st.session_state.end_d.strftime('%d.%m.%Y')}"
    )
    st.sidebar.divider()
    # Speicherparameter
    st.sidebar.subheader("Speicherparameter")
    st.sidebar.metric("Kapazität", f"{st.session_state['cap_mwh']:.1f} MWh")
    st.sidebar.metric("Leistung", f"{st.session_state['p_mw']:.1f} MW")
    st.sidebar.metric("RTE", f"{st.session_state['rte']:.1%}")
    st.sidebar.divider()
# Ergebnisse laden
analysis_results = st.session_state.get("battery_results")

if analysis_results is None:
    st.warning("Bitte zuerst Berechnung durchführen")
    st.stop()

df_results = analysis_results["df_analysis"]
df_operation = analysis_results["df_operation"]
year_stats = analysis_results["year_stats"]
month_stats = analysis_results["month_stats"]
day_stats = analysis_results["day_stats"]
hour_stats = analysis_results["hour_stats"]
cost_analysis = analysis_results["cost_analysis"]
m = analysis_results["metrics"]
yearly_metrics = analysis_results["metrics"]["yearly_activity_metrics"]
# Colour-Coding einführen
COLOURS = {
"revenue": "#247E24",
"cost": "#A52020",
"profit": "#1F77B4",
"charge": "#D7975E",
"discharge":  "#60B161",
"soc": "#FFD700"}

# --------------------------
# Tabs
# --------------------------
tab_results, tab_betrieb, tab_cost, tab_dl = st.tabs(["Zusammenfassung", "Speicherbetrieb", "Kosten & Erlöse", "Daten-Download"])

with tab_results:
    col_1, col_2, col_3 = st.columns(3, vertical_alignment="center", gap = "large")
    with col_1:
        st.metric("Gesamterlöse", f'{m["total_revenue"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Erlöse je MWh", f'{m["revenue_per_mwh"]:,.2f} €/MWh'.replace(",", "X").replace(".", ",").replace("X", "."))
    with col_2:
        st.metric("Gesamtkosten", f'{m["total_cost_full"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Kosten je MWh", f'{m["cost_per_mwh"]:,.2f} €/MWh'.replace(",", "X").replace(".", ",").replace("X", "."))
    with col_3:
        st.metric("Gesamtprofit", f'{m["total_profit"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
        st.metric("Profit je MWh", f'{m["profit_per_mwh"]:,.2f} €/MWh'.replace(",", "X").replace(".", ",").replace("X", "."))
# Ergebnistabelle
    year_stats_display = year_stats.copy()
    # Spaltennamen
    year_stats_display = year_stats_display.rename(columns={
        "year": "Jahr",
        "revenue": "Erlöse [€]",
        "cost_buy": "Einkaufskosten [€]",
        "cost_var": "Variable Kosten [€]",
        "cost": "Kosten [€]",
        "profit": "Profit [€]",
        "e_in": "Geladen [MWh]",
        "e_out": "Entladen [MWh]",
        "cycles_op": "Betriebszyklen",
        "cycles_efc": "Vollzyklen",
        "profit_per_op_cycle": "Profit/Betriebszyklus [€]",
        "profit_per_efc": "Profit/Vollzyklus [€]"
    })
    # Deutsches Zahlenformat
    for col in [
        "Erlöse [€]",
        "Einkaufskosten [€]",
        "Variable Kosten [€]",
        "Kosten [€]",
        "Profit [€]",
        "Profit/Betriebszyklus [€]",
        "Profit/Vollzyklus [€]"
        ]:
        year_stats_display[col] = year_stats_display[col].apply(
            lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    # Ganzzahlen
    for col in ["Geladen [MWh]", "Entladen [MWh]", "Betriebszyklen"]:
        year_stats_display[col] = year_stats_display[col].apply(
            lambda x: f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    # Vollzyklen
    year_stats_display["Vollzyklen"] = year_stats_display["Vollzyklen"].apply(
        lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.dataframe(year_stats_display, use_container_width=True, hide_index=True)
# Jahresergebnisse
    st.subheader("Jahresergebnisse")
    st.markdown("---")
    fig_year = px.bar(
        year_stats,
        x="year",
        y=["revenue", "cost", "profit"],
        barmode="group",
        title="Jährliche Erlöse, Kosten und Gewinne",
        labels={
            "value": "Betrag [€]",
            "year": "Jahr"
        },
        color_discrete_map={
            "revenue": COLOURS["revenue"],
            "cost": COLOURS["cost"],
            "profit": COLOURS["profit"]
        }
    )
    st.plotly_chart(fig_year, use_container_width=True,key="yearly_results")


    # Kosten vs. Erlöse - Overlay Profit
    st.markdown("---")
    fig_rev_cost = px.bar(month_stats,
        x="month",
        y="revenue",
        title="Erlöse & Profit - Monatliche Entwicklung",
        labels={"month": "Monat",
            "revenue": "Betrag [€]"},
    )
    fig_rev_cost.update_traces(
        marker_color=COLOURS["revenue"]
    )
    fig_rev_cost.add_trace(go.Scatter(
        x=month_stats["month"],
        y=month_stats["profit"],
        mode="lines+markers",
        name="Profit",
        line=dict(
            color=COLOURS["profit"],
            width=2),
        yaxis="y2")
    )
    fig_rev_cost.update_layout(
        yaxis=dict(title="Erlöse [€]"),
        yaxis2=dict(title="Profit [€]", overlaying="y", side="right", showgrid=False),
    )

    st.plotly_chart(fig_rev_cost, use_container_width=True, key="rev_cost")

# Profit pro Zyklus 
    st.markdown("---")
    fig = go.Figure()
    fig.add_bar(
        x=month_stats["month"],
        y=month_stats["cycles_efc"],
        name="Vollzyklen (EFC)",
        marker_color="rgba(40,137,228,0.65)")
    fig.add_trace(
        go.Scatter(
            x=month_stats["month"],
            y=month_stats["profit_per_efc"],
            name="Profit je Vollzyklus",
            mode="lines+markers",
            marker=dict(
                symbol="square",
                size=6,
                color="#2889E4"),
            line=dict(
                color="#2889E4",
                width=3,
                dash="dot"),
            yaxis="y2"
        )
    )

    fig.add_bar(
        x=month_stats["month"],
        y=month_stats["cycles_op"],
        name="Betriebszyklen",
        marker_color="rgba(241,153,20,0.65)")
    fig.add_trace(
        go.Scatter(
            x=month_stats["month"],
            y=month_stats["profit_per_op_cycle"],
            name="Profit je Betriebszyklus",
            mode="lines+markers",
            marker=dict(
                symbol="circle",
                size=6,
                color="#F19914"
            ),
            line=dict(
                color="#F19914",
                width=3,
                dash="dot"
            ),
            yaxis="y2")
    )

    fig.update_layout(
        barmode="group",
        xaxis_title="Monat",
        yaxis=dict(title="Zyklen"),
        yaxis2=dict(title="Profit [€]", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.12),
        height=650)
    st.plotly_chart(fig, use_container_width=True, key="profit_and_cycles")

# Laden | Entladen und SoC - für einen ausgewählten Monat
    st.markdown("---")
    # Monat mit höchstem Profit
    best_month = month_stats.loc[
        month_stats["profit"].idxmax(),
        "month"]

    df_plot = df_results[df_results["month"] == best_month].copy()
    fig_soc = go.Figure()
    # Entladen positiv
    fig_soc.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=df_plot["p_discharge"],
            mode="lines",
            name="Entladen",
            line=dict(color=COLOURS["discharge"],width=1.5),
            yaxis="y")  
    )
    # Laden negativ
    fig_soc.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=-df_plot["p_charge"],
            mode="lines",
            name="Laden",
            line=dict(color=COLOURS["charge"],width=1.5),
            yaxis="y")
    )
    # 50 % SoC entspricht 0 MW
    soc_scaled = df_plot["SoC_percent"] - 50
    fig_soc.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=soc_scaled,
            mode="lines",
            name="SoC",
            line=dict(color=COLOURS["soc"],width=3),
            yaxis="y2")
    )
    fig_soc.update_layout(
        title=f"Ladezustand und Leistung – profitabelster Monat ({best_month})",
        xaxis_title="Zeit",
        # Leistung
        yaxis=dict(
            title="Leistung [MW]",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black"),
        # SoC
        yaxis2=dict(
            title="SoC [%]",
            overlaying="y",
            side="right",
            range=[-50, 50],
            tickvals=[-50, -25, 0, 25, 50],
            ticktext=["0", "25", "50", "75", "100"]
        ),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05)
    )

    st.plotly_chart(fig_soc, use_container_width=True, key="soc_and_p_results")

    # Laden und Entladen im Tagesverlauf
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(
        x=hour_stats["hour"],
        y=hour_stats["charge_norm"],
        name="Laden",
        marker_color="#85BCF5"
    ))
    fig_hist.add_trace(go.Bar(
        x=hour_stats["hour"],
        y=hour_stats["discharge_norm"],
        name="Entladen",
        marker_color="#FFD700"
    ))
    # Overlay - Preisspanne
    fig_hist.add_trace(go.Scatter(
            x=hour_stats["hour"],
            y=hour_stats["price_median"],
            name="Medianpreis",
            mode="lines",
            line=dict(color="darkgrey", width=2),
            yaxis="y2")
    )
    # Preisband Q10 - Q90
    fig_hist.add_trace(
        go.Scatter(
            x=hour_stats["hour"],
            y=hour_stats["price_q90"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            yaxis="y2")
    )
    fig_hist.add_trace(
        go.Scatter(
            x=hour_stats["hour"],
            y=hour_stats["price_q10"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(80, 80, 80, 0.30)",
            name="Q10–Q90 Preisspanne",
            yaxis="y2"
        )
    )
    fig_hist.update_layout(
        title="Lade- und Entladeaktivität im Tagesverlauf - mit Preis-Overlay",
        template="plotly_white",
        height=500,
        barmode="group",
        xaxis_title="Stunde des Tages",
        yaxis=dict(title="Normierte Aktivität"),
        yaxis2=dict(title="Strompreis [€/MWh]",
                    overlaying="y",
                    side="right",
                    showgrid=False),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_hist, use_container_width=True, key="daily_charging_price-overlay")

with tab_betrieb:
# Betrieb 
    st.subheader("Betriebsstunden (aktiv) im Zeitverlauf")
    fig_op, ax_op = plt.subplots(figsize=(12,4))
    ax_op.plot(df_operation["timestamp"], df_operation["operating_hours_cum"], color="black")
    ax_op.set_title("Kumulierte Betriebsstunden")
    ax_op.set_xlabel("Zeit")
    ax_op.set_ylabel("Stunden")
    ax_op.grid(True)
    st.pyplot(fig_op)

# Laden und Entladen im Tagesverlauf
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(
        x=hour_stats["hour"],
        y=hour_stats["charge_norm"],
        name="Laden",
        marker_color="#85BCF5"
    ))
    fig_hist.add_trace(go.Bar(
        x=hour_stats["hour"],
        y=hour_stats["discharge_norm"],
        name="Entladen",
        marker_color="#FFD700"
    ))

    fig_hist.update_layout(
        title="Lade- und Entladeaktivität im Tagesverlauf",
        template="plotly_white",
        height=500,
        barmode="group",
        xaxis_title="Stunde des Tages",
        yaxis=dict(title="Normierte Aktivität"),
         legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_hist, use_container_width=True, key="daily_charging")

# Heatmap Laden | Entladen
    col_1, col_2 = st.columns(2)
    with col_1:
        map_charge = px.density_heatmap(
            df_results,
            x="hour",
            y="dayofyear",
            z="p_charge",
            histfunc="avg",
            color_continuous_scale="RdYlGn",
            title="Heatmap Durchschnittliche Ladeleistung nach Stunde und Kalendertag", 
            labels={
                "hour": "Stunde",
                "dayofyear": "Tag des Jahres",
                "p_charge": "Ladeleistung [MW]"
            }
        )
        st.plotly_chart(map_charge, use_container_width=True, key="heat-charge")
    with col_2:     
        map_discharge = px.density_heatmap(
            df_results,
            x="hour",
            y="dayofyear",
            z="p_discharge",
            histfunc="avg",
            color_continuous_scale="RdYlGn",
            title="Heatmap Durchschnittliche Entladeleistung nach Stunde und Kalendertag",
            labels={
                "hour": "Stunde",
                "dayofyear": "Tag des Jahres",
                "p_discharge": "Entladeleistung [MW]"
            }
        )
        st.plotly_chart(map_discharge, use_container_width=True, key="heat-discharge")    

    # Laden gegen Strompreis
    st.markdown("---")
    st.subheader("Ladeleistung gegen Strompreis")

    fig_charge_price = px.scatter(
        df_results[df_results["p_charge"] > 0],
        x="price",
        y="p_charge",
        opacity=0.5,
        labels={
            "price": "Strompreis [€/MWh]",
            "p_charge": "Ladeleistung [MW]"
        },
        title="Laden gegen Strompreis"
    )
    fig_charge_price.update_traces(
        marker=dict(
            color=COLOURS["charge"],
            size=5
        )
    )
    st.plotly_chart(fig_charge_price, use_container_width=True, key="charge_and_price")

    # Entladen gegen Strompreis
    st.subheader("Entladeleistung gegen Strompreis")
    fig_discharge_price = px.scatter(
        df_results[df_results["p_discharge"] > 0],
        x="price",
        y="p_discharge",
        opacity=0.5,
        labels={
            "price": "Strompreis [€/MWh]",
            "p_discharge": "Entladeleistung [MW]"
        },
        title="Entladen gegen Strompreis"
    )
    fig_discharge_price.update_traces(
        marker=dict(
            color=COLOURS["discharge"],
            size=5
        )
    )
    st.plotly_chart(fig_discharge_price, use_container_width=True, key="discharge_and_price")

# Laden | Entladen und SoC - für einen ausgewählten Monat
    # Monat mit höchstem Profit
    st.markdown("---")
    best_month = month_stats.loc[
        month_stats["profit"].idxmax(),
        "month"]
    df_plot = df_results[df_results["month"] == best_month].copy()
    fig_soc2 = go.Figure()
    # Entladen positiv
    fig_soc2.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=df_plot["p_discharge"],
            mode="lines",
            name="Entladen",
            line=dict(color=COLOURS["discharge"],width=1.5),
            yaxis="y")  
    )
    # Laden negativ
    fig_soc2.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=-df_plot["p_charge"],
            mode="lines",
            name="Laden",
            line=dict(color=COLOURS["charge"],width=1.5),
            yaxis="y")
    )
    # 50 % SoC entspricht 0 MW
    soc_scaled = df_plot["SoC_percent"] - 50
    fig_soc2.add_trace(go.Scatter(
            x=df_plot["timestamp"],
            y=soc_scaled,
            mode="lines",
            name="SoC",
            line=dict(color=COLOURS["soc"],width=3),
            yaxis="y2")
    )
    fig_soc2.update_layout(
        title=f"Ladezustand und Leistung – profitabelster Monat ({best_month})",
        xaxis_title="Zeit",
        # Leistung
        yaxis=dict(
            title="Leistung [MW]",
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black"),
        # SoC
        yaxis2=dict(
            title="SoC [%]",
            overlaying="y",
            side="right",
            range=[-50, 50],
            tickvals=[-50, -25, 0, 25, 50],
            ticktext=["0", "25", "50", "75", "100"]
        ),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05)
    )
    st.plotly_chart(fig_soc2, use_container_width=True, key="soc_and_p_stat")

# Heatmap SoC
    st.markdown("---")
    map = px.density_heatmap(
        df_results,
        x="hour",
        y="dayofyear",
        z="SoC_percent",
        histfunc="avg",
        color_continuous_scale="RdYlGn",
        title="Heatmap Ladezustand (SoC)",
        labels={
            "hour": "Stunde",
            "dayofyear": "Tag des Jahres",
            "SoC": "Ladezustand [%]"
        }
    )
    st.plotly_chart(map, use_container_width=True, key="heat_soc")  

# Ladeverhalten: Overlay
    st.markdown("---")
    show_price = st.checkbox("Strompreis einblenden", key="show_price")
    show_ee = st.checkbox("EE-Anteil einblenden",key="show_ee")
    # Laden 
    fig = px.bar(
        month_stats,
        x="month",
        y="e_in",
        title="Geladene & Entladene Energiemenge pro Monat",
        labels={
            "month": "Monat",
            "e_in": "Energiemenge [MWh]"
        },
        color_discrete_sequence=[COLOURS["charge"]]
    )
    # Entladen
    fig.add_bar(
        x=month_stats["month"],
        y=month_stats["e_out"],
        name="Entladen",
        marker_color=COLOURS["discharge"]
    )
    fig.update_traces(name="Laden", selector=dict(type="bar"))
    if show_price == True:
        # Strompreis
        fig.add_scatter(x=month_stats["month"],
                        y=month_stats["avg_price"],
                        name="Strompreis",
                        mode="lines+markers",
                        yaxis="y2"
                        )
        fig.update_layout(
            title="Durchschnittlicher Profit pro Monat",
            xaxis_title="Monat",
            yaxis_title="Profit [€]",
            yaxis2=dict(
                title="Strompreis [€/MWh]",
                overlaying="y",
                side="right"
            )
        )
    if show_ee == True:
        # EE-Anteil
        market = st.session_state.get("market_results")
        if market is None:
            st.warning("Keine Daten vorhanden. Bitte zuerst Berechnung starten.")
            st.stop()
        month_stats_ee = market["month_stats"]

        fig.add_scatter(x=month_stats["month"],
                        y=month_stats_ee["ee_share"],
                        name="Anteil Erneuerbarer Energien",
                        mode="lines+markers",
                        yaxis="y2"
                        )
        fig.update_layout(
            title="Durchschnittlicher Profit pro Monat",
            xaxis_title="Monat",
            yaxis_title="Profit [€]",
            yaxis2=dict(
                title="EE-Anteil [%]",
                overlaying="y",
                side="right"
            )
        )
    st.plotly_chart(fig, use_container_width=True, key="overlay_charge_price")
# Zyklen
    st.markdown("---")
    fig = go.Figure()
    fig.add_bar(
        x=month_stats["month"],
        y=month_stats["cycles_efc"],
        name="Vollzyklen (EFC)",
        marker_color="rgba(40,137,228,0.65)")
    fig.add_bar(
        x=month_stats["month"],
        y=month_stats["cycles_op"],
        name="Betriebszyklen",
        marker_color="rgba(241,153,20,0.65)")
    fig.update_layout(title="Betriebszyklen und Vollzyklen")

    st.plotly_chart(fig, use_container_width = True, key="cycles")

    df_yearly_metrics = analysis_results["df_yearly_metrics"]

    df_yearly_metrics = df_yearly_metrics.rename(columns={
        "year": "Jahr",
        "charge_hours": "Ladestunden",
        "discharge_hours": "Entladestunden",
        "active_hours_total": "Aktive Stunden",
        "avg_charge_price": "Ø Ladepreis",
        "avg_discharge_price": "Ø Entladepreis",
        "charge_price_per_kwh": "Gewichteter Ladepreis",
        "discharge_price_per_kwh": "Gewichteter Entladepreis",
        "charged_energy_kwh": "Geladene Energie [MWh]",
        "discharged_energy_kwh": "Entladene Energie [MWh]"
    })
    st.subheader("Jährliche Betriebskennzahlen")
    st.dataframe(df_yearly_metrics.style.format({
            "avg_charge_price": "{:.2f}",
            "avg_discharge_price": "{:.2f}",
            "charge_price_per_kwh": "{:.2f}",
            "discharge_price_per_kwh": "{:.2f}",
            "charged_energy_kwh": "{:,.0f}",
            "discharged_energy_kwh": "{:,.0f}",}),
            use_container_width=True
    )

with tab_cost:
# Monatl. Kostenentwicklung
    st.markdown("## Kostenaufstellung")

    col_1 , col_2, col_3 = st.columns(3)
    with col_1: 
        st.metric("Strombezugskosten", f'{m["cost_buy_pos"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
    with col_2: 
        st.metric("Durchsatzkosten", f'{m["cost_var"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
    with col_3: 
        st.metric("Gewinn aus negativen Strompreisen", f'{m["revenue_negative_price"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
    col_4 , col_5, col_6 = st.columns(3)    
    with col_4:         
        st.metric("Gesamtkosten", f'{m["total_cost_full"]:,.2f} €'.replace(",", "X").replace(".", ",").replace("X", "."))
    with col_5:
        st.metric("Ø Strombezugspreis", f'{m["avg_price_per_mwh_buy"]:,.2f} €/MWh'.replace(",", "X").replace(".", ",").replace("X", "."))

    with col_6:
        st.metric("Ø Gesamtbezugskosten",f'{m["avg_total_purchase_cost_per_mwh"]:,.2f} €/MWh'.replace(",", "X").replace(".", ",").replace("X", "."))
    
    fig_cost = go.Figure()
    # Strombezugskosten
    fig_cost.add_bar(
        x=cost_analysis["month"],
        y=cost_analysis["cost_buy_pos"],
        name="Strombezug",
        marker_color="rgba(215,46,46,0.6)"
    )
    # Negative Strompreise
    fig_cost.add_bar(
        x=cost_analysis["month"],
        y=cost_analysis["cost_buy_neg"],
        name="Negative Strompreise",
        marker_color="rgba(36,126,36,0.6)"
    )
    # Variable Kosten
    fig_cost.add_bar(
        x=cost_analysis["month"],
        y=cost_analysis["cost_var"],
        name="Durchsatzkosten",
        marker_color="rgba(133,74,186,0.6)"
    )
    fig_cost.update_layout(
        barmode="relative",
        title="Monatliche Kostenaufstellung",
        xaxis_title="Monat",
        yaxis_title="Kosten [€]",
        legend_title="Kostenart",
        height=500
    )
    st.plotly_chart(fig_cost, use_container_width=True, key="cost")


# Monatl. Profit
    fig_month = px.line(
        month_stats,
        x="month",
        y="profit",
        title="Monatlicher Profit",
        labels={
            "month": "Monat",
            "profit": "Profit [€]"
        }
    )
    fig_month.update_traces(
        line=dict(color=COLOURS["profit"], width=3)
    )
    st.plotly_chart(fig_month, use_container_width=True, key="profit_m")

# Jahresergebnisse
    st.subheader("Jahresergebnisse")
    st.markdown("---")
    fig_year = px.bar(
        year_stats,
        x="year",
        y=["revenue", "cost", "profit"],
        barmode="group",
        title="Jährliche Erlöse, Kosten und Gewinne",
        labels={
            "value": "Betrag [€]",
            "year": "Jahr"
        },
        color_discrete_map={
            "revenue": COLOURS["revenue"],
            "cost": COLOURS["cost"],
            "profit": COLOURS["profit"]
        }
    )
    st.plotly_chart(fig_year, use_container_width=True,key="yearly_results")

    
with tab_dl: 
    st.write("Download")
# Ergebnisstabelle
    csv_bytes = df_results.to_csv(
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig"
        ).encode("utf-8-sig")
    st.download_button(
        label="Ergebnistabelle als CSV herunterladen",
        data=csv_bytes,
        file_name="Battery_Model_Results.csv",
        mime="text/csv",
        key="download_results"
        )
# operation
    csv_bytes = df_operation.to_csv(
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig"
        ).encode("utf-8-sig")
    st.download_button(
        label="Ergebnistabelle (aktiv) CSV herunterladen",
        data=csv_bytes,
        file_name="Battery_Model_active.csv",
        mime="text/csv",
        key="download_active"
    )