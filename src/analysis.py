"""
analysis.py - Virtual triangulation matching algorithm
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from tqdm import tqdm
import yaml


def load_config():
    """Load configuration"""
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points on Earth
    
    Args:
        lat1, lon1: First point (decimal degrees)
        lat2, lon2: Second point (decimal degrees)
        
    Returns:
        Distance in meters
    """
    R = 6371000
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    lon1_rad = np.radians(lon1)
    lon2_rad = np.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c
    return distance


def find_matches(volunteer_df, professional_df, config):
    """
    Find volunteer-professional measurement pairs using spatial-temporal matching
    
    Args:
        volunteer_df: Volunteer measurements
        professional_df: Professional measurements
        config: Configuration dictionary
        
    Returns:
        DataFrame with matched pairs
    """
    max_distance_m = config['matching_parameters']['max_distance_meters']
    max_time_hours = config['matching_parameters']['max_time_hours']
    match_strategy = config['matching_parameters']['match_strategy']
    
    matches = []
    
    print(f"\n=== Virtual Triangulation Matching ===")
    print(f"  Volunteer measurements: {len(volunteer_df):,}")
    print(f"  Professional measurements: {len(professional_df):,}")
    print(f"  Max distance: {max_distance_m}m")
    print(f"  Max time: {max_time_hours}hrs")
    print(f"  Strategy: {match_strategy}")
    print(f"\nProcessing...")
    
    pro_lats = professional_df['LatitudeMeasure'].values
    pro_lons = professional_df['LongitudeMeasure'].values
    pro_dates = pd.to_datetime(professional_df['ActivityStartDate']).values
    pro_values = professional_df['ResultMeasureValue'].values
    pro_site_ids = professional_df['MonitoringLocationIdentifier'].values
    pro_orgs = professional_df['OrganizationIdentifier'].values
    
    pro_units = np.full(len(professional_df), np.nan, dtype=object)
    if 'ResultMeasure/MeasureUnitCode' in professional_df.columns:
        pro_units = professional_df['ResultMeasure/MeasureUnitCode'].values
    
    for idx, vol_row in tqdm(volunteer_df.iterrows(), total=len(volunteer_df), desc="Matching"):
        vol_lat = vol_row['LatitudeMeasure']
        vol_lon = vol_row['LongitudeMeasure']
        vol_datetime = pd.to_datetime(vol_row['ActivityStartDate'])
        vol_value = vol_row['ResultMeasureValue']
        vol_site_id = vol_row['MonitoringLocationIdentifier']
        vol_org = vol_row['OrganizationIdentifier']
        
        vol_units = np.nan
        if 'ResultMeasure/MeasureUnitCode' in volunteer_df.columns:
            vol_units = vol_row['ResultMeasure/MeasureUnitCode']
        
        distances = haversine_distance(vol_lat, vol_lon, pro_lats, pro_lons)
        
        time_diffs = np.abs((pro_dates - np.datetime64(vol_datetime)) / np.timedelta64(1, 'h'))
        
        mask = (distances <= max_distance_m) & (time_diffs <= max_time_hours)
        
        if not mask.any():
            continue
        
        candidate_indices = np.where(mask)[0]
        candidate_distances = distances[mask]
        candidate_time_diffs = time_diffs[mask]
        
        if match_strategy == 'all':
            for i, cand_idx in enumerate(candidate_indices):
                matches.append({
                    'Vol_SiteID': vol_site_id,
                    'Pro_SiteID': pro_site_ids[cand_idx],
                    'Vol_Organization': vol_org,
                    'Pro_Organization': pro_orgs[cand_idx],
                    'Vol_Value': vol_value,
                    'Pro_Value': pro_values[cand_idx],
                    'Vol_Units': vol_units,
                    'Pro_Units': pro_units[cand_idx],
                    'Vol_DateTime': vol_datetime,
                    'Pro_DateTime': pd.Timestamp(pro_dates[cand_idx]),
                    'Vol_Lat': vol_lat,
                    'Vol_Lon': vol_lon,
                    'Pro_Lat': pro_lats[cand_idx],
                    'Pro_Lon': pro_lons[cand_idx],
                    'Distance_m': candidate_distances[i],
                    'Time_Diff_hours': candidate_time_diffs[i]
                })
        else:
            best_idx = candidate_indices[np.argmin(candidate_distances)]
            best_distance = distances[best_idx]
            best_time_diff = time_diffs[best_idx]
            
            matches.append({
                'Vol_SiteID': vol_site_id,
                'Pro_SiteID': pro_site_ids[best_idx],
                'Vol_Organization': vol_org,
                'Pro_Organization': pro_orgs[best_idx],
                'Vol_Value': vol_value,
                'Pro_Value': pro_values[best_idx],
                'Vol_Units': vol_units,
                'Pro_Units': pro_units[best_idx],
                'Vol_DateTime': vol_datetime,
                'Pro_DateTime': pd.Timestamp(pro_dates[best_idx]),
                'Vol_Lat': vol_lat,
                'Vol_Lon': vol_lon,
                'Pro_Lat': pro_lats[best_idx],
                'Pro_Lon': pro_lons[best_idx],
                'Distance_m': best_distance,
                'Time_Diff_hours': best_time_diff
            })
    
    return pd.DataFrame(matches)


def calculate_statistics(matches_df):
    """
    Calculate correlation and regression statistics
    
    Args:
        matches_df: DataFrame with matched pairs
        
    Returns:
        Dictionary with statistics
    """
    vol_values = matches_df['Vol_Value'].values
    pro_values = matches_df['Pro_Value'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(pro_values, vol_values)
    
    r_squared = r_value ** 2
    
    return {
        'n': len(matches_df),
        'r_squared': r_squared,
        'slope': slope,
        'intercept': intercept,
        'p_value': p_value,
        'std_err': std_err
    }


def save_results(matches_df, statistics, config):
    """
    Save matched pairs and statistics
    
    Args:
        matches_df: DataFrame with matched pairs
        statistics: Dictionary with statistics
        config: Configuration dictionary
    """
    output_dir = Path(config['output_paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    matches_path = output_dir / 'matched_pairs.csv'
    matches_df.to_csv(matches_path, index=False)
    
    stats_path = output_dir / 'summary_statistics.txt'
    with open(stats_path, 'w') as f:
        f.write("Blue Thumb Virtual Triangulation - Summary Statistics\n")
        f.write("=" * 55 + "\n\n")
        f.write(f"Sample Size (N):     {statistics['n']}\n")
        f.write(f"R-squared:           {statistics['r_squared']:.6f}\n")
        f.write(f"Slope:               {statistics['slope']:.6f}\n")
        f.write(f"Intercept:           {statistics['intercept']:.6f}\n")
        f.write(f"P-value:             {statistics['p_value']:.2e}\n")
        f.write(f"Standard Error:      {statistics['std_err']:.6f}\n")
    
    print(f"\nSaved results:")
    print(f"  {matches_path}")
    print(f"  {stats_path}")


def main():
    """Run virtual triangulation analysis"""
    
    config = load_config()
    
    print("=== Virtual Triangulation Analysis ===\n")
    
    processed_dir = Path(config['output_paths']['processed_data'])
    
    volunteer_df = pd.read_csv(processed_dir / 'volunteer_chloride.csv', low_memory=False)
    professional_df = pd.read_csv(processed_dir / 'professional_chloride.csv', low_memory=False)
    
    volunteer_df['ActivityStartDate'] = pd.to_datetime(volunteer_df['ActivityStartDate'])
    professional_df['ActivityStartDate'] = pd.to_datetime(professional_df['ActivityStartDate'])
    
    print(f"Loaded volunteer data: {len(volunteer_df):,} records")
    print(f"Loaded professional data: {len(professional_df):,} records")
    
    matches_df = find_matches(volunteer_df, professional_df, config)
    
    print(f"\n=== Results ===")
    print(f"  Matched pairs found: {len(matches_df)}")
    
    if len(matches_df) > 0:
        statistics = calculate_statistics(matches_df)
        
        print(f"\n=== Statistics ===")
        print(f"  N:         {statistics['n']}")
        print(f"  R²:        {statistics['r_squared']:.6f}")
        print(f"  Slope:     {statistics['slope']:.6f}")
        print(f"  Intercept: {statistics['intercept']:.6f}")
        print(f"  P-value:   {statistics['p_value']:.2e}")
        
        save_results(matches_df, statistics, config)
        
        print(f"\n=== Column Names Verification ===")
        expected_cols = ['Vol_SiteID', 'Pro_SiteID', 'Vol_Organization', 'Pro_Organization',
                         'Vol_Value', 'Pro_Value', 'Vol_Units', 'Pro_Units',
                         'Vol_DateTime', 'Pro_DateTime', 'Vol_Lat', 'Vol_Lon',
                         'Pro_Lat', 'Pro_Lon', 'Distance_m', 'Time_Diff_hours']
        actual_cols = list(matches_df.columns)
        if actual_cols == expected_cols:
            print("  ✅ Column names match specification exactly")
        else:
            print("  ❌ Column name mismatch!")
            print(f"  Expected: {expected_cols}")
            print(f"  Actual:   {actual_cols}")
    else:
        print("  No matches found!")
    
    print("\n✅ Virtual triangulation analysis complete")


if __name__ == "__main__":
    main()
