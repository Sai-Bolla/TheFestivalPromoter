import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from geopy.distance import geodesic


class FestivalOpportunityAnalyzer:
    """
    Analyzes event data to identify opportunities for new mid-sized festivals
    """

    def __init__(self, df: pd.DataFrame, regions_df: pd.DataFrame):
        """
        Initialize with event data and region data

        Args:
            df: DataFrame with event data (event_name, venue_name, latitude, longitude, date, source, genre)
            regions_df: DataFrame with region data (region, population, lat, lon)
        """
        self.df = df.copy()
        self.regions_df = regions_df.copy()

        # Parse dates
        if "date" in self.df.columns:
            self.df["date_parsed"] = pd.to_datetime(self.df["date"], errors="coerce")
            self.df = self.df.dropna(subset=["date_parsed"])

        # Assign regions to events
        self.df = self.assign_regions_to_events()

    def assign_regions_to_events(self) -> pd.DataFrame:
        """Assign UK regions to each event based on coordinates"""
        if self.df.empty or self.regions_df.empty:
            return self.df

        def get_region(lat, lon):
            min_distance = float("inf")
            assigned = "Other"

            for _, region in self.regions_df.iterrows():
                distance = (
                    (lat - region["lat"]) ** 2 + (lon - region["lon"]) ** 2
                ) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    assigned = region["region"]

            # Only assign if within reasonable distance (approximately 50 miles)
            if min_distance > 0.7:  # Roughly 50 miles
                assigned = "Other"
            return assigned

        self.df["region"] = self.df.apply(
            lambda row: get_region(row["latitude"], row["longitude"]), axis=1
        )

        return self.df

    def calculate_region_density(self) -> pd.DataFrame:
        """Calculate event density per region"""
        if self.df.empty:
            return pd.DataFrame()

        # Count events per region
        region_counts = self.df.groupby("region").size().reset_index(name="event_count")

        # Merge with population data
        region_density = region_counts.merge(
            self.regions_df[["region", "population"]], on="region", how="left"
        )

        # Fill missing populations and ensure all regions are included
        if not self.regions_df.empty:
            # Get all regions from regions_df
            all_regions = self.regions_df[["region"]].copy()
            region_density = all_regions.merge(region_density, on="region", how="left")
            region_density["event_count"] = region_density["event_count"].fillna(0)

        # Fill missing populations
        region_density["population"] = region_density["population"].fillna(1)

        # Calculate metrics
        region_density["events_per_100k"] = (
            region_density["event_count"] / (region_density["population"] / 100000)
        ).round(2)

        # Add density rating
        def get_density_rating(events_per_100k):
            if events_per_100k >= 50:
                return "Very High"
            elif events_per_100k >= 30:
                return "High"
            elif events_per_100k >= 15:
                return "Medium"
            elif events_per_100k >= 5:
                return "Low"
            else:
                return "Very Low"

        region_density["density_rating"] = region_density["events_per_100k"].apply(
            get_density_rating
        )

        return region_density

    def find_opportunity_regions(self) -> pd.DataFrame:
        """
        Identify regions with low event density but high potential
        Returns DataFrame with opportunity scores
        """
        density_df = self.calculate_region_density()

        if density_df.empty:
            return pd.DataFrame()

        # Filter to "Other" and low density regions
        opportunity_df = density_df[
            (density_df["density_rating"].isin(["Very Low", "Low"]))
            | (density_df["region"] == "Other")
        ].copy()

        # Add latitude and longitude from regions data
        if not self.regions_df.empty:
            opportunity_df = opportunity_df.merge(
                self.regions_df[["region", "lat", "lon"]], on="region", how="left"
            )

        # Calculate opportunity score
        def calculate_opportunity_score(row):
            score = 0

            # Population factor (larger population = more potential)
            if row["population"] > 1_000_000:
                score += 30
            elif row["population"] > 500_000:
                score += 20
            elif row["population"] > 200_000:
                score += 10

            # Density factor (lower density = more opportunity)
            if row["events_per_100k"] < 5:
                score += 30
            elif row["events_per_100k"] < 10:
                score += 20
            elif row["events_per_100k"] < 20:
                score += 10

            # Region name bonus (known music cities)
            high_potential_regions = [
                "Newcastle",
                "Liverpool",
                "Bristol",
                "Nottingham",
                "Cardiff",
                "Sheffield",
                "Leeds",
                "Glasgow",
                "Belfast",
            ]
            if any(city in row["region"] for city in high_potential_regions):
                score += 20

            # Bonus for "Other" regions (unserved markets)
            if row["region"] == "Other":
                score += 15

            return min(score, 100)  # Cap at 100

        opportunity_df["opportunity_score"] = opportunity_df.apply(
            calculate_opportunity_score, axis=1
        )

        # Add opportunity rating
        def get_opportunity_rating(score):
            if score >= 70:
                return "High"
            elif score >= 50:
                return "Medium"
            else:
                return "Low"

        opportunity_df["opportunity_rating"] = opportunity_df[
            "opportunity_score"
        ].apply(get_opportunity_rating)

        # Fill NaN coordinates with default values for visualization
        if "lat" in opportunity_df.columns:
            opportunity_df["lat"] = opportunity_df["lat"].fillna(
                52.0
            )  # Default UK center
        else:
            opportunity_df["lat"] = 52.0

        if "lon" in opportunity_df.columns:
            opportunity_df["lon"] = opportunity_df["lon"].fillna(-2.0)
        else:
            opportunity_df["lon"] = -2.0

        return opportunity_df.sort_values("opportunity_score", ascending=False)

    def analyze_calendar_gaps(self, min_gap_days: int = 3) -> Dict:
        """
        Analyze calendar for gaps where a festival could fit
        """
        if self.df.empty:
            return {}

        # Sort dates
        dates = self.df["date_parsed"].dropna().sort_values().unique()

        if len(dates) < 2:
            return {}

        # Find gaps
        gaps = []
        for i in range(len(dates) - 1):
            gap_days = (dates[i + 1] - dates[i]).days
            if gap_days > min_gap_days:
                gaps.append(
                    {
                        "start": dates[i],
                        "end": dates[i + 1],
                        "duration_days": gap_days,
                        "month": dates[i].strftime("%B"),
                        "year": dates[i].year,
                        "season": self.get_season(dates[i]),
                    }
                )

        # Analyze gaps by season
        seasonal_gaps = {}
        for gap in gaps:
            season = gap["season"]
            if season not in seasonal_gaps:
                seasonal_gaps[season] = []
            seasonal_gaps[season].append(gap)

        # Find the best gap for a festival (summer gaps are ideal)
        festival_gaps = []
        for gap in gaps:
            if gap["duration_days"] >= 7 and gap["season"] in [
                "Summer",
                "Early Autumn",
            ]:
                festival_gaps.append(gap)

        return {
            "total_gaps": len(gaps),
            "seasonal_gaps": seasonal_gaps,
            "festival_calendar_gaps": festival_gaps,
            "best_gap_for_festival": festival_gaps[0] if festival_gaps else None,
            "months_with_most_gaps": self.get_most_gap_months(gaps),
        }

    def get_season(self, date: datetime) -> str:
        """Get season for a date"""
        month = date.month
        if 3 <= month <= 5:
            return "Spring"
        elif 6 <= month <= 8:
            return "Summer"
        elif 9 <= month <= 11:
            return "Early Autumn"
        else:
            return "Winter"

    def get_most_gap_months(self, gaps: List[Dict]) -> Dict:
        """Find months with most gaps"""
        month_counts = {}
        for gap in gaps:
            month = gap["month"]
            month_counts[month] = month_counts.get(month, 0) + 1
        return dict(sorted(month_counts.items(), key=lambda x: x[1], reverse=True))

    def analyze_genre_gaps(self, region: Optional[str] = None) -> Dict:
        """
        Analyze genre distribution to find underserved genres
        """
        if "genre" not in self.df.columns:
            return {}

        # Filter by region if specified
        if region and region != "All":
            df_filtered = self.df[self.df["region"] == region]
        else:
            df_filtered = self.df

        if df_filtered.empty:
            return {}

        # Count genres
        genre_counts = df_filtered["genre"].value_counts()

        # Get unique genres
        all_genres = set()
        for genre_str in df_filtered["genre"].dropna():
            for g in str(genre_str).split(","):
                all_genres.add(g.strip())

        # Identify underserved genres
        underserved = []
        for genre in all_genres:
            count = df_filtered[
                df_filtered["genre"].str.contains(genre, na=False)
            ].shape[0]
            if count < df_filtered.shape[0] * 0.05:  # Less than 5% of events
                underserved.append(
                    {
                        "genre": genre,
                        "count": count,
                        "percentage": (count / df_filtered.shape[0]) * 100,
                    }
                )

        return {
            "total_events": df_filtered.shape[0],
            "unique_genres": len(all_genres),
            "top_genres": genre_counts.head(10).to_dict(),
            "underserved_genres": sorted(underserved, key=lambda x: x["count"])[:10],
            "genre_diversity_score": (
                len(all_genres) / df_filtered.shape[0] * 100
                if df_filtered.shape[0] > 0
                else 0
            ),
        }

    def identify_festival_opportunities(self) -> Dict:
        """
        Main method to identify festival opportunities
        """
        # 1. Region analysis
        region_opportunities = self.find_opportunity_regions()

        # 2. Calendar analysis
        calendar_gaps = self.analyze_calendar_gaps()

        # 3. Genre analysis by region
        genre_opportunities = {}
        for region in region_opportunities["region"].head(5).tolist():
            genre_opportunities[region] = self.analyze_genre_gaps(region)

        # 4. Generate recommendations
        recommendations = self.generate_recommendations(
            region_opportunities, calendar_gaps, genre_opportunities
        )

        return {
            "region_opportunities": region_opportunities,
            "calendar_gaps": calendar_gaps,
            "genre_opportunities": genre_opportunities,
            "recommendations": recommendations,
        }

    def generate_recommendations(
        self, region_opp: pd.DataFrame, calendar_gaps: Dict, genre_opp: Dict
    ) -> List[Dict]:
        """
        Generate specific festival recommendations
        """
        recommendations = []

        # 1. Top region recommendation
        if not region_opp.empty:
            top_region = region_opp.iloc[0]
            recommendations.append(
                {
                    "priority": 1,
                    "type": "Region Opportunity",
                    "title": f"Mid-sized Festival in {top_region['region']}",
                    "description": f"""
                {top_region['region']} shows strong potential with {top_region['event_count']} events 
                and only {top_region['events_per_100k']:.1f} events per 100,000 people. 
                With a population of {top_region['population']:,}, this region is underserved.
                """,
                    "score": top_region["opportunity_score"],
                    "rating": top_region["opportunity_rating"],
                }
            )

        # 2. Calendar recommendation
        if calendar_gaps.get("best_gap_for_festival"):
            best_gap = calendar_gaps["best_gap_for_festival"]
            recommendations.append(
                {
                    "priority": 2,
                    "type": "Calendar Opportunity",
                    "title": f"Fill the {best_gap['duration_days']}-day Gap in {best_gap['season']}",
                    "description": f"""
                A {best_gap['duration_days']}-day gap exists between events in {best_gap['month']} ({best_gap['year']}).
                This presents an ideal window for a mid-sized festival.
                """,
                    "score": min(best_gap["duration_days"] * 5, 90),
                    "rating": "High" if best_gap["duration_days"] >= 14 else "Medium",
                }
            )

        # 3. Genre recommendations
        for region, genre_data in genre_opp.items():
            if genre_data and genre_data.get("underserved_genres"):
                top_underserved = genre_data["underserved_genres"][:3]
                for g in top_underserved:
                    recommendations.append(
                        {
                            "priority": 3,
                            "type": "Genre Opportunity",
                            "title": f"{g['genre']} Festival in {region}",
                            "description": f"""
                        {g['genre']} music is underrepresented in {region} with only {g['count']} events 
                        ({g['percentage']:.1f}% of events). A specialized festival could fill this gap.
                        """,
                            "score": min(100 - g["percentage"], 80),
                            "rating": "High" if g["percentage"] < 5 else "Medium",
                        }
                    )

        return recommendations

    def create_visualizations(self) -> Dict:
        """Create visualizations for festival opportunity analysis"""
        plots = {}

        # 1. Region opportunity map
        region_opp = self.find_opportunity_regions()
        if (
            not region_opp.empty
            and "lat" in region_opp.columns
            and "lon" in region_opp.columns
        ):
            try:
                fig1 = px.scatter_mapbox(
                    region_opp,
                    lat="lat",
                    lon="lon",
                    size="opportunity_score",
                    color="opportunity_rating",
                    hover_name="region",
                    hover_data={
                        "event_count": True,
                        "events_per_100k": ":.1f",
                        "population": ":,.0f",
                    },
                    title="Festival Opportunity Map",
                    color_discrete_map={
                        "High": "green",
                        "Medium": "yellow",
                        "Low": "red",
                    },
                    zoom=5,
                    height=500,
                )
                fig1.update_layout(mapbox_style="carto-positron")
                plots["opportunity_map"] = fig1
            except Exception as e:
                print(f"Could not create opportunity map: {str(e)}")
                # Create a fallback bar chart
                fig1 = px.bar(
                    region_opp.head(10),
                    x="region",
                    y="opportunity_score",
                    color="opportunity_rating",
                    title="Top 10 Regions by Opportunity Score",
                    color_discrete_map={
                        "High": "green",
                        "Medium": "yellow",
                        "Low": "red",
                    },
                )
                plots["opportunity_map"] = fig1

        # 2. Density comparison
        density = self.calculate_region_density()
        if not density.empty:
            try:
                fig2 = px.bar(
                    density.sort_values("events_per_100k", ascending=False),
                    x="region",
                    y="events_per_100k",
                    color="density_rating",
                    title="Events per 100,000 Population by Region",
                    color_discrete_map={
                        "Very High": "darkgreen",
                        "High": "green",
                        "Medium": "yellow",
                        "Low": "orange",
                        "Very Low": "red",
                    },
                    text=density["event_count"].apply(lambda x: f"{x} events"),
                )
                fig2.update_traces(textposition="outside")
                fig2.update_layout(xaxis_tickangle=-45, height=400, showlegend=True)
                plots["density_chart"] = fig2
            except Exception as e:
                print(f"Could not create density chart: {str(e)}")

        # 3. Calendar gap timeline
        calendar = self.analyze_calendar_gaps()
        if calendar.get("festival_calendar_gaps"):
            try:
                gaps_df = pd.DataFrame(calendar["festival_calendar_gaps"])

                fig3 = go.Figure()

                # Add events as scatter
                events = self.df[["date_parsed", "event_name"]].dropna()
                if not events.empty:
                    fig3.add_trace(
                        go.Scatter(
                            x=events["date_parsed"],
                            y=[1] * len(events),
                            mode="markers",
                            name="Events",
                            marker=dict(color="blue", size=6),
                            hovertext=events["event_name"],
                            hoverinfo="text+x",
                        )
                    )

                # Add gaps as rectangles
                for _, gap in gaps_df.iterrows():
                    fig3.add_vrect(
                        x0=gap["start"],
                        x1=gap["end"],
                        fillcolor="red",
                        opacity=0.2,
                        layer="below",
                        line_width=0,
                        annotation_text=f"{gap['duration_days']} days",
                        annotation_position="top",
                    )

                fig3.update_layout(
                    title="Event Timeline with Festival Opportunity Gaps",
                    xaxis_title="Date",
                    yaxis_title="",
                    yaxis=dict(showticklabels=False, range=[0.5, 1.5]),
                    height=300,
                    showlegend=True,
                )
                plots["gap_timeline"] = fig3
            except Exception as e:
                print(f"Could not create gap timeline: {str(e)}")

        return plots

    def generate_festival_report(self) -> str:
        """
        Generate a comprehensive report for festival organizers
        """
        try:
            opportunities = self.identify_festival_opportunities()
        except Exception as e:
            return f"Error generating report: {str(e)}"

        report = []
        report.append("=" * 60)
        report.append("🎪 MID-SIZED FESTIVAL OPPORTUNITY REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        # 1. Executive Summary
        report.append("📋 EXECUTIVE SUMMARY")
        report.append("-" * 40)
        region_opp = opportunities.get("region_opportunities", pd.DataFrame())
        if not region_opp.empty:
            top_regions = region_opp.head(3)
            report.append(f"Top opportunity regions identified:")
            for _, region in top_regions.iterrows():
                report.append(
                    f"  • {region['region']}: {region['opportunity_rating']} potential "
                    f"(Score: {region['opportunity_score']:.0f}/100)"
                )
        else:
            report.append("No opportunity regions identified.")
        report.append("")

        # 2. Region Analysis
        report.append("📍 REGION OPPORTUNITY ANALYSIS")
        report.append("-" * 40)
        if not region_opp.empty:
            for _, region in region_opp.head(5).iterrows():
                report.append(f"\n{region['region']}:")
                report.append(f"  • Events: {region['event_count']}")
                report.append(f"  • Population: {region['population']:,}")
                report.append(f"  • Events per 100k: {region['events_per_100k']:.1f}")
                report.append(
                    f"  • Opportunity Score: {region['opportunity_score']:.0f}/100"
                )
                report.append(f"  • Rating: {region['opportunity_rating']}")
        else:
            report.append("No region data available.")

        # 3. Calendar Gaps
        report.append("\n📅 CALENDAR OPPORTUNITIES")
        report.append("-" * 40)
        calendar = opportunities.get("calendar_gaps", {})
        if calendar.get("best_gap_for_festival"):
            gap = calendar["best_gap_for_festival"]
            report.append(f"\nIdeal Festival Window:")
            report.append(
                f"  • Dates: {gap['start'].strftime('%Y-%m-%d')} to {gap['end'].strftime('%Y-%m-%d')}"
            )
            report.append(f"  • Duration: {gap['duration_days']} days")
            report.append(f"  • Season: {gap['season']}")
            report.append(f"  • Month: {gap['month']}")
        else:
            report.append("No calendar gaps identified.")

        # 4. Genre Recommendations
        report.append("\n🎵 GENRE OPPORTUNITIES")
        report.append("-" * 40)
        genre_data = opportunities.get("genre_opportunities", {})
        if genre_data:
            for region, data in genre_data.items():
                if data and data.get("underserved_genres"):
                    report.append(f"\n{region}:")
                    for g in data["underserved_genres"][:3]:
                        report.append(
                            f"  • {g['genre']}: Only {g['count']} events ({g['percentage']:.1f}% of events)"
                        )
        else:
            report.append("No genre data available.")

        # 5. Top Recommendations
        report.append("\n⭐ TOP RECOMMENDATIONS")
        report.append("-" * 40)
        recs = opportunities.get("recommendations", [])
        if recs:
            for rec in recs[:5]:
                report.append(f"\n{rec['priority']}. {rec['title']}")
                report.append(
                    f"   Rating: {rec['rating']} (Score: {rec['score']:.0f}/100)"
                )
                report.append(f"   {rec['description'].strip()}")
        else:
            report.append("No recommendations available.")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
