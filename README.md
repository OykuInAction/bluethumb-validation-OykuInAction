# Blue Thumb Virtual Triangulation Validation

> **Project:** Oklahoma Blue Thumb Data Validation Pipeline  
> **Engineering Lead:** Oyku  
> **Architected by:** Miguel Ingram (Black Box Research)

## Overview

This ETL pipeline validates citizen science water quality data collected by Oklahoma's Blue Thumb volunteer program against professional monitoring data from state and federal agencies. Using a spatial-temporal matching algorithm called "virtual triangulation," the pipeline identifies measurement pairs taken at the same location within 100 meters and 48 hours of each other.

## Results

| Metric | Value |
|--------|-------|
| **Matched Pairs (N)** | 48 |
| **R²** | 0.839 |
| **Slope** | 0.712 |
| **p-value** | < 0.0001 |

**Interpretation:** The strong correlation (R² = 0.839) demonstrates that Blue Thumb volunteer measurements are scientifically valid and closely match professional monitoring data. The slope of 0.712 indicates volunteers tend to measure slightly lower concentrations than professionals, which may reflect differences in sampling methodology or equipment.

## Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/bluethumb-validation.git
cd bluethumb-validation

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run pipeline
python src/extract.py      # Download EPA data (~5-10 min)
python src/transform.py    # Clean and filter data
python src/analysis.py     # Run spatial-temporal matching
python src/visualize.py    # Create validation plot

# Verify results
pytest tests/test_pipeline.py -v
```

## Methodology

### Virtual Triangulation

The algorithm matches volunteer and professional measurements based on:

1. **Spatial proximity:** Measurements must be within 100 meters (using Haversine distance)
2. **Temporal proximity:** Measurements must be within 48 hours of each other
3. **Concentration filter:** Professional measurements must exceed 25 mg/L chloride

For each volunteer measurement, the algorithm:
1. Calculates distance to all professional measurements using the Haversine formula
2. Calculates time difference in hours
3. Identifies all pairs meeting both thresholds
4. Records matched pairs with metadata

### Statistical Analysis

Linear regression is performed on matched pairs:
- **X-axis:** Professional chloride concentration (mg/L)
- **Y-axis:** Volunteer chloride concentration (mg/L)
- **R²:** Coefficient of determination (correlation strength)
- **Slope:** Relationship between volunteer and professional values

## Data Sources

- **EPA Water Quality Portal:** https://www.waterqualitydata.us/
- **Volunteer Organizations:** OKCONCOM_WQX, CONSERVATION_COMMISSION (Blue Thumb)
- **Professional Organizations:** OKWRB-STREAMS_WQX, USGS-OK, O_MTRIBE_WQX, and others

## Project Structure

```
bluethumb-validation/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/                  # Downloaded EPA data (gitignored)
│   ├── processed/            # Cleaned datasets (gitignored)
│   └── outputs/              # Results and plots (gitignored)
├── src/
│   ├── __init__.py
│   ├── extract.py            # Download from EPA
│   ├── transform.py          # Clean and filter
│   ├── analysis.py           # Spatial-temporal matching
│   └── visualize.py          # Create plots
├── config/
│   └── config.yaml           # All parameters
├── tests/
│   └── test_pipeline.py      # Verification tests
└── docs/
    └── REPLICATION.md        # How to reproduce
```

## What I Learned

- **API Integration:** Working with EPA's Water Quality Portal REST API
- **Data Cleaning:** Handling null values, type conversions, and filtering large datasets
- **Spatial Algorithms:** Implementing the Haversine formula for great-circle distance
- **Vectorized Operations:** Using NumPy for efficient array operations instead of nested loops
- **Statistical Analysis:** Linear regression with scipy.stats
- **Scientific Visualization:** Creating publication-quality plots with matplotlib
- **Configuration Management:** Centralizing parameters in YAML
- **Testing:** Writing verification tests with pytest

## License

MIT License - See LICENSE file for details.
