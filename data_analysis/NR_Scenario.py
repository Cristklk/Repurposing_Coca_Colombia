# -----------------------------------------------------------------------------
# Script: Natural Regrowth (NR) Scenario Analysis
# Scenario: Passive Restoration (Natural Regeneration)
# Metric: Potential Carbon Accumulation (Sequestration)
# -----------------------------------------------------------------------------

#%% 
#*1. Import Necessary Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

#%% 
#*2. Specifying path 

try:
    # Robust path resolution
    interim_path = Path('../data/interim/').resolve()
    results_path = Path('../data/results/').resolve()
    
    if not interim_path.exists():
        if Path('data/interim').exists():
            interim_path = Path('data/interim').resolve()
            results_path = Path('data/results').resolve()
        else:
            interim_path = Path('.').resolve()
            results_path = Path('.').resolve()

    print(f"Data Source Path: {interim_path}")
    print(f"Results Output Path: {results_path}")

except Exception as e:
    print(f"Error setting paths: {e}")

results_path.mkdir(parents=True, exist_ok=True)

#%% 
#*3. Creating a function for Loading data

def load_data(filepath, dtype_dict=None, file_type='excel'):
    try:
        if file_type == 'csv':
            df = pd.read_csv(filepath, dtype=dtype_dict)
        elif file_type == 'excel':
            df = pd.read_excel(filepath, dtype=dtype_dict)
        else:
            print("Unsupported file type.")
            return None
        print(f"Data loaded successfully from {filepath.name}")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# %% 
#*4. Loading Data (NR Potential)
# Input: NR_Spatial_Analysis.xlsx or similar (Output from Phase 1)
nr_path = interim_path / 'Natural_Regrowth_Potential.xlsx'
dtype_dict = {'GRI_1K_F_1': str}

NR_df = load_data(nr_path, dtype_dict=dtype_dict, file_type='excel')
print(NR_df.head())

#%% 
#*5. Preprocessing Data (C -> CO2 Conversion)

def preprocess_nr_data(df):
    try:
        # 1. Clean Area
        if 'Coca_2022' in df.columns:
            df['Coca_2022'] = df['Coca_2022'].astype(float)
            df.loc[df['Coca_2022'] < 0.067, 'Coca_2022'] = 0

        # 2. Conversion Factor (Carbon to CO2)
        # Ratio of molecular weights (44/12) ≈ 3.67
        C_TO_CO2 = 3.67 

        if 'Mean_Seq_MgC' in df.columns:
            # Rename for clarity if needed, or create new col
            df['Sequestration_MgC_ha'] = df['Mean_Seq_MgC'].astype(float)
            
            # Convert Mean Metric
            df['Sequestration_MgCO2_ha'] = df['Sequestration_MgC_ha'] * C_TO_CO2
            
            # Convert Uncertainty Metrics
            # Assuming 'Error_Ratio' is proportional and 'STD_Variability' is in MgC
            if 'Error_Ratio' in df.columns:
                df['Error_Ratio_CO2'] = df['Error_Ratio'] * C_TO_CO2
            
            if 'STD_Variability' in df.columns:
                df['Sequestration_STD_MgCO2_ha'] = df['STD_Variability'] * C_TO_CO2
                
        else:
            raise ValueError("Column 'Mean_Seq_MgC' not found.")

        print("Preprocessing completed (C -> CO2 conversion).")
        
    except Exception as e:
        print(f"Error during preprocessing: {e}")
    return df

NR_df = preprocess_nr_data(NR_df)
print(NR_df[['GRI_1K_F_1', 'Sequestration_MgCO2_ha']].head())

#%% 
#*6. Calculating Total Potential (Area * Rate)

def calculate_nr_potential(df):
    try:
        # Calculate Total per Grid Cell (Mg CO2/yr)
        df['NR_Total_Potential_MgCO2_yr'] = df['Coca_2022'] * df['Sequestration_MgCO2_ha']
        
        # Calculate Total intra cell variability and error ratio Uncertainty per Grid Cell
        if 'Sequestration_STD_MgCO2_ha' in df.columns:
            df['NR_Total_STD_MgCO2_yr'] = df['Coca_2022'] * df['Sequestration_STD_MgCO2_ha']
            df['NR_Total_Error_Ratio_MgCO2_yr'] = df['Coca_2022'] * df['Error_Ratio_CO2']
            
        print("Total potentials calculated.")
    except Exception as e:
        print(f"Error during calculation: {e}")
    return df

NR_df = calculate_nr_potential(NR_df)

#%% 
#*7. Statistics (Visualization)

def generate_histograms(df, yield_column, bins=20):
    plt.figure(figsize=(10, 6))
    data = df[yield_column].dropna()
    sns.histplot(data, bins=bins, kde=True, color='teal')
    plt.title(f'Distribution of {yield_column}')
    plt.xlabel('Potential Sequestration (Mg CO2e/ha/yr)')
    plt.ylabel('Frequency')
    plt.show()

def descriptive_statistics(df, yield_column):
    print(f"\nDescriptive Statistics for {yield_column}:")
    print(df[yield_column].describe())

def segmentation_analysis(df, area_column='Coca_2022', yield_column='Sequestration_MgCO2_ha'):
    median_area = df[area_column].median()
    larger_areas_df = df[df[area_column] > median_area]
    smaller_areas_df = df[df[area_column] <= median_area]
    
    print("\n--- Segmentation Analysis (NR) ---")
    print("Larger Coca Areas:")
    print(larger_areas_df[yield_column].describe())
    print("\nSmaller Coca Areas:")
    print(smaller_areas_df[yield_column].describe())

if 'Sequestration_MgCO2_ha' in NR_df.columns:
    generate_histograms(NR_df, 'Sequestration_MgCO2_ha', bins=20)
    descriptive_statistics(NR_df, 'Sequestration_MgCO2_ha')
    segmentation_analysis(NR_df)

NR_df.fillna(0, inplace=True)

#%% 
#*8. Printing National Results (Formatted Summary)

total_area = NR_df["Coca_2022"].sum()

# Aggregate National Totals (Convert to Mt CO2e)
# 1 Mg = 1 Ton; 1,000,000 Mg = 1 Mt
total_accumulation_mt = NR_df['NR_Total_Potential_MgCO2_yr'].sum() / 10**6
total_std_mt = NR_df['NR_Total_STD_MgCO2_yr'].sum() / 10**6

# Calculate Error Ratio aggregate if needed (for comparison)
if 'Error_Ratio_CO2' in NR_df.columns:
    # Weighted error calculation or simple sum depends on the definition of Error Ratio in Phase 1
    # Assuming simple scaling for consistency with your previous code
    total_error_mt = (NR_df['Coca_2022'] * NR_df['Error_Ratio_CO2']).sum() / 10**6
else:
    total_error_mt = 0

print("-" * 50)
print(f"Total Available Area: {total_area:,.2f} ha")
print(f"1. Potential Carbon Accumulation:      {total_accumulation_mt:,.4f} Mt CO2eq")
print(f"   (Natural Regrowth Sequestration)")
print(f"2. Intra-cell Variability (STD):       {total_std_mt:,.4f} Mt CO2eq")
print(f"3. Error Ratio (aggregated):           {total_error_mt:,.4f} Mt CO2eq")
print("-" * 50)

#%% 
#*9. Exporting the Processed Data

def export_data(df, filename):
    try:
        cols_to_keep = [
            'GRI_1K_F_1', 
            'Coca_2022',
            'Sequestration_MgC_ha',      # Original Carbon
            'Sequestration_MgCO2_ha',    # Converted CO2
            'Sequestration_STD_MgCO2_ha',
            'Error_Ratio_CO2',
            'NR_Total_Potential_MgCO2_yr',
            'NR_Total_STD_MgCO2_yr',
            'NR_Total_Error_Ratio_MgCO2_yr'
        ]
        
        cols_final = [c for c in cols_to_keep if c in df.columns]
        
        df_export = df[cols_final].copy()
        df_export.to_excel(filename, index=False)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")

NR_Scenario_path = results_path / 'NR_Scenario.xlsx'
export_data(NR_df, NR_Scenario_path)