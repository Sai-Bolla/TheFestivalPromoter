import streamlit as st
import pandas as pd
import ast
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="UK Music Genre Explorer", layout="wide")


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("df_combined_genre.csv")
    df["date"] = pd.to_datetime(df["date"], format="mixed", utc=True).dt.tz_localize(None)
    df["month"] = df["date"].dt.strftime("%Y-%m")
    df["weekday"] = df["date"].dt.day_name()
    df["is_weekend"] = df["weekday"].isin(["Friday", "Saturday", "Sunday"])

    # genres_bucketed was saved as a stringified list — parse it back
    def parse_genres(val):
        if pd.isna(val):
            return []
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return []

    df["genres_bucketed"] = df["genres_bucketed"].apply(parse_genres)
    df["genre_spread"] = df["genres_bucketed"].apply(len)
    df["is_cross_genre"] = df["genre_spread"] > 1

    return df


df = load_data()

st.title("UK music genre explorer")
st.caption(
    "Combined Ticketmaster + Skiddle data — UK music events, June–August 2026. "
    "Genres normalized into shared categories across both platforms."
)

# ---------------------------------------------------------------
# Live data status
# ---------------------------------------------------------------
status_col1, status_col2 = st.columns([3, 1])

with status_col1:
    timestamp_path = Path("last_updated.txt")
    if timestamp_path.exists():
        last_updated = timestamp_path.read_text().strip()
        st.info(f"📊 Data last refreshed: **{last_updated}**  |  {len(df)} events loaded")
    else:
        st.warning("No refresh timestamp found yet — run `get_data.py` to pull live data.")

with status_col2:
    if st.button("🔄 Refresh dashboard"):
        st.cache_data.clear()
        st.rerun()

st.caption(
    "To demonstrate live ingestion: run `python get_data.py` in a terminal, then click "
    "'Refresh dashboard' above to reload the newly pulled data."
)
st.divider()


# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.header("Filters")

source_options = sorted(df["source"].unique())
selected_sources = st.sidebar.multiselect(
    "Data source", source_options, default=source_options,
    help="Ticketmaster reflects general UK music activity. Skiddle reflects festival-tagged listings only."
)

# explode so each row = one (event, genre bucket) pair — needed since genres_bucketed is a list
df_exploded = df.explode("genres_bucketed").rename(columns={"genres_bucketed": "genre_bucket"})

genre_options = sorted(df_exploded["genre_bucket"].dropna().unique())
selected_genres = st.sidebar.multiselect("Genre bucket", genre_options, default=genre_options)

cities = sorted(df["city"].dropna().unique())
selected_cities = st.sidebar.multiselect("City", cities, default=[])

weekend_only = st.sidebar.checkbox("Weekend events only (Fri–Sun)", value=False)

filtered = df_exploded[
    df_exploded["source"].isin(selected_sources) &
    df_exploded["genre_bucket"].isin(selected_genres)
]
if selected_cities:
    filtered = filtered[filtered["city"].isin(selected_cities)]
if weekend_only:
    filtered = filtered[filtered["is_weekend"]]


# ---------------------------------------------------------------
# Tabs: Overview + Genre focus
# ---------------------------------------------------------------
tab_overview, tab_genre, tab_gap = st.tabs(["Overview", "Genre deep dive", "Supply vs. festival gap"])

with tab_overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total events", filtered["id"].nunique())
    col2.metric("Distinct genre buckets", filtered["genre_bucket"].nunique())
    col3.metric("Ticketmaster events", filtered[filtered["source"] == "ticketmaster"]["id"].nunique())
    col4.metric("Skiddle festivals", filtered[filtered["source"] == "skiddle"]["id"].nunique())

    st.subheader("Events by genre bucket")
    genre_counts = filtered["genre_bucket"].value_counts().reset_index()
    genre_counts.columns = ["genre_bucket", "event_count"]
    st.bar_chart(genre_counts.set_index("genre_bucket"))

    st.subheader("Events by city (top 15)")
    city_counts = filtered.drop_duplicates("id")["city"].value_counts().head(15).reset_index()
    city_counts.columns = ["city", "event_count"]
    st.bar_chart(city_counts.set_index("city"))

    st.subheader("Events by month")
    month_counts = filtered.drop_duplicates("id")["month"].value_counts().sort_index().reset_index()
    month_counts.columns = ["month", "event_count"]
    st.bar_chart(month_counts.set_index("month"))


with tab_genre:
    st.subheader("Genre bucket × city")
    if len(selected_genres) == 0:
        st.info("Select at least one genre bucket in the sidebar.")
    else:
        pivot = pd.crosstab(filtered["city"], filtered["genre_bucket"])
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=False).drop(columns="total").head(15)

        fig_city = px.imshow(
            pivot,
            labels=dict(x="Genre bucket", y="City", color="Event count"),
            aspect="auto",
            color_continuous_scale="YlOrRd",
        )
        fig_city.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_city, width="stretch")

    st.subheader("Genre bucket × month")
    month_pivot = pd.crosstab(filtered["month"], filtered["genre_bucket"])

    fig_month = px.imshow(
        month_pivot,
        labels=dict(x="Genre bucket", y="Month", color="Event count"),
        aspect="auto",
        color_continuous_scale="YlOrRd",
    )
    fig_month.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_month, width="stretch")

    st.subheader("Cross-genre events")
    st.caption(
        "Events tagged with more than one genre bucket — reveals genre-blending "
        "that a single genre label would hide."
    )
    cross_genre_events = filtered[filtered["is_cross_genre"]].drop_duplicates("id")[
        ["name", "genre_bucket", "city", "date", "source"]
    ].sort_values("date")
    st.dataframe(cross_genre_events, width="stretch")


with tab_gap:
    st.subheader("Genre bucket: market activity vs. festival presence")
    st.caption(
        "Compares Ticketmaster event volume (general market activity) against Skiddle "
        "festival-tagged listings, by genre bucket. A high ratio suggests strong demand "
        "with limited dedicated festival coverage — a potential gap."
    )

    tm_counts = filtered[filtered["source"] == "ticketmaster"]["genre_bucket"].value_counts()
    sk_counts = filtered[filtered["source"] == "skiddle"]["genre_bucket"].value_counts()

    gap_table = pd.DataFrame({
        "ticketmaster_events": tm_counts,
        "skiddle_festivals": sk_counts
    }).fillna(0)

    gap_table["ratio"] = gap_table["ticketmaster_events"] / gap_table["skiddle_festivals"].replace(0, 1)
    gap_table = gap_table.sort_values("ratio", ascending=False)

    st.dataframe(gap_table, width="stretch")

    fig_gap = px.bar(
        gap_table.reset_index().rename(columns={"index": "genre_bucket"}),
        x="genre_bucket", y="ratio",
        labels={"genre_bucket": "Genre bucket", "ratio": "Market activity : festival presence ratio"},
    )
    fig_gap.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_gap, width="stretch")

st.divider()
st.caption(
    "Data limitations: Ticketmaster's Discovery API reflects current/upcoming listings only. "
    "Skiddle data was pulled using eventcode=FEST and may include some non-music listings. "
    "17 exact-match duplicates across platforms were removed prior to combining. "
    "City-level (not regional) geography is used, based on the stronger overlap between "
    "Ticketmaster's city_name and Skiddle's venue.town fields."
)