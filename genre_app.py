import streamlit as st
import pandas as pd
import ast
import plotly.express as px

st.set_page_config(page_title="UK Music Genre Explorer", layout="wide")


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("df_genre.csv")
    df["dates.start.localDate"] = pd.to_datetime(df["dates.start.localDate"])
    df["month"] = df["dates.start.localDate"].dt.strftime("%Y-%m")
    df["weekday"] = df["dates.start.localDate"].dt.day_name()
    df["is_weekend"] = df["weekday"].isin(["Friday", "Saturday", "Sunday"])

    # attraction_genres was saved as a stringified list — parse it back
    def parse_genres(val):
        if pd.isna(val):
            return []
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return []

    df["attraction_genres_list"] = df["attraction_genres"].apply(parse_genres)
    df["lineup_genre_count"] = df["attraction_genres_list"].apply(len)
    df["is_cross_genre"] = df["lineup_genre_count"] > 1

    return df


df = load_data()

st.title("UK music genre explorer")
st.caption(
    "Ticketmaster Discovery API — UK music events, June–August 2026. "
    "June has minimal coverage since the API only returns current/upcoming listings."
)


# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.header("Filters")

genres = sorted(df["genre_name"].dropna().unique())
selected_genres = st.sidebar.multiselect("Genre", genres, default=genres)

cities = sorted(df["city_name"].dropna().unique())
selected_cities = st.sidebar.multiselect("City", cities, default=[])

weekend_only = st.sidebar.checkbox("Weekend events only (Fri–Sun)", value=False)

filtered = df[df["genre_name"].isin(selected_genres)]
if selected_cities:
    filtered = filtered[filtered["city_name"].isin(selected_cities)]
if weekend_only:
    filtered = filtered[filtered["is_weekend"]]


# ---------------------------------------------------------------
# Tabs: Overview + Genre focus
# ---------------------------------------------------------------
tab_overview, tab_genre = st.tabs(["Overview", "Genre deep dive"])

with tab_overview:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total events", len(filtered))
    col2.metric("Distinct genres", filtered["genre_name"].nunique())
    col3.metric("Cross-genre lineups", int(filtered["is_cross_genre"].sum()))

    st.subheader("Events by genre")
    genre_counts = filtered["genre_name"].value_counts().reset_index()
    genre_counts.columns = ["genre", "event_count"]
    st.bar_chart(genre_counts.set_index("genre"))

    st.subheader("Events by city (top 15)")
    city_counts = filtered["city_name"].value_counts().head(15).reset_index()
    city_counts.columns = ["city", "event_count"]
    st.bar_chart(city_counts.set_index("city"))

    st.subheader("Events by month")
    month_counts = filtered["month"].value_counts().sort_index().reset_index()
    month_counts.columns = ["month", "event_count"]
    st.bar_chart(month_counts.set_index("month"))


with tab_genre:
    st.subheader("Genre × city — where is each genre concentrated?")
    if len(selected_genres) == 0:
        st.info("Select at least one genre in the sidebar.")
    else:
        pivot = pd.crosstab(filtered["city_name"], filtered["genre_name"])
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=False).drop(columns="total").head(15)

        fig_city = px.imshow(
            pivot,
            labels=dict(x="Genre", y="City", color="Event count"),
            aspect="auto",
            color_continuous_scale="YlOrRd",
        )
        fig_city.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_city, use_container_width=True)

    st.subheader("Genre × month loading")
    month_pivot = pd.crosstab(filtered["month"], filtered["genre_name"])

    fig_month = px.imshow(
        month_pivot,
        labels=dict(x="Genre", y="Month", color="Event count"),
        aspect="auto",
        color_continuous_scale="YlOrRd",
    )
    fig_month.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_month, use_container_width=True)

    st.subheader("Cross-genre lineups")
    st.caption(
        "Events where the lineup spans more than one distinct genre at the artist level — "
        "reveals genre-blending that the event's own single genre tag hides."
    )
    cross_genre_events = filtered[filtered["is_cross_genre"]][
        ["name", "genre_name", "attraction_genres_list", "city_name", "dates.start.localDate"]
    ].sort_values("dates.start.localDate")
    st.dataframe(cross_genre_events, use_container_width=True)

    st.subheader("Genre representation table")
    summary = filtered.groupby("genre_name").agg(
        event_count=("id", "count"),
        distinct_cities=("city_name", "nunique"),
        avg_lineup_genre_spread=("lineup_genre_count", "mean"),
    ).sort_values("event_count", ascending=False)
    st.dataframe(summary, use_container_width=True)

st.divider()
st.caption(
    "Data limitations: Ticketmaster's Discovery API reflects current/upcoming listings only; "
    "venue-level UK region is not populated in the source data, so city is used as the geographic unit. "
    "This view shows market-level genre activity only — compare against the festival reference list "
    "to assess actual representation gaps."
)