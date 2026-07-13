
import pandas as pd
import ast

# Load the CSV file
skiddle = pd.read_csv('skiddle2.csv')

# Grouping columns by logic helps understand why they are being removed
index_based_drops = skiddle.columns[:7].tolist()

cancellation_cols = [
    'cancellationDate', 'cancellationType', 'cancellationReason'
]
media_cols = [
    'imageurl', 'largeimageurl', 'xlargeimageurl', 'xlargeimageurlWebP'
]
metadata_cols = [
    'link', 'openingtimes', 'minage', 'imgoing', 'goingtos', 'goingtocount',
    'tickets', 'ticketpricing', 'entryprice', 'eventvisibility', 'ticketUrl',
    'hotSeller', 'rep', 'headerHex', 'currency', 'artists', 'genres',
    'healthAndSafety', 'festivalId'
]

columns_to_remove = index_based_drops + cancellation_cols + media_cols + metadata_cols

# Perform the drop
skiddle.drop(columns=columns_to_remove, inplace=True, errors='ignore')

#extract the relevant data from venue into its own columns
def extract_venue_fields(row_data):
    # This remains in-line as a lambda or simple comprehension for readability
    data = ast.literal_eval(row_data) if isinstance(row_data, str) else {}
    return pd.Series({
        'venue_name': data.get('name'),
        'postcode':   data.get('postcode'),
        'longitude':  data.get('longitude'),
        'latitude':   data.get('latitude')
    })

venue_details = skiddle['venue'].apply(extract_venue_fields)

# Add the new columns to the main dataframe
skiddle = pd.concat([skiddle, venue_details], axis=1)

# Remove the original 'venue' column as it is no longer needed
skiddle.drop(columns=['venue'], inplace=True)

#convert the date columns to datetime
skiddle['date'] = pd.to_datetime(skiddle['date'])
skiddle['rescheduledDate'] = pd.to_datetime(skiddle['rescheduledDate'])

#drop rows where cancelled = 1 and there is no data in the rescheduledDate
skiddle.drop(skiddle[(skiddle['cancelled'] == 1) & (skiddle['rescheduledDate'].isna())].index, inplace=True)
skiddle.drop(columns=['cancelled'], inplace=True)

skiddle['startdate'] = pd.to_datetime(skiddle['startdate'])
skiddle['enddate'] = pd.to_datetime(skiddle['enddate'])

#replace the date with the rescheduled date, if there is a rescheduled date
skiddle['date'] = skiddle['rescheduledDate'].fillna(skiddle['date'])
skiddle.drop(columns=['rescheduledDate'], inplace=True) 


#drop the description column, longitude and latitude columns and the festival column
skiddle.drop(columns=['description', 'festival','longitude','latitude'], inplace=True)

#save to csv
skiddle.to_csv('cleaned_skiddle_data14.csv', index=False)


print(skiddle.columns.tolist())
print(skiddle.head())
print(skiddle.info())
print(skiddle.dtypes)

