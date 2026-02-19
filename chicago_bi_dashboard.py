#!/usr/bin/env python3
"""
Advanced Business Intelligence Dashboard for Chicago Open Data.

This Streamlit app reads from FinalDB.db and provides interactive BI views on:
1) Socioeconomic indicators vs. education outcomes
2) Crime distribution across low- and high-income communities
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# Resolve the database path relative to this dashboard file.
DB_PATH = Path(__file__).resolve().parent / "FinalDB.db"


def configure_page() -> None:
    """Configure Streamlit page settings and dashboard-level styling."""
    st.set_page_config(
        page_title="Chicago BI Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for a cleaner BI presentation and stronger visual hierarchy.
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            }
            [data-testid="stMetric"] {
                background-color: white;
                border: 1px solid #dbeafe;
                border-radius: 12px;
                padding: 14px;
            }
            .dashboard-subtitle {
                margin-top: -6px;
                color: #334155;
                font-size: 0.98rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    """
    Execute a SQL query against FinalDB.db and return a DataFrame.

    The function is cached to keep the dashboard responsive while users interact
    with filters and tabs.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as exc:  # pragma: no cover - defensive UI guard
        st.error(f"Database query failed: {exc}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_socioeducation_dataset() -> pd.DataFrame:
    """
    Build a community-level socioeconomic + education dataset.

    SQL logic:
    - LEFT JOIN ensures communities remain visible even if school rows are missing.
    - NULL checks avoid introducing bad values into averages.
    - Empty/aggregate census rows are filtered out.
    """
    query = """
    SELECT
        CAST(c.COMMUNITY_AREA_NUMBER AS INTEGER) AS community_area_number,
        c.COMMUNITY_AREA_NAME AS community_area_name,
        c.HARDSHIP_INDEX AS hardship_index,
        c.PERCENT_HOUSEHOLDS_BELOW_POVERTY AS poverty_rate,
        AVG(CASE WHEN s.SAFETY_SCORE IS NOT NULL THEN s.SAFETY_SCORE END) AS avg_safety_score,
        COUNT(s.School_ID) AS school_count
    FROM CENSUS_DATA c
    LEFT JOIN CHICAGO_PUBLIC_SCHOOLS s
        ON CAST(s.COMMUNITY_AREA_NUMBER AS INTEGER) = CAST(c.COMMUNITY_AREA_NUMBER AS INTEGER)
    WHERE c.COMMUNITY_AREA_NUMBER IS NOT NULL
      AND TRIM(COALESCE(c.COMMUNITY_AREA_NAME, '')) <> ''
    GROUP BY
        CAST(c.COMMUNITY_AREA_NUMBER AS INTEGER),
        c.COMMUNITY_AREA_NAME,
        c.HARDSHIP_INDEX,
        c.PERCENT_HOUSEHOLDS_BELOW_POVERTY
    ORDER BY community_area_number
    """

    df = run_query(query)
    numeric_cols = [
        "community_area_number",
        "hardship_index",
        "poverty_rate",
        "avg_safety_score",
        "school_count",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_crime_dataset() -> pd.DataFrame:
    """
    Build a crime dataset enriched with socioeconomic context by community area.

    SQL logic:
    - COALESCE keeps categorical fields usable for charts.
    - LEFT JOIN preserves crime rows even when census linkage is incomplete.
    - Explicit numeric conversion happens in pandas for safer downstream math.
    """
    query = """
    SELECT
        cr.ID AS crime_id,
        COALESCE(cr.CASE_NUMBER, 'N/A') AS case_number,
        COALESCE(cr.PRIMARY_TYPE, 'UNKNOWN') AS primary_type,
        COALESCE(cr.DESCRIPTION, 'No description') AS description,
        CAST(cr.COMMUNITY_AREA_NUMBER AS INTEGER) AS community_area_number,
        COALESCE(c.COMMUNITY_AREA_NAME, 'Unknown') AS community_area_name,
        c.PER_CAPITA_INCOME AS per_capita_income,
        c.PERCENT_HOUSEHOLDS_BELOW_POVERTY AS poverty_rate,
        c.HARDSHIP_INDEX AS hardship_index,
        cr.YEAR AS crime_year
    FROM CHICAGO_CRIME_DATA cr
    LEFT JOIN CENSUS_DATA c
        ON CAST(cr.COMMUNITY_AREA_NUMBER AS INTEGER) = CAST(c.COMMUNITY_AREA_NUMBER AS INTEGER)
    WHERE cr.COMMUNITY_AREA_NUMBER IS NOT NULL
    """

    df = run_query(query)
    for col in ["community_area_number", "per_capita_income", "poverty_rate", "hardship_index"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def format_metric(value: float | int | None, decimals: int = 1, suffix: str = "") -> str:
    """Format KPI values and handle null/NaN safely."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value:,.{decimals}f}{suffix}" if isinstance(value, float) else f"{value:,}{suffix}"


def build_sidebar_filters(
    socio_df: pd.DataFrame, crime_df: pd.DataFrame
) -> tuple[Sequence[str], Sequence[str], int, int]:
    """Render sidebar controls and return selected filters."""
    st.sidebar.header("Dashboard Filters")

    community_options = sorted(
        [area for area in socio_df["community_area_name"].dropna().unique().tolist() if area != "Unknown"]
    )
    selected_communities = st.sidebar.multiselect(
        "Community Area",
        options=community_options,
        help="Filter both tabs to one or more Chicago communities.",
    )

    crime_type_options = sorted(crime_df["primary_type"].dropna().unique().tolist())
    selected_crime_types = st.sidebar.multiselect(
        "Crime Type",
        options=crime_type_options,
        help="Optional filter applied to the Crime Hotspots tab.",
    )

    income_series = pd.to_numeric(crime_df["per_capita_income"], errors="coerce").dropna()
    if income_series.empty:
        min_income, max_income, default_income = 0, 10000, 5000
    else:
        min_income = int(income_series.min())
        max_income = int(income_series.max())
        default_income = int(income_series.median())
        if min_income == max_income:
            max_income = min_income + 1

    income_threshold = st.sidebar.slider(
        "Income Split Threshold (Per Capita Income)",
        min_value=min_income,
        max_value=max_income,
        value=default_income,
        step=max(100, (max_income - min_income) // 100),
        help="Communities at or below this value are classified as low-income.",
    )

    top_n = st.sidebar.slider(
        "Top Crime Types to Compare",
        min_value=5,
        max_value=20,
        value=10,
        step=1,
    )

    return selected_communities, selected_crime_types, income_threshold, top_n


def apply_filters(
    socio_df: pd.DataFrame,
    crime_df: pd.DataFrame,
    selected_communities: Sequence[str],
    selected_crime_types: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply sidebar selections to both base datasets."""
    filtered_socio = socio_df.copy()
    filtered_crime = crime_df.copy()

    if selected_communities:
        filtered_socio = filtered_socio[
            filtered_socio["community_area_name"].isin(selected_communities)
        ]
        filtered_crime = filtered_crime[
            filtered_crime["community_area_name"].isin(selected_communities)
        ]

    if selected_crime_types:
        filtered_crime = filtered_crime[filtered_crime["primary_type"].isin(selected_crime_types)]

    return filtered_socio, filtered_crime


def render_kpis(socio_df: pd.DataFrame, crime_df: pd.DataFrame, income_threshold: int) -> None:
    """Render dashboard KPI cards at the top of the page."""
    known_income_crime = crime_df[crime_df["per_capita_income"].notna()].copy()
    low_income_share = np.nan
    if not known_income_crime.empty:
        low_income_share = (
            100.0
            * (known_income_crime["per_capita_income"] <= income_threshold).sum()
            / len(known_income_crime)
        )

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Communities in View", format_metric(socio_df["community_area_name"].nunique(), 0))
    kpi_cols[1].metric("Avg Hardship Index", format_metric(socio_df["hardship_index"].mean(), 1))
    kpi_cols[2].metric("Avg Poverty Rate", format_metric(socio_df["poverty_rate"].mean(), 1, "%"))
    kpi_cols[3].metric("Avg School Safety", format_metric(socio_df["avg_safety_score"].mean(), 1))
    kpi_cols[4].metric("Low-Income Crime Share", format_metric(low_income_share, 1, "%"))


def render_socioeducation_tab(socio_df: pd.DataFrame) -> None:
    """Render the Socioeconomic & Education analytics tab."""
    st.subheader("Socioeconomic & Education")
    st.caption(
        "Analyze how hardship and poverty levels align with average school safety scores at community level."
    )

    viz_df = socio_df.copy()
    valid_df = viz_df.dropna(subset=["hardship_index", "poverty_rate", "avg_safety_score"])

    if valid_df.empty:
        st.warning("No data available for this view after filters. Try broadening your filters.")
        return

    col1, col2 = st.columns(2)

    # Scatter plot: Poverty vs safety, colored by hardship and sized by number of schools.
    scatter_fig = px.scatter(
        valid_df,
        x="poverty_rate",
        y="avg_safety_score",
        size="school_count",
        color="hardship_index",
        hover_name="community_area_name",
        color_continuous_scale="Turbo",
        labels={
            "poverty_rate": "Households Below Poverty (%)",
            "avg_safety_score": "Average School Safety Score",
            "hardship_index": "Hardship Index",
            "school_count": "Schools",
        },
        title="Community Poverty vs. School Safety (Bubble Size = School Count)",
    )
    scatter_fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    col1.plotly_chart(scatter_fig, width="stretch")

    # Correlation heatmap: Quantifies relationship among hardship, poverty, and safety.
    corr_df = valid_df[["hardship_index", "poverty_rate", "avg_safety_score"]].corr()
    heatmap_fig = px.imshow(
        corr_df,
        text_auto=".2f",
        zmin=-1,
        zmax=1,
        color_continuous_scale="RdBu_r",
        labels=dict(color="Correlation"),
        title="Correlation Matrix: Hardship, Poverty, and School Safety",
        aspect="auto",
    )
    heatmap_fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    col2.plotly_chart(heatmap_fig, width="stretch")

    summary_cols = [
        "community_area_name",
        "hardship_index",
        "poverty_rate",
        "avg_safety_score",
        "school_count",
    ]
    st.markdown("**Community Detail (Sorted by Hardship Index)**")
    st.dataframe(
        valid_df[summary_cols]
        .sort_values(by="hardship_index", ascending=False)
        .rename(
            columns={
                "community_area_name": "Community",
                "hardship_index": "Hardship Index",
                "poverty_rate": "Poverty Rate (%)",
                "avg_safety_score": "Avg Safety Score",
                "school_count": "School Count",
            }
        ),
        width="stretch",
        hide_index=True,
    )


def render_crime_hotspots_tab(
    crime_df: pd.DataFrame, income_threshold: int, top_n: int
) -> None:
    """Render the Crime Hotspots analytics tab."""
    st.subheader("Crime Hotspots")
    st.caption("Compare crime type concentration between low-income and high-income communities.")

    if crime_df.empty:
        st.warning("No crime data available for this view after filters.")
        return

    working_df = crime_df.copy()

    # Create an income segment for side-by-side comparisons.
    working_df["income_segment"] = np.where(
        working_df["per_capita_income"].isna(),
        "Unknown / Missing Income",
        np.where(
            working_df["per_capita_income"] <= income_threshold,
            "Low Income Areas",
            "High Income Areas",
        ),
    )

    compare_df = working_df[
        working_df["income_segment"].isin(["Low Income Areas", "High Income Areas"])
    ]

    if compare_df.empty:
        st.warning(
            "No low/high income comparison data is available with the current filters or income threshold."
        )
        return

    grouped = (
        compare_df.groupby(["income_segment", "primary_type"], dropna=False)
        .size()
        .reset_index(name="crime_count")
    )

    top_crimes = (
        grouped.groupby("primary_type", dropna=False)["crime_count"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .index
    )
    grouped_top = grouped[grouped["primary_type"].isin(top_crimes)]

    col1, col2 = st.columns([2, 1])

    # Grouped bar chart: side-by-side low vs high income crime volume by type.
    bar_fig = px.bar(
        grouped_top,
        x="primary_type",
        y="crime_count",
        color="income_segment",
        barmode="group",
        color_discrete_map={
            "Low Income Areas": "#f97316",
            "High Income Areas": "#0ea5e9",
        },
        labels={
            "primary_type": "Crime Type",
            "crime_count": "Incident Count",
            "income_segment": "Income Segment",
        },
        title=f"Top {top_n} Crime Types: Low- vs High-Income Communities",
    )
    bar_fig.update_layout(margin=dict(l=20, r=20, t=60, b=20), xaxis_tickangle=-35)
    col1.plotly_chart(bar_fig, width="stretch")

    # Donut chart: overall share of incidents by low/high income segment.
    segment_share = (
        compare_df.groupby("income_segment", dropna=False)
        .size()
        .reset_index(name="crime_count")
    )
    pie_fig = px.pie(
        segment_share,
        values="crime_count",
        names="income_segment",
        hole=0.45,
        color="income_segment",
        color_discrete_map={
            "Low Income Areas": "#f97316",
            "High Income Areas": "#0ea5e9",
        },
        title="Crime Share by Income Segment",
    )
    pie_fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    col2.plotly_chart(pie_fig, width="stretch")

    unknown_income_count = (working_df["income_segment"] == "Unknown / Missing Income").sum()
    if unknown_income_count:
        st.caption(
            f"{unknown_income_count} crime record(s) were excluded from low/high segmentation due to missing income data."
        )

    hotspots = (
        compare_df.groupby(["community_area_name", "income_segment"], dropna=False)
        .size()
        .reset_index(name="crime_count")
        .sort_values("crime_count", ascending=False)
        .head(15)
        .rename(
            columns={
                "community_area_name": "Community",
                "income_segment": "Income Segment",
                "crime_count": "Incidents",
            }
        )
    )
    st.markdown("**Top Crime Hotspots (Filtered View)**")
    st.dataframe(hotspots, width="stretch", hide_index=True)


def main() -> None:
    """App entry point."""
    configure_page()

    st.title("Chicago Advanced Business Intelligence Dashboard")
    st.markdown(
        (
            "<div class='dashboard-subtitle'>Correlating socioeconomic hardship with public safety "
            "and education outcomes using Chicago open data.</div>"
        ),
        unsafe_allow_html=True,
    )

    if not DB_PATH.exists():
        st.error(
            "Database not found. Generate it first by running: `python chicago_data_analysis.py`"
        )
        st.stop()

    socio_df = load_socioeducation_dataset()
    crime_df = load_crime_dataset()

    if socio_df.empty or crime_df.empty:
        st.error(
            "One or more required datasets are empty in `FinalDB.db`. Rebuild the database and try again."
        )
        st.stop()

    (
        selected_communities,
        selected_crime_types,
        income_threshold,
        top_n,
    ) = build_sidebar_filters(socio_df, crime_df)

    filtered_socio, filtered_crime = apply_filters(
        socio_df,
        crime_df,
        selected_communities,
        selected_crime_types,
    )

    render_kpis(filtered_socio, filtered_crime, income_threshold)

    tab1, tab2 = st.tabs(["Socioeconomic & Education", "Crime Hotspots"])
    with tab1:
        render_socioeducation_tab(filtered_socio)
    with tab2:
        render_crime_hotspots_tab(filtered_crime, income_threshold, top_n)

    st.caption(
        "Data source: `FinalDB.db` tables `CENSUS_DATA`, `CHICAGO_PUBLIC_SCHOOLS`, and `CHICAGO_CRIME_DATA`."
    )


if __name__ == "__main__":
    main()
