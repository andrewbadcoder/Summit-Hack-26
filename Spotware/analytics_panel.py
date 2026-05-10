"""
analytics_panel.py  —  SpotWare history analytics panel
Place this file alongside app.py (inside Spotware/).

Call render_analytics_panel() anywhere in your app.py after results exist,
or add it as a sidebar section / separate Streamlit page.
"""

import datetime
import streamlit as st
import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False

from cache import load_submissions, clear_cache, submission_count


# ── Colour map matching the app's action colours ─────────────────────────────
_COLOR_MAP = {
    "green": "#4db85c",
    "blue":  "#4a90d0",
    "amber": "#c98d2a",
    "red":   "#e5533d",
}
_FALLBACK = "#58a6ff"


def _submissions_to_df(rows: list[dict]) -> pd.DataFrame:
    """Convert cache rows to a flat DataFrame ready for charting."""
    records = []
    for r in rows:
        records.append(
            {
                "id":           r.get("id"),
                "created_at":   r.get("created_at", ""),
                "device_class": r.get("device_class") or "Unknown",
                "manufacturer": r.get("manufacturer") or "Unknown",
                "model":        r.get("model") or "Unknown",
                "condition":    r.get("condition") or "Unknown",
                "confidence":   float(r.get("confidence") or 0),
                "action":       r.get("action_label") or "Unknown",
                "color":        r.get("action_color") or "amber",
                "co2_kg":       float(r.get("co2_avoided_kg") or 0),
                "value_usd":    float(r.get("value_usd") or 0),
                "metals_g":     float(r.get("metals_total_g") or 0),
                "image_b64":    r.get("image_b64", ""),
            }
        )
    df = pd.DataFrame(records)
    if df.empty:
        return df

    def _try_parse(s):
        for fmt in ("%Y-%m-%d %H:%M", "%b %d, %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.datetime.strptime(s, fmt)
            except (ValueError, TypeError):
                pass
        return None

    df["dt"]   = df["created_at"].apply(_try_parse)
    df["date"] = df["dt"].apply(lambda x: x.date() if x else None)
    return df


# ── Main render function ──────────────────────────────────────────────────────

def render_analytics_panel():
    """
    Drop this call into app.py wherever you want the analytics section.
    Renders completely standalone — no external state needed.
    """
    st.markdown("<div class='panel-title' style='font-size:2rem;'>📊 Sustainability Impact Summary</div>", unsafe_allow_html=True)

    total = submission_count()
    if total == 0:
        st.markdown(
            "<div style='color:#4f6a80;font-size:0.85rem;padding:1rem 0;'>"
            "No submissions in cache yet. Run an analysis to start building history.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    rows = load_submissions(limit=500)
    df   = _submissions_to_df(rows)

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total submissions", f"{total:,}")
    k2.metric("CO₂ avoided",       f"{df['co2_kg'].sum():.1f} kg")
    k3.metric("Total value",       f"${df['value_usd'].sum():,.0f}")
    k4.metric("Metals recovered",  f"{df['metals_g'].sum():.0f} g")

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    if not _PLOTLY:
        st.warning("Install **plotly** (`pip install plotly`) to enable interactive charts.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ── Shared chart layout config ────────────────────────────────────────────
    chart_cfg = dict(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font_color="#8b949e",
        font_family="Inter, sans-serif",
        margin=dict(l=10, r=10, t=36, b=10),
    )

    col_left, col_right = st.columns(2)

    # 1. Donut — action breakdown
    with col_left:
        action_counts = df["action"].value_counts().reset_index()
        action_counts.columns = ["action", "count"]
        colors = [
            _COLOR_MAP.get(
                df[df["action"] == a]["color"].iloc[0]
                if not df[df["action"] == a].empty else "amber",
                _FALLBACK,
            )
            for a in action_counts["action"]
        ]
        fig_donut = go.Figure(
            go.Pie(
                labels=action_counts["action"],
                values=action_counts["count"],
                hole=0.55,
                marker_colors=colors,
                textinfo="label+percent",
                textfont_size=11,
            )
        )
        fig_donut.update_layout(
            title=dict(text="Recommended actions", font_size=13, x=0.5),
            showlegend=False,
            height=280,
            **chart_cfg,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # 2. Bar — device class frequency
    with col_right:
        class_counts = df["device_class"].value_counts().reset_index()
        class_counts.columns = ["device_class", "count"]
        fig_bar = px.bar(
            class_counts,
            x="count", y="device_class",
            orientation="h",
            color_discrete_sequence=["#58a6ff"],
            labels={"device_class": "", "count": "submissions"},
        )
        fig_bar.update_layout(
            title=dict(text="Device classes", font_size=13, x=0.5),
            height=280,
            yaxis=dict(categoryorder="total ascending"),
            **chart_cfg,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 3. Cumulative CO₂ area line (only if ≥2 dated entries)
    dated = df.dropna(subset=["date"]).copy()
    if not dated.empty and len(dated) > 1:
        daily_co2 = (
            dated.groupby("date")["co2_kg"]
            .sum()
            .reset_index()
            .sort_values("date")
        )
        daily_co2["cumulative_co2"] = daily_co2["co2_kg"].cumsum()
        fig_line = px.area(
            daily_co2,
            x="date", y="cumulative_co2",
            labels={"date": "", "cumulative_co2": "CO₂ avoided (kg)"},
            color_discrete_sequence=["#4db85c"],
        )
        fig_line.update_traces(fillcolor="rgba(77,184,92,0.15)")
        fig_line.update_layout(
            title=dict(text="Cumulative CO₂ avoided over time", font_size=13, x=0.5),
            height=220,
            **chart_cfg,
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # 4. Scatter — confidence vs recovery value
    fig_scatter = px.scatter(
        df,
        x="confidence",
        y="value_usd",
        color="condition",
        size="metals_g",
        size_max=22,
        hover_data=["device_class", "manufacturer", "model", "action"],
        labels={
            "confidence": "Confidence",
            "value_usd":  "Recovery value (USD)",
            "condition":  "Condition",
        },
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_scatter.update_layout(
        title=dict(
            text="Confidence vs. recovery value (bubble size = metals recovered)",
            font_size=13, x=0.5,
        ),
        height=280,
        legend=dict(bgcolor="rgba(0,0,0,0)", font_color="#8b949e"),
        **chart_cfg,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Full submission log ───────────────────────────────────────────────────
    with st.expander("📋  Full submission log"):
        display_cols = [
            "id", "created_at", "device_class", "manufacturer",
            "model", "condition", "action", "co2_kg", "value_usd", "metals_g",
        ]
        st.dataframe(
            df[display_cols].rename(columns={
                "id": "#", "created_at": "Timestamp",
                "device_class": "Class", "manufacturer": "Make",
                "model": "Model", "condition": "Condition",
                "action": "Action", "co2_kg": "CO₂ (kg)",
                "value_usd": "Value ($)", "metals_g": "Metals (g)",
            }),
            use_container_width=True,
            hide_index=True,
        )
        csv_data = df[display_cols].to_csv(index=False)
        st.download_button(
            label="⬇️  Export all submissions (.csv)",
            data=csv_data,
            file_name=f"spotware_history_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Danger zone ───────────────────────────────────────────────────────────
    with st.expander("🗑️  Danger zone — clear persistent cache"):
        st.warning("This permanently deletes all submission history from the SQLite database.")
        if st.button("💥  Delete all cache data", key="clear_db_btn"):
            clear_cache()
            st.success("Cache cleared. Refresh to see updated analytics.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)