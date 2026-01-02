"""
transform.py - Clean and filter EPA data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml


def load_config():
    """Load configuration"""
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)


def load_raw_data(config):
    """
    Load raw EPA data
    
    Args:
        config: Configuration dictionary
        
    Returns:
        DataFrame with raw data
    """
    filepath = Path(config['output_paths']['raw_data']) / 'oklahoma_chloride.csv'
    df = pd.read_csv(filepath, low_memory=False)
    print(f"Loaded raw data: {len(df):,} records")
    return df


def filter_chloride(df):
    """
    Filter for chloride measurements only
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame with only Chloride measurements
    """
    df_filtered = df[df['CharacteristicName'] == 'Chloride'].copy()
    print(f"After chloride filter: {len(df_filtered):,} records")
    return df_filtered


def clean_coordinates(df, config):
    """
    Remove invalid coordinates
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        DataFrame with valid coordinates only
    """
    df_clean = df[
        df['LatitudeMeasure'].notna() & 
        df['LongitudeMeasure'].notna()
    ].copy()
    print(f"After coordinate cleaning: {len(df_clean):,} records")
    return df_clean


def clean_concentrations(df):
    """
    Filter for valid concentration values
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with valid concentrations
    """
    initial_count = len(df)
    
    df_clean = df[df['ResultMeasureValue'].notna()].copy()
    after_null = len(df_clean)
    
    if 'ResultDetectionConditionText' in df_clean.columns:
        df_clean = df_clean[df_clean['ResultDetectionConditionText'].isna()].copy()
    after_detection = len(df_clean)
    
    df_clean['ResultMeasureValue'] = pd.to_numeric(df_clean['ResultMeasureValue'], errors='coerce')
    df_clean = df_clean[df_clean['ResultMeasureValue'].notna()].copy()
    df_clean = df_clean[df_clean['ResultMeasureValue'] >= 0].copy()
    
    print(f"After concentration cleaning: {len(df_clean):,} records")
    print(f"  (removed {initial_count - len(df_clean):,} invalid values)")
    return df_clean


def parse_dates(df):
    """
    Convert dates to datetime objects
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with parsed dates
    """
    df_parsed = df.copy()
    df_parsed['ActivityStartDate'] = pd.to_datetime(df_parsed['ActivityStartDate'], errors='coerce')
    df_parsed = df_parsed[df_parsed['ActivityStartDate'].notna()].copy()
    print(f"After date parsing: {len(df_parsed):,} records")
    return df_parsed


def separate_volunteer_professional(df, config):
    """
    Separate volunteer and professional measurements
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        
    Returns:
        Tuple of (volunteer_df, professional_df)
    """
    volunteer_orgs = config['organizations']['volunteer']
    professional_orgs = config['organizations']['professional']
    min_concentration = config['matching_parameters']['min_concentration_mg_l']
    
    volunteer_df = df[df['OrganizationIdentifier'].isin(volunteer_orgs)].copy()
    
    professional_df = df[df['OrganizationIdentifier'].isin(professional_orgs)].copy()
    professional_df = professional_df[professional_df['ResultMeasureValue'] > min_concentration].copy()
    
    print(f"\nSeparated by organization:")
    print(f"  Volunteer records: {len(volunteer_df):,}")
    print(f"  Professional records: {len(professional_df):,} (after >{min_concentration} mg/L filter)")
    
    print(f"\nVolunteer organizations found:")
    for org in volunteer_df['OrganizationIdentifier'].unique():
        count = len(volunteer_df[volunteer_df['OrganizationIdentifier'] == org])
        print(f"    {org}: {count:,}")
    
    print(f"\nProfessional organizations found:")
    for org in professional_df['OrganizationIdentifier'].unique():
        count = len(professional_df[professional_df['OrganizationIdentifier'] == org])
        print(f"    {org}: {count:,}")
    
    return volunteer_df, professional_df


def save_processed_data(volunteer_df, professional_df, config):
    """
    Save processed datasets
    
    Args:
        volunteer_df: Volunteer measurements DataFrame
        professional_df: Professional measurements DataFrame
        config: Configuration dictionary
    """
    output_dir = Path(config['output_paths']['processed_data'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    volunteer_path = output_dir / 'volunteer_chloride.csv'
    professional_path = output_dir / 'professional_chloride.csv'
    
    volunteer_df.to_csv(volunteer_path, index=False)
    professional_df.to_csv(professional_path, index=False)
    
    print(f"\nSaved processed data:")
    print(f"  {volunteer_path}: {len(volunteer_df):,} records")
    print(f"  {professional_path}: {len(professional_df):,} records")


def main():
    """Main data cleaning pipeline"""
    config = load_config()
    
    print("=== Data Transformation Pipeline ===\n")
    
    df = load_raw_data(config)
    df = filter_chloride(df)
    df = clean_coordinates(df, config)
    df = clean_concentrations(df)
    df = parse_dates(df)
    
    volunteer_df, professional_df = separate_volunteer_professional(df, config)
    
    save_processed_data(volunteer_df, professional_df, config)
    
    print("\n✅ Data transformation complete")


if __name__ == "__main__":
    main()
