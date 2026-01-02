# Replication Guide

This document provides step-by-step instructions to reproduce the Blue Thumb Virtual Triangulation validation results.

## Prerequisites

- **Python:** 3.10 or higher
- **Internet connection:** Required for EPA data download
- **Disk space:** ~100 MB for data files
- **Time:** ~15-20 minutes total

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/bluethumb-validation.git
cd bluethumb-validation
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0
- pyyaml >= 6.0
- requests >= 2.31.0
- tqdm >= 4.66.0
- pytest >= 7.4.0

## Running the Pipeline

### Step 1: Data Extraction (~5-10 minutes)

```bash
python src/extract.py
```

**What it does:**
- Downloads chloride measurement data from EPA Water Quality Portal
- Downloads station location data for coordinates
- Merges result and station data

**Expected output:**
- `data/raw/oklahoma_chloride.csv` (~24 MB, ~50,000 records)

**Troubleshooting:**
- If download fails, check internet connection
- EPA servers may be temporarily unavailable; retry after a few minutes
- If you get a 500 error, the EPA server is overloaded; wait and retry

### Step 2: Data Transformation (~1 minute)

```bash
python src/transform.py
```

**What it does:**
- Filters for chloride measurements only
- Removes invalid coordinates and concentrations
- Parses dates to datetime format
- Separates volunteer and professional data
- Applies >25 mg/L filter to professional data

**Expected output:**
- `data/processed/volunteer_chloride.csv` (~15,600 records)
- `data/processed/professional_chloride.csv` (~19,800 records)

### Step 3: Spatial-Temporal Matching (~2-5 minutes)

```bash
python src/analysis.py
```

**What it does:**
- Implements virtual triangulation algorithm
- Calculates Haversine distance between all measurement pairs
- Identifies pairs within 100m and 48 hours
- Calculates linear regression statistics

**Expected output:**
- `data/outputs/matched_pairs.csv` (48 records)
- `data/outputs/summary_statistics.txt`

**Expected statistics:**
- N = 48
- R² = 0.839 (±0.001)
- Slope = 0.712 (±0.001)

### Step 4: Visualization (~30 seconds)

```bash
python src/visualize.py
```

**What it does:**
- Creates publication-quality scatter plot
- Adds regression line and 1:1 reference line
- Includes statistics text box

**Expected output:**
- `data/outputs/validation_plot.png` (300 DPI)

## Verification

Run the test suite to verify all results:

```bash
pytest tests/test_pipeline.py -v
```

**All 11 tests should pass:**
- `test_matched_pairs_exist`
- `test_correct_column_names`
- `test_sample_size` (N=48)
- `test_distance_threshold` (≤100m)
- `test_time_threshold` (≤48hrs)
- `test_concentration_filter` (>25 mg/L)
- `test_correlation` (R²=0.839±0.001)
- `test_slope` (slope=0.712±0.001)
- `test_organizations`
- `test_validation_plot_exists`
- `test_summary_statistics_exists`

## Configuration

All parameters are centralized in `config/config.yaml`:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `max_distance_meters` | 100 | Maximum spatial distance for matching |
| `max_time_hours` | 48 | Maximum temporal difference for matching |
| `min_concentration_mg_l` | 25 | Minimum professional concentration |
| `match_strategy` | "all" | Include all qualifying matches |

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError:** Ensure virtual environment is activated and dependencies installed
2. **FileNotFoundError:** Run pipeline steps in order (extract → transform → analysis → visualize)
3. **EPA download fails:** Check internet connection; EPA servers may be temporarily unavailable
4. **Different record counts:** EPA data updates periodically; slight variations are expected

### Verifying Haversine Implementation

```python
from src.analysis import haversine_distance

# Oklahoma City to Tulsa should be ~160 km
okc = (35.4676, -97.5164)
tulsa = (36.1540, -95.9928)
distance = haversine_distance(okc[0], okc[1], tulsa[0], tulsa[1])
print(f"Distance: {distance/1000:.1f} km")  # Should print ~160 km
```

## Contact

For questions about this implementation, please open an issue on GitHub.
