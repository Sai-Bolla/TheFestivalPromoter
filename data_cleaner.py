import pandas as pd
import numpy as np
from typing import List, Tuple
import re
from fuzzywuzzy import fuzz, process

class AdvancedDataCleaner:
    """Advanced data cleaning"""
    
    def __init__(self):
        pass
    
    def clean_venue_names(self, df: pd.DataFrame, threshold: int = 85) -> pd.DataFrame:
        """Clean venue names"""
        
        if df.empty:
            return df        
    
        # Get unique venue names
        venues = df['venue_name'].unique()
        
        # Group similar venue names
        venue_groups = {}
        processed = set()
        
        for venue in venues:
            if venue in processed:
                continue
            
            # Similar venues
            similar = []
            for other in venues:
                if other in processed:
                    continue
                if fuzz.ratio(str(venue).lower(), str(other).lower()) > threshold:
                    similar.append(other)
                    processed.add(other)
            
            # Common name as standard
            if similar:
                # Frequently
                name_counts = df[df['venue_name'].isin(similar)]['venue_name'].value_counts()
                standard_name = name_counts.index[0]
                
                for s in similar:
                    venue_groups[s] = standard_name
                    
        # Standarise
        df['venue_name_cleaned'] = df['venue_name'].map(venue_groups).fillna(df['venue_name'])
        return df
    
    def extract_event_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and standardise event"""
        if df.empty:
            return df
        
        # Genre mapping
        genre_mapping = {
            'rock': 'Rock',
            'pop': 'Pop',
            'electronic': 'Electronic',
            'hip hop': 'Hip Hop',
            'jazz': 'Jazz',
            'classical': 'Classical',
            'folk': 'Folk',
            'metal': 'Metal',
            'reggae': 'Reggae'
        }
        
        def categorise_genre(genre_str):
            if pd.isna(genre_str) or genre_str == 'N/A':
                return 'Uncategorised'
            
            genre_lower = str(genre_str).lower()
            for key, value in genre_mapping.items():
                if key in genre_lower:
                    return value
                
            # Take the first one
            genres = [g.strip() for g in genre_str.split(',')]
            return genres[0] if genres else 'Uncategorised'
        
        df['event_category'] = df['genre'].apply(categorise_genre)
        return df
    
    def add_event_quality_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a score"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0
            
            # Has name
            if row['event_name'] and row['event_name'] != 'Unknown Event':
                score += 2
            
            # Valid coordinates
            if row['latitude'] != 0 and row['longitude'] != 0:
                score += 3
                
            # Has date
            if row['date'] and row['date'] != 'Date TBC':
                score += 2
                
            # Has genre
            if row['genre'] and row['genre'] != 'N/A': 
                score += 1
            
            # Has price
            if row['price'] and row['price'] != 'TBC':
                score += 1
                
            # Has URL
            if row['url'] and row['url'] != '#':
                score += 1
            
            scores.append(score)
            
        df['quality_score'] = scores
        return df
    
    def validate_event_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Check valid and invalid data"""
        if df.empty:
            return df, df
        
        # Validation rules
        is_valid = (
            (df['event_name'].notna()) &
            (df['venue_name'].notna()) &
            (df['latitude'].between(-90, 90)) &
            (df['longitude'].between(-180, 180)) &
            (df['quality_score'] >= 5)  # Minimum quality score
        )
        
        valid_df = df[is_valid].copy()
        invalid_df = df[~is_valid].copy()
        
        print(f"Valid events: {len(valid_df)}")
        print(f"Invalid events: {len(invalid_df)}")
        
        return valid_df, invalid_df
    
    def deduplicate_with_confidence(self, df: pd.DataFrame, threshold: int = 90) -> pd.DataFrame:
        """Advanced deduplciation"""
        if len(df) < 2:
            return df
        
        df_clean = df.copy()
        duplicates = []
        
        # compare events
        for i in range(len(df_clean)):
            if i in duplicates:
                continue
            
            row_i = df_clean.iloc[i]
            
            for j in range(i + 1, len(df_clean)):
                if j in duplicates:
                    continue
                
                row_j = df_clean.iloc[j]
                
                # Calculate similarity
                name_sim = fuzz.ratio(str(row_i['event_name']).lower(), str(row_j['event_name']).lower())
                
                venue_sim = fuzz.ratio(str(row_i['venue_name']).lower(), str(row_j['venue_name']).lower())
                
                # Similar names and venues
                if name_sim > threshold and venue_sim > threshold:
                    if row_i['quality_score'] >= row_j['quality_score']:
                        duplicates.append(j)
                    else:
                        duplicates.append(i)
                        break
        # remove duplicates
        df_clean = df_clean.drop(index=duplicates)
        
        print(f"Removed {len(duplicates)} duplicate events (threshold={threshold}%)")
        return df_clean
    
if __name__ == "__main__":
    # Load data
    df = pd.read_csv("data/processed/events_cleaned_latest.csv")
    
    # Initialise cleaner
    cleaner = AdvancedDataCleaner()
    
    # Cleaning
    df = cleaner.clean_venue_names(df)
    df = cleaner.extract_event_categories(df)
    df = cleaner.add_event_quality_score(df)
    df = cleaner.deduplicate_with_confidence(df)
    
    # Validate
    valid, invalid = cleaner.validate_event_data(df)
    
    # Save results
    valid.to_csv("data/processed/events_valid.csv", index=False)
    invalid.to_csv("data/processed/events_invalid.csv", index=False)