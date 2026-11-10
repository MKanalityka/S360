"""Syntetyczne, deterministyczne dane demonstracyjne do Spółdzielnia360.

Wszystkie dane są fikcyjne. Nie zawierają danych osobowych mieszkańców.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

DEMO_START = pd.Timestamp("2024-01-01")
DEMO_END = pd.Timestamp("2026-10-01")
AS_OF = pd.Timestamp("2026-10-31")

CATEGORY_GROUPS = {
    "Ogrzewanie": "Media",
    "Ciepła woda": "Media",
    "Woda i ścieki": "Media",
    "Energia wspólna": "Media",
    "Wywóz odpadów": "Eksploatacja",
    "Utrzymanie czystości": "Eksploatacja",
    "Konserwacja": "Eksploatacja",
    "Tereny zielone": "Eksploatacja",
    "Administracja": "Administracja",
    "Ubezpieczenia": "Pozostałe",
    "Podatki i opłaty": "Pozostałe",
    "Dźwigi": "Eksploatacja",
}
CATEGORIES = list(CATEGORY_GROUPS)
MEDIA_TO_CATEGORY = {
    "Ciepło (CO)": ("Ogrzewanie", "GJ"),
    "Ciepła woda": ("Ciepła woda", "m³"),
    "Woda i ścieki": ("Woda i ścieki", "m³"),
    "Energia elektryczna": ("Energia wspólna", "kWh"),
}
CATEGORY_RATES = {
    "Ogrzewanie": 3.25, "Ciepła woda": 1.60,
    "Woda i ścieki": 2.15, "Energia wspólna": 0.69,
    "Wywóz odpadów": 0.92, "Utrzymanie czystości": 0.77,
    "Konserwacja": 1.05, "Tereny zielone": 0.24,
    "Administracja": 0.92, "Ubezpieczenia": 0.18,
    "Podatki i opłaty": 0.20, "Dźwigi": 0.31,
}
CATEGORY_COLORS = {
    "Ogrzewanie": "#E59A46", "Ciepła woda": "#EDC17B",
    "Woda i ścieki": "#53A7C7", "Energia wspólna": "#7769C3",
    "Wywóz odpadów": "#97A7B0", "Utrzymanie czystości": "#7CC1A3",
    "Konserwacja": "#3A806F", "Tereny zielone": "#A0B96B",
    "Administracja": "#536C95", "Ubezpieczenia": "#B8A5CE",
    "Podatki i opłaty": "#BF8D91", "Dźwigi": "#8F9CBC",
}


def _safe_round(v: float) -> float:
    return round(max(float(v), 0.0), 2)


def make_buildings(rng: np.random.Generator) -> pd.DataFrame:
    estate_names = ["Centrum", "Północ", "Południe", "Zachód"]
    street_names = ["Słoneczna", "Lipowa", "Leśna", "Ogrodowa", "Kwiatowa", "Parkowa",
                    "Wiosenna", "Spokojna", "Polna", "Wrzosowa", "Klonowa", "Szkolna"]
    data = []
    for i in range(24):
        area = float(rng.integers(2800, 8500))
        units = int(round(area / rng.uniform(52, 68)))
        floors = int(rng.choice([4, 5, 9, 11]))
        built = int(rng.integers(1973, 2017))
        data.append({
            "building_id": f"B{i+1:02}",
            "building": f"{street_names[i % 12]} {3 + 2 * (i // 12) + (i % 9)}",
            "estate": estate_names[i % 4],
            "area_m2": area,
            "units": units,
            "year_built": built,
            "floors": floors,
            "elevator": floors >= 9,
            "heat_factor": float(rng.uniform(0.76, 1.34)),
            "cost_factor": float(rng.uniform(0.89, 1.10)),
            "fund_rate": float(rng.uniform(1.65, 2.65)),
        })
    return pd.DataFrame(data)


def make_projects(buildings: pd.DataFrame, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    scopes = ["Modernizacja dachu", "Docieplenie elewacji", "Wymiana pionów wodnych",
              "Remont klatek schodowych", "Modernizacja węzła cieplnego",
              "Wymiana oświetlenia na LED", "Modernizacja dźwigów",
              "Hydroizolacja fundamentów", "Remont instalacji elektrycznej"]
    months = pd.date_range(DEMO_START, "2027-06-01", freq="MS")
    projects, spends = [], []
    for i in range(34):
        b = buildings.iloc[i % len(buildings)]
        # Część projektów już zamknięta, część trwa, część jest planowana.
        start_index = int(rng.integers(0, len(months) - 3))
        start = months[start_index]
        duration = int(rng.integers(3, 9))
        end = start + pd.DateOffset(months=duration - 1)
        budget = float(rng.integers(50, 310) * 1000)
        final_factor = float(rng.uniform(0.89, 1.13))
        if start > AS_OF:
            status = "Planowany"
        elif end < AS_OF.replace(day=1):
            status = "Zakończony"
        else:
            status = "W realizacji"
        project_id = f"R{i + 1:03}"
        active_months = pd.date_range(start, end, freq="MS")
        weights = rng.uniform(0.65, 1.35, len(active_months))
        weights = weights / weights.sum()
        for month, weight in zip(active_months, weights):
            if month <= DEMO_END:
                spends.append({"project_id": project_id, "building_id": b["building_id"],
                               "month": month, "expense": round(budget * final_factor * weight, 2)})
        projects.append({
            "project_id": project_id, "building_id": b["building_id"],
            "building": b["building"], "estate": b["estate"],
            "scope": scopes[i % len(scopes)], "start": start, "end": end,
            "budget": budget, "status": status,
        })
    project_df = pd.DataFrame(projects)
    spent_df = pd.DataFrame(spends)
    spent_totals = spent_df.groupby("project_id")["expense"].sum()
    project_df["spent"] = project_df["project_id"].map(spent_totals).fillna(0).round(2)
    project_df["progress_pct"] = (100 * project_df["spent"] / project_df["budget"]).clip(upper=100).round(1)
    project_df["budget_delta"] = project_df["spent"] - project_df["budget"]
    return project_df, spent_df


def make_inspections(buildings: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    kinds = ["Przegląd budowlany", "Instalacja gazowa", "Przegląd elektryczny",
             "Przewody kominowe", "Ochrona przeciwpożarowa", "Kontrola dźwigów"]
    data = []
    for _, b in buildings.iterrows():
        for j, kind in enumerate(kinds[:4] + ([kinds[5]] if b["elevator"] else [])):
            offset = int(rng.integers(-100, 285))
            deadline = AS_OF + pd.Timedelta(days=offset)
            last = deadline - pd.Timedelta(days=365 if j != 2 else 5 * 365)
            status = ("Po terminie" if deadline.date() < AS_OF.date()
                      else "Wkrótce" if offset <= 60 else "Zaplanowany")
            data.append({"building_id": b["building_id"], "building": b["building"],
                         "estate": b["estate"], "inspection": kind,
                         "last_date": last, "due_date": deadline,
                         "days_to_due": offset, "status": status})
    return pd.DataFrame(data)


def make_demo_data(seed: int = 360) -> dict[str, pd.DataFrame]:
    """Zwraca spójne tabele: budynki, koszty, media, należności, fundusze, remonty, przeglądy."""
    rng = np.random.default_rng(seed)
    buildings = make_buildings(rng)
    projects, project_spends = make_projects(buildings, rng)
    inspections = make_inspections(buildings, rng)
    months = pd.date_range(DEMO_START, DEMO_END, freq="MS")
    cost_rows, utility_rows, arrears_rows, fund_rows = [], [], [], []
    heating_seasons = {1: 2.05, 2: 1.86, 3: 1.38, 4: 0.77, 5: 0.26, 6: 0.10,
                       7: 0.08, 8: 0.08, 9: 0.34, 10: 0.97, 11: 1.52, 12: 1.97}
    price_by_media = {"Ciepło (CO)": (148.0, "GJ"),
                      "Ciepła woda": (48.0, "m³"),
                      "Woda i ścieki": (15.2, "m³"),
                      "Energia elektryczna": (1.18, "kWh")}
    spends = project_spends.groupby(["building_id", "month"])["expense"].sum().to_dict()

    for _, b in buildings.iterrows():
        bid = b["building_id"]
        arrears_stock = float(b["area_m2"] * rng.uniform(1.4, 3.0))
        fund_balance = float(b["area_m2"] * rng.uniform(65, 112))
        for month in months:
            inflation = 1 + 0.048 * (month.year - 2024) + (month.month - 1) * 0.0025
            heat_season = heating_seasons[month.month]
            month_costs = {}
            for category, group in CATEGORY_GROUPS.items():
                base = b["area_m2"] * CATEGORY_RATES[category] * b["cost_factor"]
                if category == "Ogrzewanie":
                    base *= heat_season * b["heat_factor"]
                elif category == "Dźwigi":
                    base *= 1 if b["elevator"] else 0.07
                elif category == "Tereny zielone":
                    base *= 0.55 + 0.85 * (month.month in (4, 5, 6, 7, 8, 9))
                elif category == "Woda i ścieki":
                    base *= float(rng.uniform(0.96, 1.04))
                plan = base * inflation * (0.96 + 0.025 * np.sin(month.month / 12 * np.pi))
                actual = base * inflation * float(rng.normal(1.01, 0.055))
                # Celowe anomalie - można je wykryć na ekranie alertów.
                if bid == "B04" and category == "Ogrzewanie" and month >= pd.Timestamp("2026-09-01"):
                    actual *= 1.48
                if bid == "B11" and category == "Energia wspólna" and month >= pd.Timestamp("2026-06-01"):
                    actual *= 1.68
                if bid == "B07" and category == "Konserwacja" and month >= pd.Timestamp("2026-08-01"):
                    actual *= 2.15
                if bid == "B15" and category == "Woda i ścieki" and month >= pd.Timestamp("2026-09-01"):
                    actual *= 1.61
                if bid == "B21" and category == "Wywóz odpadów" and month >= pd.Timestamp("2026-07-01"):
                    actual *= 1.42
                cost_rows.append({"month": month, "building_id": bid,
                                  "estate": b["estate"], "category": category,
                                  "group": group, "plan": _safe_round(plan),
                                  "actual": _safe_round(actual)})
                month_costs[category] = _safe_round(actual)

            for medium, (category, _) in MEDIA_TO_CATEGORY.items():
                cost = month_costs[category]
                unit_price = price_by_media[medium][0] * (1 + 0.045 * (month.year - 2024))
                consumption = max(0, cost / unit_price)
                utility_rows.append({"month": month, "building_id": bid,
                                     "estate": b["estate"], "medium": medium,
                                     "unit": price_by_media[medium][1],
                                     "consumption": round(consumption, 2),
                                     "unit_price": round(unit_price, 2),
                                     "cost": round(cost, 2)})

            charges = b["area_m2"] * 11.2 * inflation
            paid_ratio = float(rng.uniform(0.955, 0.993))
            payments = charges * paid_ratio
            new_overdue = charges - payments
            recoveries = min(arrears_stock * float(rng.uniform(0.055, 0.13)), arrears_stock)
            arrears_stock = max(0, arrears_stock + new_overdue - recoveries)
            old_frac = float(rng.uniform(0.25, 0.43))
            medium_frac = float(rng.uniform(0.19, 0.31))
            arrears_rows.append({"month": month, "building_id": bid, "estate": b["estate"],
                                 "charges": _safe_round(charges), "payments": _safe_round(payments),
                                 "new_overdue": _safe_round(new_overdue),
                                 "recoveries": _safe_round(recoveries),
                                 "arrears_total": _safe_round(arrears_stock),
                                 "over_90_days": _safe_round(arrears_stock * old_frac),
                                 "days_31_90": _safe_round(arrears_stock * medium_frac),
                                 "days_0_30": _safe_round(arrears_stock * (1 - old_frac - medium_frac))})

            inflow = float(b["area_m2"] * b["fund_rate"])
            outflow = float(spends.get((bid, month), 0))
            opening = fund_balance
            fund_balance += inflow - outflow
            fund_rows.append({"month": month, "building_id": bid, "estate": b["estate"],
                              "opening": _safe_round(opening),
                              "inflow": _safe_round(inflow), "outflow": _safe_round(outflow),
                              "closing": round(fund_balance, 2),
                              "minimum_reserve": _safe_round(b["area_m2"] * 27)})

    costs = pd.DataFrame(cost_rows)
    costs["delta"] = costs["actual"] - costs["plan"]
    costs["delta_pct"] = np.where(costs["plan"] != 0, costs["delta"] / costs["plan"] * 100, 0)
    utilities = pd.DataFrame(utility_rows)
    receivables = pd.DataFrame(arrears_rows)
    funds = pd.DataFrame(fund_rows)
    return {"buildings": buildings, "costs": costs, "utilities": utilities,
            "receivables": receivables, "funds": funds,
            "projects": projects, "inspections": inspections}


def period_filter(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp,
                  ids: list[str], field: str = "month") -> pd.DataFrame:
    return frame.loc[(frame[field] >= start) & (frame[field] <= end)
                     & frame["building_id"].isin(ids)].copy()


def period_latest(frame: pd.DataFrame, month: pd.Timestamp, ids: list[str]) -> pd.DataFrame:
    return frame.loc[(frame["month"] == month) & frame["building_id"].isin(ids)].copy()


def pct_change(current: float, previous: float) -> float | None:
    return (current / previous - 1) * 100 if previous else None


def cost_anomalies(costs: pd.DataFrame, selected_ids: list[str], month: pd.Timestamp,
                   threshold_pct: float = 20.0, min_difference: float = 1200.0) -> pd.DataFrame:
    """Zmiana m/m poprzedniego roku (ten sam miesiąc), per budynek i kategoria."""
    prev_month = month - pd.DateOffset(years=1)
    curr = costs.loc[(costs["month"] == month) & costs["building_id"].isin(selected_ids),
                     ["building_id", "estate", "category", "actual", "plan"]].copy()
    prev = costs.loc[(costs["month"] == prev_month) & costs["building_id"].isin(selected_ids),
                     ["building_id", "category", "actual"]].copy()
    prev = prev.rename(columns={"actual": "previous_actual"})
    df = curr.merge(prev, on=["building_id", "category"], how="inner")
    if df.empty:
        return pd.DataFrame(columns=["building_id", "estate", "category", "actual", "previous_actual",
                                     "difference", "yoy_pct", "plan", "plan_pct"])
    df["difference"] = df["actual"] - df["previous_actual"]
    df["yoy_pct"] = np.where(df["previous_actual"] > 0,
                              (df["actual"] / df["previous_actual"] - 1) * 100, 0)
    df["plan_pct"] = np.where(df["plan"] > 0, (df["actual"] / df["plan"] - 1) * 100, 0)
    df = df.loc[(df["yoy_pct"] >= threshold_pct) & (df["difference"] >= min_difference)]
    return df.sort_values(["difference", "yoy_pct"], ascending=False).reset_index(drop=True)


def check_cost_csv(imported: pd.DataFrame, valid_buildings: set[str]) -> list[str]:
    """Weryfikacja wgrywanego pliku, bez zapisania danych i bez automatycznego łączenia z demo."""
    required = {"month", "building_id", "category", "plan", "actual"}
    errors = []
    if not required.issubset(imported.columns):
        return ["Brak kolumn: " + ", ".join(sorted(required - set(imported.columns)))]
    if imported.empty:
        return ["Plik nie zawiera żadnych wierszy."]
    parsed_dates = pd.to_datetime(imported["month"], errors="coerce")
    if parsed_dates.isna().any():
        errors.append("Kolumna month zawiera niepoprawne daty.")
    if (~imported["building_id"].astype(str).isin(valid_buildings)).any():
        errors.append("Występują nieznane identyfikatory budynków.")
    if (~imported["category"].astype(str).isin(CATEGORIES)).any():
        errors.append("Występują kategorie spoza słownika.")
    for field in ("plan", "actual"):
        nums = pd.to_numeric(imported[field], errors="coerce")
        if nums.isna().any() or (nums < 0).any():
            errors.append(f"Kolumna {field} zawiera wartości puste, ujemne lub nieliczbowe.")
    if imported.duplicated(subset=["month", "building_id", "category"]).any():
        errors.append("Występują zduplikowane klucze miesiąc–budynek–kategoria.")
    return errors
