
import pandas as pd
import pulp as pl
import numpy as np
from typing import Dict, Any

# Konstanten einführen 
DT = 1.0
SOC_START = 0.0
SOC_MAX = 1.0
DOD_0 = 0.90
SOC_OP_MIN = 1 - DOD_0
SOC_OP_MAX = DOD_0
CYCLES_LIFETIME = 4500

# ===============================
# Batteriespeicher | Berechnungen
# -------------------------------
# Rohdaten vorbereiten
# -------------------------------
def prepare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    df_calc = prices.copy().reset_index(drop=True)
    if "timestamp" not in df_calc.columns or "price" not in df_calc.columns:
        raise ValueError("Spalten 'timestamp' und 'price' fehlen")

    df_calc = df_calc.dropna(subset=["timestamp", "price"])
    if not pd.api.types.is_datetime64_any_dtype(df_calc["timestamp"]):
        df_calc["timestamp"] = pd.to_datetime(df_calc["timestamp"], errors="coerce")
    if not pd.api.types.is_numeric_dtype(df_calc["price"]):
        df_calc["price"] = pd.to_numeric(df_calc["price"], errors="coerce")
    df_calc = df_calc.sort_values("timestamp").reset_index(drop=True)
    if df_calc.empty:
        raise ValueError("Keine gültigen Daten vorhanden")

    return df_calc

# -------------------------------
# Optimierungsmodell
# -------------------------------
def run_arbitrage_optimization(
    df_calc: pd.DataFrame,
    cap_mwh: float,
    p_mw: float,
    rte: float,
    neg_cost: float,
    life_cost: float,
) -> Dict[str, Any]:

    df_calc = df_calc.copy().reset_index(drop=True)

    T = len(df_calc)
    e_price = df_calc["price"].reset_index(drop=True)

    dt = 1.0
    p_max = float(p_mw)

    eta_c = float(np.sqrt(rte))
    eta_d = float(np.sqrt(rte))

    dod_0 = 0.90
    soc_op_min = 1 - dod_0
    soc_op_max = dod_0

    cost_MWh = float(neg_cost + life_cost)

    model = pl.LpProblem("Arbitrage", pl.LpMaximize)

    p_c = pl.LpVariable.dicts("p_c", range(T), lowBound=0, upBound=p_max, cat="Continuous")
    p_d = pl.LpVariable.dicts("p_d", range(T), lowBound=0, upBound=p_max, cat="Continuous")
    soc = pl.LpVariable.dicts("State_of_Charge", range(T), lowBound=soc_op_min, upBound=soc_op_max,cat="Continuous")
    y = pl.LpVariable.dicts("is_charging", range(T), lowBound=0, upBound=1, cat="Binary")

    model += pl.lpSum(
        (e_price.iloc[t] * ((p_d[t] - p_c[t]) * dt))
        - (cost_MWh * ((p_c[t] + p_d[t]) * dt))
        for t in range(T)
    )
    for t in range(T):
        if t == 0:
            model += soc[t] == soc_op_min \
                + (p_c[t] * eta_c * dt) / cap_mwh \
                - (p_d[t] * dt) / (eta_d * cap_mwh)
        else:
            model += soc[t] == soc[t - 1] \
                + (p_c[t] * eta_c * dt) / cap_mwh \
                - (p_d[t] * dt) / (eta_d * cap_mwh)

        model += p_c[t] <= p_max * y[t]
        model += p_d[t] <= p_max * (1 - y[t])

    solver = pl.PULP_CBC_CMD(msg=False)
    model.solve(solver)

    status = pl.LpStatus[model.status]
    objective = pl.value(model.objective)

    df_calc["p_charge_raw"] = [(pl.value(p_c[t]) or 0.0) for t in range(T)]
    df_calc["p_discharge_raw"] = [(pl.value(p_d[t]) or 0.0) for t in range(T)]
    df_calc["SoC"] = [
        pl.value(soc[t]) if pl.value(soc[t]) is not None else np.nan
        for t in range(T)
    ]

    STEP = 0.1
    df_calc["p_charge"] = (df_calc["p_charge_raw"] / STEP).round() * STEP
    df_calc["p_discharge"] = (df_calc["p_discharge_raw"] / STEP).round() * STEP

    required_result_cols = ["timestamp", "price", "p_charge", "p_discharge", "SoC"]
    missing_cols = [c for c in required_result_cols if c not in df_calc.columns]

    if missing_cols:
        raise ValueError(
            f"Fehlende Spalten in df_calc: {missing_cols}. "
            f"Vorhandene Spalten: {list(df_calc.columns)}"
        )

    df_results = df_calc[required_result_cols].copy()

    df_results["e_in"] = df_results["p_charge"] * dt
    df_results["e_out"] = df_results["p_discharge"] * dt

    df_results["cost_buy"] = df_results["price"] * df_results["e_in"]
    df_results["cost_var"] = cost_MWh * (df_results["e_in"] + df_results["e_out"])

    df_results["Netzentgelte"] = neg_cost * (df_results["e_in"] + df_results["e_out"])
    df_results["Durchsatzkosten"] = life_cost * (df_results["e_in"] + df_results["e_out"])

    df_results["revenue_sell"] = df_results["price"] * df_results["e_out"]
    df_results["profit"] = (df_results["revenue_sell"]
        - df_results["cost_buy"]
        - df_results["cost_var"]
    )
    return {
        "status": status,
        "objective": objective,
        "df_results": df_results,
        "df_calc": df_calc,
        "soc_min": soc_op_min,
        "soc_max": soc_op_max,
        "cost_MWh": cost_MWh,
    }
# -------------------------------
# Vorberechnungen Charts-/Tabellen-DataFrames 
# -------------------------------
def build_analysis_frames(df_results: pd.DataFrame, cap_mwh: float) -> Dict[str, Any]:
    df_analysis = df_results.copy()
    # Zeitgliederung
    df_analysis["year"] = df_analysis["timestamp"].dt.year
    df_analysis["month"] = df_analysis["timestamp"].dt.to_period("M").astype(str)
    df_analysis["day"] = df_analysis["timestamp"].dt.date
    df_analysis["hour"] = df_analysis["timestamp"].dt.hour
    df_analysis["dayofyear"] = df_analysis["timestamp"].dt.dayofyear
    # Berechnungen
    df_analysis["cost_full"] = (df_analysis["cost_buy"] + df_analysis["cost_var"])
    df_analysis["SoC_percent"] = (df_analysis["SoC"] * 100)
    # Aktivitätszeiten bestimmen
    df_analysis["active"] = ((df_analysis["e_in"] > 0) | (df_analysis["e_out"] > 0)).astype(int)
    # Daten, wenn Speicher aktiv
    df_operation = df_analysis[(df_analysis["e_in"] > 0) | (df_analysis["e_out"] > 0)].copy()
    df_operation["operating_hours_cum"] = range(1, len(df_operation) + 1)
    
    n_days = pd.Series(df_analysis["timestamp"].dt.normalize().unique()).nunique()

    total_revenue = df_analysis["revenue_sell"].sum()
    total_cost_full = (df_analysis["cost_buy"] + df_analysis["cost_var"]).sum()
    total_profit = df_analysis["profit"].sum()

    avg_revenue_day = total_revenue / n_days if n_days > 0 else 0.0
    avg_cost_day = total_cost_full / n_days if n_days > 0 else 0.0
    avg_profit_day = total_profit / n_days if n_days > 0 else 0.0

    total_discharge = df_analysis["e_out"].sum()
    cycles = total_discharge / cap_mwh if cap_mwh > 0 else 0.0
    cycles_per_day = cycles / n_days if n_days > 0 else 0.0

    # Zustand des Speicherserkennen
    df_operation["is_charging"] = (df_operation["e_in"] > 0).astype(int)
    df_analysis["is_charging"] = (df_analysis["e_in"] > 0).astype(int)
    # Zyklusstart: vorher nicht geladen, jetzt laden
    df_operation["cycle_start"] = ((df_operation["is_charging"] == 1)
        & (df_operation["is_charging"].shift(1, fill_value=0) == 0)).astype(int)
    df_analysis["cycle_start"] = ((df_analysis["is_charging"] == 1)
        & (df_analysis["is_charging"].shift(1, fill_value=0) == 0)).astype(int)
    # Zyklusnummer hochzählen
    df_operation["cycle_op_id"] = df_operation["cycle_start"].cumsum()
    df_analysis["cycle_op_id"] = df_analysis["cycle_start"].cumsum()
# gefilterte df nach Zeiteinheit (Jahr | Monat | Tag | Stunde)
# Jahr 
    year_stats = (df_analysis.groupby("year", as_index=False)
        .agg(
            revenue=("revenue_sell", "sum"),
            cost_buy=("cost_buy", "sum"),
            cost_var=("cost_var", "sum"),
            cost=("cost_full", "sum"),
            profit=("profit", "sum"),
            e_in=("e_in", "sum"),
            e_out=("e_out", "sum"),
            cycles_op=("cycle_start", "sum")
        )
    )
    year_stats["cycles_efc"] = (year_stats["e_in"] + year_stats["e_out"]) / (2 * cap_mwh)
    year_stats["profit_per_op_cycle"] = np.where(
        year_stats["cycles_op"] > 0,
        year_stats["profit"] / year_stats["cycles_op"],
        np.nan
    )

    year_stats["profit_per_efc"] = np.where(
        year_stats["cycles_efc"] > 0,
        year_stats["profit"] / year_stats["cycles_efc"],
        np.nan
    )
# Monat
    month_stats = (df_analysis.groupby("month", as_index=False)
        .agg(
            revenue=("revenue_sell", "sum"),
            cost_buy=("cost_buy", "sum"),
            cost_var=("cost_var", "sum"),
            cost=("cost_full", "sum"),
            profit=("profit", "sum"),
            e_in=("e_in", "sum"),
            e_out=("e_out", "sum"),
            cycles_op=("cycle_start", "sum"), 
            avg_price=("price", "mean")            
        )
    )
    month_stats["cycles_efc"] = (month_stats["e_in"] + month_stats["e_out"]) / (2 * cap_mwh)
    
    month_stats["profit_per_op_cycle"] = np.where(
        month_stats["cycles_op"] > 0,
        month_stats["profit"] / month_stats["cycles_op"],
        np.nan
    )

    month_stats["profit_per_efc"] = np.where(
        month_stats["cycles_efc"] > 0,
        month_stats["profit"] / month_stats["cycles_efc"],
        np.nan
    )

# Tag
    day_stats = (df_analysis.groupby("day", as_index=False)
        .agg(
            revenue=("revenue_sell", "sum"),
            cost_buy=("cost_buy", "sum"),
            cost_var=("cost_var", "sum"),
            cost=("cost_full", "sum"),
            profit=("profit", "sum"),
            e_in=("e_in", "sum"),
            e_out=("e_out", "sum"),
            soc_min=("SoC_percent", "min"),
            soc_max=("SoC_percent", "max")
        )
    )
# Stunde
    hour_stats = (df_analysis.groupby("hour", as_index=False)
        .agg(
            charge_sum=("p_charge", "sum"),
            discharge_sum=("p_discharge", "sum"),
            charge_mean=("p_charge", "mean"),
            discharge_mean=("p_discharge", "mean"),
            cost_buy=("cost_buy", "sum"),
            cost_var=("cost_var", "sum"),
            cost=("cost_full", "sum"),
            revenue=("revenue_sell", "sum"),
            profit=("profit", "sum"),
            price_mean=("price", "mean"),
            price_median=("price", "median"),
            price_q10=("price", lambda x: x.quantile(0.10)),
            price_q90=("price", lambda x: x.quantile(0.90)))
        )

    hour_stats["charge_norm"] = (
        hour_stats["charge_sum"] / hour_stats["charge_sum"].max()
        if hour_stats["charge_sum"].max() > 0
        else 0.0
    )
    hour_stats["discharge_norm"] = (
        hour_stats["discharge_sum"] / hour_stats["discharge_sum"].max()
        if hour_stats["discharge_sum"].max() > 0
        else 0.0
    )
    
    cost_analysis = month_stats.copy()
    cost_analysis["cost_buy_pos"] = cost_analysis["cost_buy"].clip(lower=0)
    cost_analysis["cost_buy_neg"] = cost_analysis["cost_buy"].clip(upper=0)
    revenue_negative_price = abs(cost_analysis["cost_buy_neg"].sum())
    cost_buy_pos = cost_analysis["cost_buy_pos"].sum()
    cost_var = df_analysis["cost_var"].sum()

    def create_yearly_activity_metrics(df_operation: pd.DataFrame) -> Dict[str, Any]:
        yearly_activity_metrics = {}
        for year, df_year in df_operation.groupby("year"):

            # Laden
            df_charge = df_year[df_year["e_in"] > 0]

            charge_hours = len(df_charge)

            avg_charge_price = (
                df_charge["price"].mean()
                if charge_hours > 0 else 0
            )

            total_charge_energy = df_charge["e_in"].sum()

            charge_price_per_kwh = (
                (df_charge["price"] * df_charge["e_in"]).sum()
                / total_charge_energy
                if total_charge_energy > 0 else 0
            )

            # Entladen
            df_discharge = df_year[df_year["e_out"] > 0]

            discharge_hours = len(df_discharge)

            avg_discharge_price = (
                df_discharge["price"].mean()
                if discharge_hours > 0 else 0
            )

            total_discharge_energy = abs(df_discharge["e_out"].sum())

            discharge_price_per_kwh = (
                (df_discharge["price"] * abs(df_discharge["e_out"])).sum()
                / total_discharge_energy
                if total_discharge_energy > 0 else 0
            )

            yearly_activity_metrics[year] = {
                "charge_hours": charge_hours,
                "discharge_hours": discharge_hours,
                "active_hours_total": charge_hours + discharge_hours,

                "avg_charge_price": avg_charge_price,
                "avg_discharge_price": avg_discharge_price,

                "charge_price_per_kwh": charge_price_per_kwh,
                "discharge_price_per_kwh": discharge_price_per_kwh,

                "charged_energy_kwh": total_charge_energy,
                "discharged_energy_kwh": total_discharge_energy,
            }
        
        return yearly_activity_metrics

    yearly_activity_metrics = create_yearly_activity_metrics(df_operation)
    df_yearly_metrics = (pd.DataFrame.from_dict(
            yearly_activity_metrics,
            orient="index")
        .reset_index().rename(columns={"index": "year"})
    )
    total_charge_energy = df_analysis["e_in"].sum()
    avg_price_per_mwh_buy = (
        df_analysis["cost_buy"].sum() / total_charge_energy
        if total_charge_energy > 0
        else 0.0
    )
    avg_total_purchase_cost_per_mwh = (
    (df_analysis["cost_buy"].sum() + df_analysis["cost_var"].sum())
    / total_charge_energy
    if total_charge_energy > 0
    else 0.0
    )
    total_e_in = df_analysis["e_in"].sum()
    total_e_out = df_analysis["e_out"].sum()
    revenue_per_mwh = (total_revenue / total_e_out
        if total_e_out > 0 else 0)
    cost_per_mwh = (total_cost_full / total_e_in
        if total_e_in > 0 else 0)

    profit_per_mwh = (total_profit / total_e_out
        if total_e_out > 0 else 0)
    operating_hours = len(df_operation)
    total_cycles_op = df_analysis["cycle_start"].sum()
    total_cycles_efc = ((total_e_in + total_e_out)/ (2 * cap_mwh)
        if cap_mwh > 0 else 0)
    metrics = {
        "n_days": n_days,
        "total_revenue": total_revenue,
        "total_cost_full": total_cost_full,
        "total_profit": total_profit,
        "avg_revenue_day": avg_revenue_day,
        "avg_cost_day": avg_cost_day,
        "avg_profit_day": avg_profit_day,
        "revenue_negative_price": revenue_negative_price,
        "cost_buy_pos": cost_buy_pos,
        "cost_var": cost_var,     
        "avg_price_per_mwh_buy": avg_price_per_mwh_buy,
        "avg_total_purchase_cost_per_mwh": avg_total_purchase_cost_per_mwh,
        "yearly_activity_metrics": yearly_activity_metrics,
        "revenue_per_mwh": revenue_per_mwh,
        "cost_per_mwh": cost_per_mwh,
        "profit_per_mwh": profit_per_mwh,
        "operating_hours": operating_hours,
        "total_cycles_op": total_cycles_op,
        "total_cycles_efc": total_cycles_efc,
    }
    return {
        "df_analysis": df_analysis,
        "df_operation": df_operation,
        "year_stats": year_stats,
        "month_stats": month_stats,
        "day_stats": day_stats,
        "hour_stats": hour_stats,
        "cost_analysis" : cost_analysis,
        "df_yearly_metrics": df_yearly_metrics,
        "metrics": metrics
    }

# -------------------------------
# Ergebnisausgabe
# -------------------------------
def compute_all_battery_results(
    prices: pd.DataFrame,
    cap_mwh: float,
    p_mw: float,
    rte: float,
    neg_cost: float,
    life_cost: float,
) -> Dict[str, Any]:
    df_prices = prepare_prices(prices)
    opt = run_arbitrage_optimization(
        df_prices,
        cap_mwh,
        p_mw,
        rte,
        neg_cost,
        life_cost
    )
    print("nach opt")
    print(opt.keys())

    analysis = build_analysis_frames(opt["df_results"], cap_mwh)
    
    return {
    # Optimierung
        "status": opt["status"],
        "objective": opt["objective"],
        "soc_min": opt["soc_min"],
        "soc_max": opt["soc_max"],
        "cost_MWh": opt["cost_MWh"],
    # Analyse-Daten
        "df_analysis": analysis["df_analysis"],
        "df_operation": analysis["df_operation"],
    # Statistiken
        "year_stats": analysis["year_stats"],
        "month_stats": analysis["month_stats"],
        "day_stats": analysis["day_stats"],
        "hour_stats": analysis["hour_stats"],
        "cost_analysis" : analysis["cost_analysis"],
        "df_yearly_metrics": analysis["df_yearly_metrics"],
    # Kennzahlen
        "metrics": analysis["metrics"],
    }
