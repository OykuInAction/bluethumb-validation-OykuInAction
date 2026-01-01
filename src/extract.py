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


def download_oklahoma_chloride(config):
    """
    Download Oklahoma chloride data from EPA Water Quality Portal
    
    EPA API Documentation: https://www.waterqualitydata.us/webservices_documentation/
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Path to downloaded CSV file
    """
    
    base_url = "https://www.waterqualitydata.us/data/Result/search"
    
    start_date = config['data_sources']['date_range']['start']
    end_date = config['data_sources']['date_range']['end']
    start_parts = start_date.split('-')
    end_parts = end_date.split('-')
    start_formatted = f"{start_parts[1]}-{start_parts[2]}-{start_parts[0]}"
    end_formatted = f"{end_parts[1]}-{end_parts[2]}-{end_parts[0]}"
    
    params = {
        'statecode': config['data_sources']['state_code'],
        'characteristicName': config['data_sources']['characteristic'],
        'siteType': config['data_sources']['site_type'],
        'sampleMedia': config['data_sources']['sample_media'],
        'startDateLo': start_formatted,
        'startDateHi': end_formatted,
        'mimeType': 'csv',
        'zip': 'yes',
        'dataProfile': 'resultPhysChem'
    }
    
    output_dir = Path(config['output_paths']['raw_data'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {config['data_sources']['characteristic']} data from EPA...")
    print(f"  State: {config['data_sources']['state']}")
    print(f"  Site Type: {config['data_sources']['site_type']}")
    print(f"  Sample Media: {config['data_sources']['sample_media']}")
    print(f"  Date Range: {config['data_sources']['date_range']['start']} to {config['data_sources']['date_range']['end']}")
    print(f"  This may take 5-10 minutes...")
    
    response = requests.get(base_url, params=params, stream=True)
    response.raise_for_status()
    
    zip_path = output_dir / "oklahoma_data.zip"
    
    total_size = int(response.headers.get('content-length', 0))
    with open(zip_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"Extracting CSV from zip...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_files = [name for name in zf.namelist() if 'result' in name.lower() and name.endswith('.csv')]
        if not csv_files:
            raise ValueError("No result CSV file found in downloaded zip")
        
        csv_name = csv_files[0]
        print(f"  Found: {csv_name}")
        
        zf.extract(csv_name, output_dir)
        
        extracted_path = output_dir / csv_name
        final_path = output_dir / "oklahoma_chloride.csv"
        
        if extracted_path != final_path:
            extracted_path.rename(final_path)
    
    zip_path.unlink()
    
    print(f"\nVerifying downloaded data...")
    df = pd.read_csv(final_path, low_memory=False)
    file_size_mb = final_path.stat().st_size / (1024 * 1024)
    
    print(f"  File: {final_path}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Records: {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    
    return final_path


def main():
    """Main execution"""
    config = load_config()
    filepath = download_oklahoma_chloride(config)
    print("\n✅ Data extraction complete")


if __name__ == "__main__":
    main()
