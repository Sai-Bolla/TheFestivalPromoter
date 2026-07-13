import pandas as pd
from datetime import datetime
import ast


# 1. Load the datasets
skiddle_df = pd.read_csv('cleaned_skiddle_data10.csv')
ticketmaster_df = pd.read_csv('cleaned_ticketmaster_data3.csv')

# 2. Standardize column names for easier merging
skiddle_df = skiddle_df.rename(columns={'eventname': 'event_name', 'postcode': 'venue_postcode'})
ticketmaster_df = ticketmaster_df.rename(columns={'postalCode': 'venue_postcode'})

# 3. Combine the dataframes
combined_df = pd.concat([skiddle_df, ticketmaster_df], ignore_index=True)

# 4. Consolidate start and end times
# This uses the 'start_datetime' if available, otherwise falls back to 'startdate'
combined_df['start'] = combined_df['start_datetime'].fillna(combined_df['startdate'])
combined_df['end'] = combined_df['end_datetime'].fillna(combined_df['enddate'])

# 5. Clean up: Drop the original, redundant columns
final_df = combined_df.drop(columns=['startdate', 'enddate', 'start_datetime', 'end_datetime'])

# 6. Remove duplicates
# We drop duplicates based on the event name, venue, and the newly created 'start' time
final_df = final_df.drop_duplicates(subset=['event_name', 'venue_name', 'start'])
final_df = final_df.drop_duplicates(subset=['start', 'end', 'venue_postcode'])
final_df = final_df.drop_duplicates(subset=['event_name', 'venue_postcode'])

# 7. Save to a new file
final_df.to_csv('final_merged_events5.csv', index=False)

print(f"Merge successful! Total unique entries: {len(final_df)}")
print(final_df.head())