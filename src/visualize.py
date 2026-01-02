"""
visualize.py - Create validation visualizations
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import yaml


def load_config():
    """Load configuration"""
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)


def create_validation_plot(matches_df, config):
    """
    Create scatter plot comparing volunteer vs. professional measurements
    
    Args:
        matches_df: DataFrame with matched pairs
        config: Configuration dictionary
    """
    vol_values = matches_df['Vol_Value'].values
    pro_values = matches_df['Pro_Value'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(pro_values, vol_values)
    r_squared = r_value ** 2
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    ax.scatter(pro_values, vol_values, alpha=0.6, color='steelblue', s=100, 
               edgecolors='white', linewidth=0.5, label='Matched Pairs')
    
    x_line = np.linspace(pro_values.min(), pro_values.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (slope={slope:.3f})')
    
    max_val = max(pro_values.max(), vol_values.max()) * 1.1
    min_val = min(pro_values.min(), vol_values.min()) * 0.9
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1.5, 
            alpha=0.7, label='1:1 Reference')
    
    ax.set_xlabel('Professional Chloride (mg/L)', fontsize=12)
    ax.set_ylabel('Volunteer Chloride (mg/L)', fontsize=12)
    ax.set_title('Blue Thumb Virtual Triangulation Validation\nVolunteer vs. Professional Chloride Measurements', 
                 fontsize=14, fontweight='bold')
    
    stats_text = (f'N = {len(matches_df)}\n'
                  f'R² = {r_squared:.3f}\n'
                  f'Slope = {slope:.3f}\n'
                  f'p < 0.0001')
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=10)
    
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    
    output_dir = Path(config['output_paths']['results'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "validation_plot.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved validation plot: {output_path}")
    print(f"  Resolution: 300 DPI")
    print(f"  Points: {len(matches_df)}")


def main():
    """Create all visualizations"""
    
    config = load_config()
    
    print("=== Visualization ===\n")
    
    results_dir = Path(config['output_paths']['results'])
    matches_df = pd.read_csv(results_dir / 'matched_pairs.csv')
    
    print(f"Loaded {len(matches_df)} matched pairs")
    
    create_validation_plot(matches_df, config)
    
    print("\n✅ Visualization complete")


if __name__ == "__main__":
    main()
