"""
extract.py - Download data from EPA Water Quality Portal
"""

import requests
import zipfile
import pandas as pd
from pathlib import Path
import yaml
from tqdm import tqdm


def load_config():
    """Load configuration from YAML file"""
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)


def download_data(base_url, params, output_dir, output_filename, description):
    """
    Generic download function for EPA Water Quality Portal data.
    
    Args:
        base_url: API endpoint URL
        params: Query parameters dict
        output_dir: Path to output directory
        output_filename: Name for the final CSV file
        description: Description for progress messages
        
    Returns:
        Path to downloaded CSV file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {description}...")
    
    response = requests.get(base_url, params=params, stream=True)
    response.raise_for_status()
    
    zip_path = output_dir / "temp_data.zip"
    
    total_size = int(response.headers.get('content-length', 0))
    with open(zip_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"Extracting CSV from zip...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_files = [name for name in zf.namelist() if name.endswith('.csv')]
        if not csv_files:
            raise ValueError("No CSV file found in downloaded zip")
        
        csv_name = csv_files[0]
        print(f"  Found: {csv_name}")
        
        zf.extract(csv_name, output_dir)
        
        extracted_path = output_dir / csv_name
        final_path = output_dir / output_filename
        
        if extracted_path != final_path:
            if final_path.exists():
                final_path.unlink()
            extracted_path.rename(final_path)
    
    zip_path.unlink()
    
    df = pd.read_csv(final_path, low_memory=False)
    file_size_mb = final_path.stat().st_size / (1024 * 1024)
    
    print(f"  File: {final_path}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Records: {len(df):,}")
    
    return final_path


def download_oklahoma_chloride(config):
    """
    Download Oklahoma chloride result data and station data from EPA Water Quality Portal,
    then merge them to include coordinates.
    
    EPA API Documentation: https://www.waterqualitydata.us/webservices_documentation/
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Path to downloaded and merged CSV file
    """
    
    start_date = config['data_sources']['date_range']['start']
    end_date = config['data_sources']['date_range']['end']
    start_parts = start_date.split('-')
    end_parts = end_date.split('-')
    start_formatted = f"{start_parts[1]}-{start_parts[2]}-{start_parts[0]}"
    end_formatted = f"{end_parts[1]}-{end_parts[2]}-{end_parts[0]}"
    
    output_dir = config['output_paths']['raw_data']
    
    print(f"=== EPA Water Quality Portal Data Extraction ===")
    print(f"  State: {config['data_sources']['state']}")
    print(f"  Characteristic: {config['data_sources']['characteristic']}")
    print(f"  Site Type: {config['data_sources']['site_type']}")
    print(f"  Sample Media: {config['data_sources']['sample_media']}")
    print(f"  Date Range: {start_date} to {end_date}")
    print()
    
    result_params = {
        'statecode': config['data_sources']['state_code'],
        'characteristicName': config['data_sources']['characteristic'],
        'siteType': config['data_sources']['site_type'],
        'sampleMedia': config['data_sources']['sample_media'],
        'startDateLo': start_formatted,
        'startDateHi': end_formatted,
        'mimeType': 'csv',
        'zip': 'yes'
    }
    
    result_path = download_data(
        base_url="https://www.waterqualitydata.us/data/Result/search",
        params=result_params,
        output_dir=output_dir,
        output_filename="oklahoma_results.csv",
        description="Result data (chloride measurements)"
    )
    
    print()
    
    station_params = {
        'statecode': config['data_sources']['state_code'],
        'characteristicName': config['data_sources']['characteristic'],
        'siteType': config['data_sources']['site_type'],
        'sampleMedia': config['data_sources']['sample_media'],
        'startDateLo': start_formatted,
        'startDateHi': end_formatted,
        'mimeType': 'csv',
        'zip': 'yes'
    }
    
    station_path = download_data(
        base_url="https://www.waterqualitydata.us/data/Station/search",
        params=station_params,
        output_dir=output_dir,
        output_filename="oklahoma_stations.csv",
        description="Station data (site coordinates)"
    )
    
    print("\nMerging result and station data...")
    results_df = pd.read_csv(result_path, low_memory=False)
    stations_df = pd.read_csv(station_path, low_memory=False)
    
    station_cols = ['MonitoringLocationIdentifier', 'LatitudeMeasure', 'LongitudeMeasure',
                    'HorizontalCoordinateReferenceSystemDatumName']
    stations_subset = stations_df[station_cols].drop_duplicates()
    
    merged_df = results_df.merge(stations_subset, on='MonitoringLocationIdentifier', how='left')
    
    final_path = Path(output_dir) / "oklahoma_chloride.csv"
    merged_df.to_csv(final_path, index=False)
    
    file_size_mb = final_path.stat().st_size / (1024 * 1024)
    
    print(f"\n=== Final Merged Dataset ===")
    print(f"  File: {final_path}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Records: {len(merged_df):,}")
    print(f"  Columns: {len(merged_df.columns)}")
    
    coords_present = merged_df['LatitudeMeasure'].notna().sum()
    print(f"  Records with coordinates: {coords_present:,} ({100*coords_present/len(merged_df):.1f}%)")
    
    return final_path


def main():
    """Main execution"""
    config = load_config()
    filepath = download_oklahoma_chloride(config)
    print("\n✅ Data extraction complete")


if __name__ == "__main__":
    main()
