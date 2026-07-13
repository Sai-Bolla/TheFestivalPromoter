from datetime import timedelta
from typing import Dict, Optional, Tuple
import pandas as pd
import plotly.express as px


class EventGapAnalyser:
    """Figure out gaps in events"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

        # Get dates
        if "date" in self.df.columns:
            self.df["date_parsed"] = pd.to_datetime(self.df["date"], errors="coerce")
            self.df = self.df.dropna(subset=["date_parsed"])
            self.df = self.df.sort_values("date_parsed")

        self.event_dates = self.df["date_parsed"].dropna()

    def find_gaps(
        self, gap_threshold_days: int = 3, date_range: Optional[Tuple[str, str]] = None
    ) -> pd.DataFrame:
        """Find gaps"""
        if self.event_dates.empty:
            return pd.DataFrame()

        # Get range
        if date_range:
            start_date = pd.to_datetime(date_range[0])
            end_date = pd.to_datetime(date_range[1])
            dates = self.event_dates[
                (self.event_dates >= start_date) & (self.event_dates <= end_date)
            ]
        else:
            dates = self.event_dates
            start_date = dates.min()
            end_date = dates.max()

        if dates.empty:
            return pd.DataFrame()

        gaps = []
        sorted_dates = dates.sort_values().unique()

        for i in range(len(sorted_dates) - 1):
            gap_days = (sorted_dates[i + 1] - sorted_dates[i]).days

            if gap_days > gap_threshold_days:
                gap_start = sorted_dates[i]
                gap_end = sorted_dates[i + 1]
                gap_midpoint = gap_start + timedelta(days=gap_days // 2)

                # Check for events
                events_before = len(self.df[self.df["date_parsed"] <= gap_start])
                events_after = len(self.df[self.df["date_parsed"] >= gap_end])

                is_start_gap = (
                    i == 0 and (gap_start - start_date).days > gap_threshold_days
                )
                is_end_gap = (
                    i == len(sorted_dates) - 2
                    and (end_date - gap_end).days > gap_threshold_days
                )

                gaps.append(
                    {
                        "gap_start": gap_start,
                        "gap_end": gap_end,
                        "gap_days": gap_days,
                        "gap_midpoint": gap_midpoint,
                        "events_before": events_before,
                        "events_after": events_after,
                        "is_start_gap": is_start_gap,
                        "is_end_gap": is_end_gap,
                        "day_of_week_start": gap_start.strftime("%A"),
                        "day_of_week_end": gap_end.strftime("%A"),
                        "month": gap_start.strftime("%B"),
                        "year": gap_start.year,
                    }
                )
        return pd.DataFrame(gaps)

    def get_gap_summary(self, gap_threshold_days: int = 3) -> Dict:
        """Get summary"""

        if self.event_dates.empty:
            return {}

        gaps_df = self.find_gaps(gap_threshold_days)

        if gaps_df.empty:
            return {
                "total_gaps": 0,
                "total_gap_days": 0,
                "average_gap_days": 0,
                "max_gap_days": 0,
                "min_gap_days": 0,
                "gaps_by_month": {},
                "gaps_by_day": {},
                "largest_gap": None,
                "total_days_analyzed": 0,
                "event_days": len(self.event_dates.unique()),
                "coverage_percentage": 0,
            }

        # Calculate total days in range
        date_range_days = (self.event_dates.max() - self.event_dates.min()).days
        event_days = len(self.event_dates.unique())

        summary = {
            "total_gaps": len(gaps_df),
            "total_gap_days": gaps_df["gap_days"].sum(),
            "average_gap_days": gaps_df["gap_days"].mean(),
            "max_gap_days": gaps_df["gap_days"].max(),
            "min_gap_days": gaps_df["gap_days"].min(),
            "gaps_by_month": gaps_df["month"].value_counts().to_dict(),
            "gaps_by_day": gaps_df["day_of_week_start"].value_counts().to_dict(),
            "largest_gap": (
                gaps_df.loc[gaps_df["gap_days"].idxmax()].to_dict()
                if not gaps_df.empty
                else None
            ),
            "total_days_analyzed": date_range_days,
            "event_days": event_days,
            "coverage_percentage": (
                (event_days / date_range_days) * 100 if date_range_days > 0 else 0
            ),
        }
        return summary

    def analyze_gap_causes(self, gap_df: pd.DataFrame) -> Dict:
        """
        Analyze potential causes for gaps in events

        Returns:
            Dictionary with potential causes (never None)
        """
        # Initialize with default empty structure
        causes = {
            "seasonal_pattern": {"most_gap_prone_month": None, "gaps_by_month": {}},
            "day_pattern": {"most_gap_prone_day": None, "gaps_by_day": {}},
            "holiday_pattern": {"gaps_during_holidays": 0, "percentage_of_gaps": 0},
            "data_boundary_issues": {
                "gaps_at_start": 0,
                "gaps_at_end": 0,
                "suggestion": "",
            },
            "consecutive_gaps": {"count": 0, "suggestion": ""},
        }

        if gap_df.empty:
            causes["message"] = "No gaps found to analyze"
            return causes

        try:
            # Check for seasonal patterns
            monthly_gaps = gap_df["month"].value_counts()
            if not monthly_gaps.empty:
                causes["seasonal_pattern"] = {
                    "most_gap_prone_month": monthly_gaps.index[0],
                    "gaps_by_month": monthly_gaps.to_dict(),
                }

            # Check for day-of-week patterns
            daily_gaps = gap_df["day_of_week_start"].value_counts()
            if not daily_gaps.empty:
                causes["day_pattern"] = {
                    "most_gap_prone_day": daily_gaps.index[0],
                    "gaps_by_day": daily_gaps.to_dict(),
                }

            # Check for holiday patterns (simplified)
            uk_holidays = [
                "2026-12-25",
                "2026-12-28",
                "2026-01-01",
                "2026-04-03",
                "2026-04-04",
                "2026-05-04",
                "2026-05-25",
                "2026-08-31",
            ]

            holiday_gaps = []
            for _, gap in gap_df.iterrows():
                gap_dates = pd.date_range(gap["gap_start"], gap["gap_end"])
                for date in gap_dates:
                    if date.strftime("%Y-%m-%d") in uk_holidays:
                        holiday_gaps.append(gap)
                        break

            causes["holiday_pattern"] = {
                "gaps_during_holidays": len(holiday_gaps),
                "percentage_of_gaps": (
                    (len(holiday_gaps) / len(gap_df)) * 100 if len(gap_df) > 0 else 0
                ),
            }

            # Check data boundary issues
            start_gaps = gap_df[gap_df.get("is_start_gap", False)]
            end_gaps = gap_df[gap_df.get("is_end_gap", False)]

            causes["data_boundary_issues"] = {
                "gaps_at_start": len(start_gaps),
                "gaps_at_end": len(end_gaps),
                "suggestion": "Consider extending your date range if these are significant",
            }

            # Look for consecutive gaps
            if len(gap_df) > 1:
                consecutive_gaps = 0
                for i in range(len(gap_df) - 1):
                    if (
                        gap_df.iloc[i + 1]["gap_start"] - gap_df.iloc[i]["gap_end"]
                    ).days <= 1:
                        consecutive_gaps += 1

                causes["consecutive_gaps"] = {
                    "count": consecutive_gaps,
                    "suggestion": "Multiple consecutive gaps may indicate a broader issue",
                }

        except Exception as e:
            causes["error"] = str(e)

        return causes

    def visualize_gaps(self, gap_df: pd.DataFrame) -> None:
        """Create visualizations of event gaps"""
        if gap_df.empty:
            print("No gaps to visualize")
            return

        # 1. Timeline of events with gaps highlighted
        fig1 = px.scatter(
            self.df,
            x="date_parsed",
            y=[1] * len(self.df),
            title="Event Timeline with Gaps",
            labels={"x": "Date", "y": "Events"},
            color="source" if "source" in self.df.columns else None,
            hover_data=["event_name"] if "event_name" in self.df.columns else None,
        )

        # Add gap rectangles
        for _, gap in gap_df.iterrows():
            fig1.add_vrect(
                x0=gap["gap_start"],
                x1=gap["gap_end"],
                fillcolor="red",
                opacity=0.2,
                layer="below",
                line_width=0,
                annotation_text=f"{gap['gap_days']} days",
                annotation_position="top",
            )

        fig1.update_layout(showlegend=False, height=300)
        fig1.show()

        # 2. Gap duration distribution
        fig2 = px.histogram(
            gap_df,
            x="gap_days",
            title="Distribution of Gap Lengths",
            labels={"gap_days": "Gap Length (days)"},
            nbins=20,
            color_discrete_sequence=["#FF6B6B"],
        )
        fig2.show()

        # 3. Gaps by month
        if not gap_df["month"].empty:
            monthly_gaps = gap_df["month"].value_counts()
            fig3 = px.bar(
                x=monthly_gaps.index,
                y=monthly_gaps.values,
                title="Gaps by Month",
                labels={"x": "Month", "y": "Number of Gaps"},
                color=monthly_gaps.values,
                color_continuous_scale="Reds",
            )
            fig3.show()

    

def analyse_events_gap(df: pd.DataFrame, gap_threshold_days: int = 3) -> Dict:
    """Function to analysis events gap"""

    analyser = EventGapAnalyser(df)

    # Find gaps
    gaps = analyser.find_gaps(gap_threshold_days)

    # Get summary
    summary = analyser.get_gap_summary(gap_threshold_days)

    # Analyse causes
    causes = analyser.analyze_gap_causes(gaps)

    return {"gaps": gaps, "summary": summary, "causes": causes, "analyser": analyser}
