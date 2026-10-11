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
#*4. Loading Agroclimatic Yield Data
AFS_path = interim_path / 'Agroclimatic_Potential_Yields_Final.xlsx'
dtype_dict = {'GRI_1K_F_1': str}

AFS_df = load_data(AFS_path, dtype_dict=dtype_dict, file_type='excel')
print(AFS_df.head())

#%% 
#*5. Statistical Analysis of Yields (Validation Step)
# This step validates the raw yield data before we apply normalization.
# It ensures the MAX_RUBBER_GAEZ constant (2514) is appropriate relative to the data.

def analyze_yield_statistics(df, yield_col='Yield_Rubber'):
    try:
        if yield_col not in df.columns:
            print(f"⚠️ Column {yield_col} not found. Skipping stats.")
            return

        print(f"\n--- Statistical Analysis: {yield_col} (Kg/ha) ---")
        stats = df[yield_col].describe()
        print(stats)
        
        # Check for values exceeding the theoretical max
        theoretical_max = 2514
        exceeding = df[df[yield_col] > theoretical_max]
        
        if not exceeding.empty:
            print(f"⚠️ WARNING: {len(exceeding)} records exceed the theoretical max of {theoretical_max}.")
            print(f"Max value found: {df[yield_col].max()}")
        else:
            print(f"✅ Data Validation: All values are within the theoretical limit ({theoretical_max}).")
            print(f"   Max value found in dataset: {df[yield_col].max()}")
            
        # Visualization
        plt.figure(figsize=(10, 5))
        sns.histplot(df[yield_col].dropna(), bins=30, kde=True, color='blue')
        plt.axvline(theoretical_max, color='red', linestyle='--', label=f'GAEZ Max ({theoretical_max})')
        plt.title(f'Distribution of Raw {yield_col}')
        plt.xlabel('Potential Yield (Kg/ha)')
        plt.legend()
        plt.show()
        
    except Exception as e:
        print(f"Error during statistical analysis: {e}")

# Run the analysis specifically for Rubber (the driver of our AFS index)
analyze_yield_statistics(AFS_df, 'Yield_Rubber')

#%% 
#*6. Creating preprocess Data function (System-Level Lifecycle Analysis)

def preprocess_data(df):
    try:
        # 1. Clean Area Data
        if 'Coca_2022' in df.columns:
            df['Coca_2022'] = df['Coca_2022'].astype(float)
            df.loc[df['Coca_2022'] < 0.067, 'Coca_2022'] = 0
        
        # --- AFS SYSTEM PARAMETERS ---
        # Driven by Rubber Suitability Index
        MAX_RUBBER_GAEZ = 2514  # Max Rubber Yield from GAEZ (Kg/ha) 
        
        # System-Wide Carbon Factors (Mg CO2e/ha/yr)
        AFS_GROSS_Sequestration = 15.68 
        AFS_LIFECYCLE_EMISSIONS = 3.38 

        if 'Yield_Rubber' in df.columns:
            # 1. Normalize System Performance based on Rubber Yield (0 to 1)
            # This creates the "Suitability Index" for the AFS
            df['AFS_Index'] = df['Yield_Rubber'] / MAX_RUBBER_GAEZ
            df['AFS_Index_STD'] = df['STD_Rubber'] / MAX_RUBBER_GAEZ
            
            # 2. Calculate System-Level Carbon Metrics
            # The potential is scaled by the suitability (AFS_Index)
            df['AFS_Gross_Sequestration_MgCO2_ha'] = df['AFS_Index'] * AFS_GROSS_Sequestration
            df['AFS_Emissions_MgCO2_ha'] = df['AFS_Index'] * AFS_LIFECYCLE_EMISSIONS
            
            # 3. Net Mitigation Potential
            df['AFS_Net_MgCO2_ha'] = df['AFS_Gross_Sequestration_MgCO2_ha'] - df['AFS_Emissions_MgCO2_ha']
            
            # 4. Uncertainty
            df['AFS_Net_STD_MgCO2_ha'] = df['AFS_Index_STD'] * (AFS_GROSS_Sequestration - AFS_LIFECYCLE_EMISSIONS)

        else:
            print("⚠️ Warning: 'Yield_Rubber' not found.")

        print("Preprocessing and System-Level Lifecycle Analysis completed.")
        
    except Exception as e:
        print(f"Error during preprocessing: {e}")
    return df

#%% 
# Running the preprocess function
AFS_df = preprocess_data(AFS_df)
print(AFS_df[['GRI_1K_F_1', 'AFS_Net_MgCO2_ha']].head())

#%% 
#*7. Calculating Total Potentials (Area * Net_Metric)

def calculate_total_potentials(df):
    try:
        if 'Coca_2022' in df.columns and 'AFS_Net_MgCO2_ha' in df.columns:
            # Calculate Total Mitigation per Grid Cell (Mg CO2e/yr)
            df['AFS_Total_Net_Potential_MgCO2_yr'] = df['Coca_2022'] * df['AFS_Net_MgCO2_ha']
            
            # Calculate Total Uncertainty per Grid Cell
            df['AFS_Total_STD_MgCO2_yr'] = df['Coca_2022'] * df['AFS_Net_STD_MgCO2_ha']

            # Calculate Total Lifecycle Emissions per Grid Cell
            df['AFS_Total_Lifecycle_Emissions_MgCO2_yr'] = df['Coca_2022'] * df['AFS_Emissions_MgCO2_ha']

            #Calculate Total Gross Sequestration per Grid Cell
            df['AFS_Total_Gross_Sequestration_MgCO2_yr'] = df['Coca_2022'] * df['AFS_Gross_Sequestration_MgCO2_ha']
            
        print("Total potentials calculated.")
    except Exception as e:
        print(f"Error during calculation: {e}")
    return df

#%% Running the function
AFS_df = calculate_total_potentials(AFS_df)
print(AFS_df.head())

#%% 
#*8. Creating function to obtain statistics (Net Potential)

def generate_histograms(df, yield_column, bins=20):
    plt.figure(figsize=(10, 6))
    data = df[yield_column].dropna()
    sns.histplot(data, bins=bins, kde=True, color='orange')
    plt.title(f'Distribution of {yield_column}')
    plt.xlabel('Net Mitigation Potential (Mg CO2e/ha)')
    plt.ylabel('Frequency')
    plt.show()

def descriptive_statistics(df, yield_column):
    print(f"\nDescriptive Statistics for {yield_column}:")
    print(df[yield_column].describe())

def segmentation_analysis(df, area_column='Coca_2022', yield_column='AFS_Net_MgCO2_ha'):
    median_area = df[area_column].median()
    larger_areas_df = df[df[area_column] > median_area]
    smaller_areas_df = df[df[area_column] <= median_area]
    
    print("\n--- Segmentation Analysis (AFS System) ---")
    print("Larger Coca Areas:")
    print(larger_areas_df[yield_column].describe())
    print("\nSmaller Coca Areas:")
    print(smaller_areas_df[yield_column].describe())

# Execute Stats
if 'AFS_Net_MgCO2_ha' in AFS_df.columns:
    generate_histograms(AFS_df, 'AFS_Net_MgCO2_ha', bins=20)
    descriptive_statistics(AFS_df, 'AFS_Net_MgCO2_ha')
    segmentation_analysis(AFS_df)

AFS_df.fillna(0, inplace=True)

#%% 
#%% 
#*9. Printing National Results with Lifecycle Breakdown

total_area = AFS_df["Coca_2022"].sum()

# We perform the vector multiplication (Area * Metric_per_ha) inside the sum 
# to get the totals without creating extra columns in the dataframe just for printing.

# 1. Gross Carbon sequestration (Total Sequestration before emissions)
gross_Sequestration_mt = AFS_df['AFS_Total_Gross_Sequestration_MgCO2_yr'].sum() / 10**6

# 2. Lifecycle Emissions (Fertilizer, establishment, management)
lifecycle_emissions_mt = AFS_df['AFS_Total_Lifecycle_Emissions_MgCO2_yr'].sum() / 10**6

# 3. Net Mitigation (Gross - Emissions)
# This matches the 'AFS_Total_Net_Potential_MgCO2_yr' column we calculated earlier
net_mitigation_mt = AFS_df['AFS_Total_Net_Potential_MgCO2_yr'].sum() / 10**6
net_std_mt = AFS_df['AFS_Total_STD_MgCO2_yr'].sum() / 10**6

print("-" * 50)
print(f"Total Available Area: {total_area:,.2f} ha")
print(f"1. Gross Carbon sequestration (Sequestration): {gross_Sequestration_mt:,.4f} Mt CO2eq")
print(f"2. Lifecycle Emissions (AFS):          {lifecycle_emissions_mt:,.4f} Mt CO2eq")
print(f"3. Net Mitigation Potential:           {net_mitigation_mt:,.4f} Mt CO2eq")
print(f"   Intra-cell Variability Uncertainty (STD):      {net_std_mt:,.4f} Mt CO2eq")
print("-" * 50)

#%% 
#*10. Exporting the Processed Data

def export_data(df, filename):
    try:
        # We include the breakdown columns in the export as well for transparency
        cols_to_keep = [
            'GRI_1K_F_1', 
            'Coca_2022',
            'AFS_Index',
            'AFS_Gross_Sequestration_MgCO2_ha',   # Added
            'AFS_Emissions_MgCO2_ha',     # Added
            'AFS_Net_MgCO2_ha',
            'AFS_Net_STD_MgCO2_ha',
            'AFS_Total_Net_Potential_MgCO2_yr',
            'AFS_Total_Lifecycle_Emissions_MgCO2_yr',  # Added
            'AFS_Total_Gross_Sequestration_MgCO2_yr',        # Added
            'AFS_Total_STD_MgCO2_yr'
        ]
        
        cols_final = [c for c in cols_to_keep if c in df.columns]
        
        df_export = df[cols_final].copy()
        df_export.to_excel(filename, index=False)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")

AFS_Scenario_path = results_path / 'AFS_Scenario.xlsx'
export_data(AFS_df, AFS_Scenario_path)