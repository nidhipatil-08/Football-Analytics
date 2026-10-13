from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------- App configuration -----------------------------
st.set_page_config(
    page_title="PitchIQ | Football Performance Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).resolve().parent / "football_players.csv"
POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
REQUIRED_COLUMNS = [
    "player_id", "player_name", "team", "season", "position", "age",
    "matches_played", "minutes_played", "goals", "assists", "shots",
    "shots_on_target", "passes_completed", "tackles", "clean_sheets", "rating",
]
NUMERIC_COLUMNS = [
    "player_id", "age", "matches_played", "minutes_played", "goals", "assists",
    "shots", "shots_on_target", "passes_completed", "tackles", "clean_sheets", "rating",
]
DARK_BG = "#101715"
PANEL_BG = "#18251F"
GREEN = "#39D98A"
MINT = "#B9F6D2"
TEXT = "#E7F0EB"
MUTED = "#9DB2A6"


# ------------------------------- Styling ------------------------------------
st.markdown(
    f"""
    <style>
      .stApp {{ background: {DARK_BG}; color: {TEXT}; }}
      [data-testid="stSidebar"] {{ background: #142019; border-right: 1px solid #2A3D32; }}
      [data-testid="stMetric"] {{
        background: {PANEL_BG}; border: 1px solid #2A3D32; padding: 16px 18px;
        border-radius: 14px; min-height: 112px;
      }}
      [data-testid="stMetricLabel"] {{ color: {MUTED}; }}
      [data-testid="stMetricValue"] {{ color: {TEXT}; }}
      h1, h2, h3 {{ color: {TEXT}; }}
      .pitchiq-kicker {{ color: {GREEN}; font-size: .78rem; font-weight: 800;
                         letter-spacing: .16em; text-transform: uppercase; }}
      .pitchiq-note {{ color: {MUTED}; font-size: .9rem; }}
      .synthetic-banner {{
        background: #243B2E; border-left: 4px solid {GREEN}; border-radius: 8px;
        padding: 12px 15px; margin: 8px 0 18px 0; color: #E7F7ED;
      }}
      div[data-testid="stDownloadButton"] button {{
        background: {GREEN}; color: #102017; border: 0; font-weight: 700;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- Data functions -------------------------------
@st.cache_data
def load_data(path_string: str) -> pd.DataFrame:
    """Load the CSV, validate required fields, and prepare safe data types."""
    path = Path(path_string)
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {path.name}. Keep football_players.csv in the same folder as app.py."
        )

    data = pd.read_csv(path)
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError("The CSV is missing required columns: " + ", ".join(missing_columns))

    data = data[REQUIRED_COLUMNS].copy()
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    # Text columns are trimmed and empty strings become missing values.
    for column in ["player_name", "team", "season", "position"]:
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    # Invalid records are reported and excluded rather than silently rewritten.
    key_columns = ["player_id", "player_name", "team", "season", "position"]
    data = data.dropna(subset=key_columns).copy()
    data = data.drop_duplicates(subset=["player_id", "season"], keep="first").copy()

    nonnegative_columns = [
        "age", "matches_played", "minutes_played", "goals", "assists", "shots",
        "shots_on_target", "passes_completed", "tackles", "clean_sheets",
    ]
    for column in nonnegative_columns:
        data.loc[data[column] < 0, column] = np.nan

    # Invalid values are treated as missing. This avoids presenting impossible values.
    data.loc[~data["position"].isin(POSITIONS), "position"] = pd.NA
    data.loc[~data["rating"].between(1, 10), "rating"] = np.nan
    data.loc[data["shots_on_target"] > data["shots"], "shots_on_target"] = np.nan
    data.loc[data["clean_sheets"] > data["matches_played"], "clean_sheets"] = np.nan
    data.loc[data["matches_played"] > 0, "minutes_played"] = data.loc[
        data["matches_played"] > 0, "minutes_played"
    ].clip(upper=90 * data.loc[data["matches_played"] > 0, "matches_played"])

    return data.dropna(subset=["position"]).reset_index(drop=True)


def add_derived_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Add rates that are calculated from each player's season record."""
    result = data.copy()
    safe_minutes = result["minutes_played"].replace(0, np.nan)
    safe_shots = result["shots"].replace(0, np.nan)
    safe_matches = result["matches_played"].replace(0, np.nan)
    result["goal_contributions"] = result["goals"] + result["assists"]
    result["goals_per_90"] = result["goals"] / safe_minutes * 90
    result["assists_per_90"] = result["assists"] / safe_minutes * 90
    result["shot_conversion_pct"] = result["goals"] / safe_shots * 100
    result["avg_minutes_per_match"] = result["minutes_played"] / safe_matches
    return result


def apply_filters(data: pd.DataFrame, seasons, teams, positions, players) -> pd.DataFrame:
    filtered = data.copy()
    if seasons:
        filtered = filtered[filtered["season"].isin(seasons)]
    if teams:
        filtered = filtered[filtered["team"].isin(teams)]
    if positions:
        filtered = filtered[filtered["position"].isin(positions)]
    if players:
        filtered = filtered[filtered["player_name"].isin(players)]
    return filtered


def format_number(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}"


def style_chart(fig, height=360):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Arial, sans-serif"),
        height=height,
        margin=dict(l=12, r=12, t=48, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor=PANEL_BG, font_color=TEXT),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#293A31", zeroline=False)
    return fig


def show_empty_message():
    st.info("No records match the current filters. Try clearing one or more filters in the sidebar.")


def render_kpis(data: pd.DataFrame):
    total_players = data["player_id"].nunique()
    total_goals = data["goals"].sum(min_count=1)
    total_assists = data["assists"].sum(min_count=1)
    total_minutes = data["minutes_played"].sum(min_count=1)
    avg_rating = data["rating"].mean()

    cols = st.columns(5)
    metrics = [
        ("Players", format_number(total_players), "Unique player IDs"),
        ("Goals", format_number(total_goals), "Selected records"),
        ("Assists", format_number(total_assists), "Selected records"),
        ("Minutes played", format_number(total_minutes), "Total minutes"),
        ("Average rating", format_number(avg_rating, 2), "Scale: 1–10"),
    ]
    for col, (label, value, help_text) in zip(cols, metrics):
        col.metric(label, value, help=help_text)


def player_table(data: pd.DataFrame, key_prefix="table"):
    st.subheader("Player statistics")
    search = st.text_input(
        "Search player, team or position",
        placeholder="e.g. Alex, Northbridge FC, Forward",
        key=f"{key_prefix}_search",
    )
    view = data.copy()
    if search.strip():
        term = search.strip().casefold()
        mask = (
            view["player_name"].astype(str).str.casefold().str.contains(term, na=False)
            | view["team"].astype(str).str.casefold().str.contains(term, na=False)
            | view["position"].astype(str).str.casefold().str.contains(term, na=False)
        )
        view = view[mask]

    display_columns = [
        "player_name", "team", "season", "position", "age", "matches_played",
        "minutes_played", "goals", "assists", "shots", "rating",
        "goal_contributions", "goals_per_90", "assists_per_90", "shot_conversion_pct",
    ]
    display = view[display_columns].rename(columns={
        "player_name": "Player", "team": "Team", "season": "Season",
        "position": "Position", "age": "Age", "matches_played": "Matches",
        "minutes_played": "Minutes", "goals": "Goals", "assists": "Assists",
        "shots": "Shots", "rating": "Rating", "goal_contributions": "Goal contributions",
        "goals_per_90": "Goals / 90", "assists_per_90": "Assists / 90",
        "shot_conversion_pct": "Shot conversion %",
    })
    st.caption(f"{len(display):,} player-season records shown.")
    st.dataframe(display, use_container_width=True, hide_index=True, height=360)
    csv_bytes = view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv_bytes,
        file_name="pitchiq_filtered_player_stats.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )


# ------------------------------ Sidebar -------------------------------------
st.sidebar.markdown(
    f'<div class="pitchiq-kicker">⚽ PITCHIQ</div><h2 style="margin-top:0">Performance intelligence</h2>',
    unsafe_allow_html=True,
)
st.sidebar.caption("Explore player, team and position performance.")
st.sidebar.divider()

try:
    raw_data = load_data(str(DATA_PATH))
except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
    st.error(f"Data loading problem: {error}")
    st.stop()

data = add_derived_metrics(raw_data)
st.sidebar.markdown("### Global filters")
all_seasons = sorted(data["season"].dropna().unique().tolist())
selected_seasons = st.sidebar.multiselect("Season", all_seasons, default=all_seasons)
team_options = sorted(data["team"].dropna().unique().tolist())
selected_teams = st.sidebar.multiselect("Team", team_options, default=team_options)
position_options = [p for p in POSITIONS if p in data["position"].unique()]
selected_positions = st.sidebar.multiselect("Position", position_options, default=position_options)

# Cascading player options respect the season, team and position selections.
player_scope = data.copy()
if selected_seasons:
    player_scope = player_scope[player_scope["season"].isin(selected_seasons)]
if selected_teams:
    player_scope = player_scope[player_scope["team"].isin(selected_teams)]
if selected_positions:
    player_scope = player_scope[player_scope["position"].isin(selected_positions)]
player_options = sorted(player_scope["player_name"].dropna().unique().tolist())
selected_players = st.sidebar.multiselect("Player", player_options, default=[])

filtered = apply_filters(
    data, selected_seasons, selected_teams, selected_positions, selected_players
)

st.sidebar.divider()
st.sidebar.caption("Dataset: football_players.csv")
st.sidebar.caption(f"{raw_data['player_id'].nunique():,} unique synthetic players · {len(raw_data):,} player-season rows")
st.sidebar.caption("All figures are synthetic demo data.")


# ------------------------------ Header --------------------------------------
st.markdown('<div class="pitchiq-kicker">FOOTBALL PERFORMANCE INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("PitchIQ")
st.markdown(
    '<div class="synthetic-banner"><strong>SYNTHETIC DEMO DATA</strong> — '
    'These statistics are generated for demonstration and do not represent real players, clubs, '
    'or actual football results.</div>',
    unsafe_allow_html=True,
)
st.caption("Filter the dataset from the sidebar. KPIs, charts and tables update to match your selection.")

page = st.radio(
    "Dashboard section",
    ["Overview", "Player Analysis", "Team Analysis", "Position Analysis"],
    horizontal=True,
    label_visibility="collapsed",
)

if filtered.empty:
    show_empty_message()
    st.stop()

# -------------------------------- Overview ----------------------------------
if page == "Overview":
    st.header("Overview")
    st.caption("A high-level summary of the selected synthetic player-season records.")
    render_kpis(filtered)

    left, right = st.columns(2)
    team_summary = (
        filtered.groupby("team", as_index=False)
        .agg(Goals=("goals", "sum"), Assists=("assists", "sum"))
        .sort_values("Goals", ascending=False)
    )
    with left:
        fig = px.bar(
            team_summary, x="team", y="Goals", color="Goals",
            color_continuous_scale=["#24543C", GREEN],
            title="Goals by team", hover_data={"Assists": True, "Goals": ":,.0f"},
        )
        fig.update_xaxes(title="Team", tickangle=-25)
        fig.update_yaxes(title="Goals")
        st.plotly_chart(style_chart(fig), use_container_width=True)

    with right:
        position_summary = (
            filtered.groupby("position", as_index=False)
            .agg(Goals=("goals", "sum"), Players=("player_id", "nunique"))
        )
        fig = px.bar(
            position_summary, x="position", y="Goals", color="position",
            color_discrete_sequence=[GREEN, "#77BFA3", "#4B8F72", "#B9F6D2"],
            title="Goal output by position",
            hover_data={"Players": True, "Goals": ":,.0f"},
        )
        fig.update_xaxes(title="Position")
        fig.update_yaxes(title="Goals")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Quick insights")
    top_scorer = filtered.sort_values(["goals", "assists"], ascending=False).iloc[0]
    top_assist = filtered.sort_values(["assists", "goals"], ascending=False).iloc[0]
    avg_conversion = filtered["shot_conversion_pct"].replace([np.inf, -np.inf], np.nan).mean()
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Top scoring record:** {top_scorer['player_name']} ({top_scorer['team']}) — {int(top_scorer['goals'])} goals in {top_scorer['season']}.")
    c2.info(f"**Most assists:** {top_assist['player_name']} ({top_assist['team']}) — {int(top_assist['assists'])} assists in {top_assist['season']}.")
    c3.info(f"**Average shot conversion:** {avg_conversion:.1f}% across records with shots." if pd.notna(avg_conversion) else "Shot conversion is unavailable for the current selection.")

# ---------------------------- Player Analysis -------------------------------
elif page == "Player Analysis":
    st.header("Player Analysis")
    st.caption("Compare output, shooting volume and contribution rates. Compare players within similar contexts where possible.")

    candidates = sorted(filtered["player_name"].dropna().unique().tolist())
    default_compare = candidates[:min(3, len(candidates))]
    comparison = st.multiselect(
        "Choose players to compare", candidates, default=default_compare, key="player_comparison"
    )
    compare_data = filtered[filtered["player_name"].isin(comparison)].copy()

    if not compare_data.empty:
        comparison_summary = (
            compare_data.groupby(["player_name", "position"], as_index=False)
            .agg(Goals=("goals", "sum"), Assists=("assists", "sum"),
                 Minutes=("minutes_played", "sum"), Rating=("rating", "mean"),
                 Shots=("shots", "sum"))
        )
        fig = go.Figure()
        for _, row in comparison_summary.iterrows():
            fig.add_trace(go.Bar(
                name=row["player_name"],
                x=["Goals", "Assists"],
                y=[row["Goals"], row["Assists"]],
                hovertemplate=f"{row['player_name']}<br>%{{x}}: %{{y}}<extra></extra>",
            ))
        fig.update_layout(barmode="group", title="Goals and assists by selected player", xaxis_title="Metric", yaxis_title="Total")
        st.plotly_chart(style_chart(fig), use_container_width=True)

    left, right = st.columns(2)
    with left:
        fig = px.scatter(
            filtered, x="assists", y="goals", color="position", size="minutes_played",
            hover_name="player_name",
            hover_data={"team": True, "season": True, "rating": ":.2f",
                        "goal_contributions": True, "minutes_played": ":,.0f"},
            title="Goals versus assists",
            color_discrete_sequence=[GREEN, "#8CCFB0", "#5D9D7B", "#D0F7E0"],
        )
        fig.update_xaxes(title="Assists")
        fig.update_yaxes(title="Goals")
        st.plotly_chart(style_chart(fig), use_container_width=True)
    with right:
        fig = px.scatter(
            filtered, x="shots", y="goals", color="position", size="minutes_played",
            hover_name="player_name",
            hover_data={"team": True, "season": True, "shot_conversion_pct": ":.1f",
                        "shots_on_target": True, "minutes_played": ":,.0f"},
            title="Shots versus goals",
            color_discrete_sequence=[GREEN, "#8CCFB0", "#5D9D7B", "#D0F7E0"],
        )
        fig.update_xaxes(title="Shots")
        fig.update_yaxes(title="Goals")
        st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Player comparison table")
    if not compare_data.empty:
        st.dataframe(
            comparison_summary.sort_values("Goals", ascending=False),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Choose at least one player in the comparison selector to see a summary.")
    player_table(filtered, key_prefix="player")

# ----------------------------- Team Analysis -------------------------------
elif page == "Team Analysis":
    st.header("Team Analysis")
    st.caption("Aggregate player-season records to compare team output and represented squad size.")

    team_summary = (
        filtered.groupby("team", as_index=False)
        .agg(
            Goals=("goals", "sum"),
            Assists=("assists", "sum"),
            Players=("player_id", "nunique"),
            Avg_Rating=("rating", "mean"),
            Minutes=("minutes_played", "sum"),
        )
        .sort_values("Goals", ascending=False)
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            team_summary, y="team", x="Goals", orientation="h",
            color="Goals", color_continuous_scale=["#24543C", GREEN],
            title="Team goals", hover_data={"Assists": True, "Players": True},
        )
        fig.update_yaxes(title="Team", autorange="reversed")
        fig.update_xaxes(title="Goals")
        st.plotly_chart(style_chart(fig, height=430), use_container_width=True)
    with c2:
        fig = px.scatter(
            team_summary, x="Goals", y="Assists", size="Players", color="Avg_Rating",
            color_continuous_scale=["#24543C", GREEN], hover_name="team",
            hover_data={"Players": True, "Minutes": ":,.0f", "Avg_Rating": ":.2f"},
            title="Team goals versus assists",
        )
        fig.update_xaxes(title="Goals")
        fig.update_yaxes(title="Assists")
        st.plotly_chart(style_chart(fig, height=430), use_container_width=True)

    st.subheader("Team summary")
    team_display = team_summary.rename(columns={
        "team": "Team", "Goals": "Goals", "Assists": "Assists",
        "Players": "Unique players", "Avg_Rating": "Average rating", "Minutes": "Minutes played",
    })
    st.dataframe(team_display, use_container_width=True, hide_index=True)
    st.caption("Team totals aggregate the filtered player-season records; they are not official club statistics.")

# --------------------------- Position Analysis -----------------------------
else:
    st.header("Position Analysis")
    st.caption("Compare statistical profiles across goalkeepers, defenders, midfielders and forwards.")

    position_summary = (
        filtered.groupby("position", as_index=False)
        .agg(
            Players=("player_id", "nunique"),
            Goals=("goals", "sum"),
            Assists=("assists", "sum"),
            Avg_Goals=("goals", "mean"),
            Avg_Assists=("assists", "mean"),
            Avg_Rating=("rating", "mean"),
            Avg_Minutes=("minutes_played", "mean"),
            Avg_Tackles=("tackles", "mean"),
            Avg_Clean_Sheets=("clean_sheets", "mean"),
            Avg_Passes=("passes_completed", "mean"),
        )
    )
    order = [p for p in POSITIONS if p in position_summary["position"].tolist()]
    position_summary["position"] = pd.Categorical(position_summary["position"], categories=order, ordered=True)
    position_summary = position_summary.sort_values("position")

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            position_summary, x="position", y="Avg_Goals", color="position",
            color_discrete_sequence=[GREEN, "#8CCFB0", "#5D9D7B", "#D0F7E0"],
            title="Average goals per player-season",
            hover_data={"Players": True, "Avg_Assists": ":.2f"},
        )
        fig.update_xaxes(title="Position")
        fig.update_yaxes(title="Average goals")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_chart(fig), use_container_width=True)
    with right:
        rating_data = filtered.dropna(subset=["rating"])
        if rating_data.empty:
            st.info("Ratings are unavailable for the current selection.")
        else:
            fig = px.box(
                rating_data, x="position", y="rating", color="position",
                points="all", title="Player rating distribution",
                color_discrete_sequence=[GREEN, "#8CCFB0", "#5D9D7B", "#D0F7E0"],
                hover_data=["player_name", "team", "season"],
            )
            fig.update_xaxes(title="Position")
            fig.update_yaxes(title="Rating (1–10)", range=[1, 10])
            fig.update_layout(showlegend=False)
            st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Position profile")
    st.dataframe(
        position_summary.rename(columns={
            "position": "Position", "Players": "Unique players", "Goals": "Total goals",
            "Assists": "Total assists", "Avg_Goals": "Average goals",
            "Avg_Assists": "Average assists", "Avg_Rating": "Average rating",
            "Avg_Minutes": "Average minutes", "Avg_Tackles": "Average tackles",
            "Avg_Clean_Sheets": "Average clean sheets", "Avg_Passes": "Average completed passes",
        }).round(2),
        use_container_width=True, hide_index=True,
    )
    st.caption("Position-specific statistics should be interpreted in context; goalkeepers and forwards have different responsibilities.")

st.divider()
st.markdown(
    '<p class="pitchiq-note">PitchIQ · Synthetic demo dataset · Built with Python, Pandas, NumPy, Streamlit and Plotly.</p>',
    unsafe_allow_html=True,
)
