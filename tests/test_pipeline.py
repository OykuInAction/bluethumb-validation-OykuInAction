"""
test_pipeline.py - Verify pipeline results

Run with: pytest tests/test_pipeline.py -v
"""

import pandas as pd
import pytest
from pathlib import Path
from scipy import stats


def test_matched_pairs_exist():
    """Verify matched pairs file was created"""
    path = Path("data/outputs/matched_pairs.csv")
    assert path.exists(), "matched_pairs.csv not found"


def test_correct_column_names():
    """Verify exact column names match specification"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    
    expected_columns = [
        'Vol_SiteID', 'Pro_SiteID',
        'Vol_Organization', 'Pro_Organization',
        'Vol_Value', 'Pro_Value',
        'Vol_Units', 'Pro_Units',
        'Vol_DateTime', 'Pro_DateTime',
        'Vol_Lat', 'Vol_Lon', 'Pro_Lat', 'Pro_Lon',
        'Distance_m', 'Time_Diff_hours'
    ]
    
    assert list(df.columns) == expected_columns, f"Column mismatch. Expected: {expected_columns}, Got: {list(df.columns)}"


def test_sample_size():
    """Verify we got exactly 48 matches"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    assert len(df) == 48, f"Expected 48 matches, got {len(df)}"


def test_distance_threshold():
    """Verify all distances <= 100m"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    max_distance = df['Distance_m'].max()
    assert max_distance <= 100, f"Max distance {max_distance}m exceeds 100m threshold"


def test_time_threshold():
    """Verify all time differences <= 48 hours"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    max_time = df['Time_Diff_hours'].max()
    assert max_time <= 48, f"Max time difference {max_time}hrs exceeds 48hr threshold"


def test_concentration_filter():
    """Verify professional concentrations > 25 mg/L"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    min_pro_value = df['Pro_Value'].min()
    assert min_pro_value > 25, f"Min professional value {min_pro_value} mg/L is not > 25 mg/L"


def test_correlation():
    """Verify R² = 0.839 ± 0.001"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    
    pro_values = df['Pro_Value'].values
    vol_values = df['Vol_Value'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(pro_values, vol_values)
    r_squared = r_value ** 2
    
    assert abs(r_squared - 0.839) < 0.001, f"R² = {r_squared:.6f}, expected 0.839 ± 0.001"


def test_slope():
    """Verify slope = 0.712 ± 0.001"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    
    pro_values = df['Pro_Value'].values
    vol_values = df['Vol_Value'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(pro_values, vol_values)
    
    assert abs(slope - 0.712) < 0.001, f"Slope = {slope:.6f}, expected 0.712 ± 0.001"


def test_organizations():
    """Verify correct organizations present"""
    df = pd.read_csv("data/outputs/matched_pairs.csv")
    
    volunteer_orgs = set(df['Vol_Organization'].unique())
    professional_orgs = set(df['Pro_Organization'].unique())
    
    expected_volunteer = {'OKCONCOM_WQX', 'CONSERVATION_COMMISSION'}
    assert volunteer_orgs.issubset(expected_volunteer), f"Unexpected volunteer orgs: {volunteer_orgs - expected_volunteer}"
    
    expected_professional_subset = {'OKWRB-STREAMS_WQX', 'O_MTRIBE_WQX'}
    assert len(professional_orgs & expected_professional_subset) > 0, f"Expected at least one of {expected_professional_subset} in professional orgs"


def test_validation_plot_exists():
    """Verify validation plot was created"""
    path = Path("data/outputs/validation_plot.png")
    assert path.exists(), "validation_plot.png not found"


def test_summary_statistics_exists():
    """Verify summary statistics file was created"""
    path = Path("data/outputs/summary_statistics.txt")
    assert path.exists(), "summary_statistics.txt not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
