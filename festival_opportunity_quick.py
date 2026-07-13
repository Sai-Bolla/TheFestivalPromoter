# festival_opportunity_quick.py
import pandas as pd
from festival_opportunity import FestivalOpportunityAnalyzer

# Load data
df = pd.read_csv("data/processed/events_cleaned_latest.csv")
regions_df = pd.read_csv("UK_regions.csv")

# Analyze
analyzer = FestivalOpportunityAnalyzer(df, regions_df)
report = analyzer.generate_festival_report()

# Print report
print(report)

# Save report
with open("festival_opportunity_report.txt", "w") as f:
    f.write(report)