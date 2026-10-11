# -----------------------------------------------------------------------------
# Script: BECCS Scenario Analysis (Bioenergy with Carbon Capture & Storage)
# Scenario: Bioethanol + CCS (Replacing Gasoline)
# Methodology: Ordonez et al. 2018 (Scenario S4 with CCS)
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
#* 4. Loading Data (Agroclimatic Yields)
input_path = interim_path / 'Agroclimatic_Potential_Yields_Final.xlsx'
dtype_dict = {'GRI_1K_F_1': str}

beccs_df = load_data(input_path, dtype_dict=dtype_dict, file_type='excel')
print(beccs_df.head())

#%% 
#*5. Creating preprocess Data function (Yield -> Cane Mass)

def preprocess_yields(df):
    try:
        # 1. Clean Area Data
        if 'Coca_2022' in df.columns:
            df['Coca_2022'] = df['Coca_2022'].astype(float)
            df.loc[df['Coca_2022'] < 0.067, 'Coca_2022'] = 0

        # 2. Convert GAEZ Output to Total Cane Mass
        # Factor 10: Convert Sugar Index to Cane Mass (GAEZ Doc p.156)
        GAEZ_SUGAR_TO_CANE_FACTOR = 10 
        
        if 'Yield_SugarCane' in df.columns:
            df['Yield_SugarCane'] = df['Yield_SugarCane'].astype(float)
            df['STD_SugarCane'] = df['STD_SugarCane'].astype(float) # Ensure STD is float
            # Mg Cane / ha
            df['Cane_Yield_Kg_ha'] = df['Yield_SugarCane'] * GAEZ_SUGAR_TO_CANE_FACTOR
            df['Cane_STD_Kg_ha']   = df['STD_SugarCane'] * GAEZ_SUGAR_TO_CANE_FACTOR
            
            # Total Cane Mass per Grid Cell (Mg)
            df['Total_Cane_Mg'] = (df['Cane_Yield_Kg_ha'] * df['Coca_2022']) / 1000
            df['Total_Cane_STD_Mg'] = (df['Cane_STD_Kg_ha'] * df['Coca_2022']) / 1000
            
        else:
            raise ValueError("Column 'Yield_SugarCane' not found.")

        print("Preprocessing completed: Converted to Total Cane Mass.")
        
    except Exception as e:
        print(f"Error during preprocessing: {e}")
    return df

beccs_df = preprocess_yields(beccs_df)

#%% 
#*6. Calculating BECCS Potentials (Detailed Breakdown)

def calculate_beccs_components(df):
    try:
        # --- CONSTANTS (Ordonez et al. 2018 - Scenario S4) ---
        ETHANOL_YIELD_L_PER_MG = 88.5
        ETHANOL_DENSITY_KG_L   = 0.789
        LHHV_MJ_KG             = 28.26
        
        # --- EMISSION FACTORS (gCO2/MJ) ---
        # 1. Baseline: Gasoline Fossil Fuel Emission
        EF_GASOLINE_SUBSTITUTION = 94.0
        
        # 2. Life Cycle (Gross): Production emissions WITHOUT CCS
        # Standard S4 Bioenergy intensity
        EF_LIFECYCLE_GROSS = 31.1
        
        # 3. BECCS Net Intensity: Target Net Emission with CCS
        # From code/methodology: The final intensity is -2.7 gCO2/MJ
        EF_BECCS_NET = -2.7
        
        # 4. Derived CCS Mitigation: The amount captured to reach Net -2.7
        # Capture = Gross (31.1) - Net (-2.7) = 33.8 gCO2/MJ
        EF_CCS_CAPTURE = EF_LIFECYCLE_GROSS - EF_BECCS_NET # 33.8

        # --- CALCULATIONS ---
        
        # A. Energy Production (MJ)
        df['Ethanol_Liters'] = df['Total_Cane_Mg'] * ETHANOL_YIELD_L_PER_MG
        df['Ethanol_STD_Liters'] = df['Total_Cane_STD_Mg'] * ETHANOL_YIELD_L_PER_MG
        
        df['Ethanol_MJ'] = (df['Ethanol_Liters'] * ETHANOL_DENSITY_KG_L) * LHHV_MJ_KG
        df['Ethanol_STD_MJ'] = (df['Ethanol_STD_Liters'] * ETHANOL_DENSITY_KG_L) * LHHV_MJ_KG
        
        # B. COMPONENT 1: Fossil Fuel Substitution (Gross Benefit)
        # Replacing Gasoline
        df['Fossil_Fuel_Substitution_gCO2'] = df['Ethanol_MJ'] * EF_GASOLINE_SUBSTITUTION
        df['Fossil_Fuel_Substitution_STD_gCO2'] = df['Ethanol_STD_MJ'] * EF_GASOLINE_SUBSTITUTION
        
        # C. COMPONENT 2: Life Cycle Emissions (Gross Cost)
        # Emissions from farming/processing
        df['Lifecycle_Emissions_Gross_gCO2'] = df['Ethanol_MJ'] * EF_LIFECYCLE_GROSS
        df['Lifecycle_Emissions_Gross_STD_gCO2'] = df['Ethanol_STD_MJ'] * EF_LIFECYCLE_GROSS
        
        # D. COMPONENT 3: Mitigation from CCS (Capture)
        # Carbon captured and stored
        df['CCS_Mitigation_gCO2'] = df['Ethanol_MJ'] * EF_CCS_CAPTURE
        df['CCS_Mitigation_STD_gCO2'] = df['Ethanol_STD_MJ'] * EF_CCS_CAPTURE
        
        # E. Net Project Emission (Gross Lifecycle - CCS Capture)
        # Should equal Energy * -2.7
        df['Net_Project_Emission_gCO2'] = df['Lifecycle_Emissions_Gross_gCO2'] - df['CCS_Mitigation_gCO2']
        df['Net_Project_Emission_STD_gCO2'] = np.sqrt(df['Lifecycle_Emissions_Gross_STD_gCO2']**2 + df['CCS_Mitigation_STD_gCO2']**2)

        # F. COMPONENT 4: Net Avoided Emissions (Substitution - Net Project)
        # (94.0) - (-2.7) = 96.7 gCO2/MJ benefit
        df['Avoided_Emissions_BECCS_gCO2'] = df['Fossil_Fuel_Substitution_gCO2'] - df['Net_Project_Emission_gCO2']
        df['Avoided_Emissions_BECCS_STD_gCO2'] = df['Fossil_Fuel_Substitution_STD_gCO2'] - df['Net_Project_Emission_STD_gCO2']
        
        # --- CONVERSIONS ---
        
        # Convert all to Megagrams (Mg CO2e)
        df['Fossil_Fuel_Substitution_MgCO2']  = df['Fossil_Fuel_Substitution_gCO2'] / 10**6
        df['Lifecycle_Emissions_Gross_MgCO2'] = df['Lifecycle_Emissions_Gross_gCO2'] / 10**6
        df['CCS_Mitigation_MgCO2']            = df['CCS_Mitigation_gCO2'] / 10**6
        df['Avoided_Emissions_BECCS_MgCO2']   = df['Avoided_Emissions_BECCS_gCO2'] / 10**6
        df['Avoided_Emissions_BECCS_STD_MgCO2'] = df['Avoided_Emissions_BECCS_STD_gCO2'] / 10**6

        # Metric per Hectare for Analysis
        df['Avoided_Emissions_BECCS_MgCO2_ha'] = 0.0
        mask = df['Coca_2022'] > 0
        df.loc[mask, 'Avoided_Emissions_BECCS_MgCO2_ha'] = (
            df.loc[mask, 'Avoided_Emissions_BECCS_MgCO2'] / df.loc[mask, 'Coca_2022']
        )

        print("BECCS components calculated successfully.")
        
    except Exception as e:
        print(f"Error during calculation: {e}")
    return df

beccs_df = calculate_beccs_components(beccs_df)
print(beccs_df[['GRI_1K_F_1', 'Avoided_Emissions_BECCS_MgCO2']].head())

#%% 
#* 7. Statistics (Net Avoided Emissions)

def generate_histograms(df, yield_column, bins=20):
    plt.figure(figsize=(10, 6))
    data = df[yield_column].dropna()
    sns.histplot(data, bins=bins, kde=True, color='purple')
    plt.title(f'Distribution of {yield_column}')
    plt.xlabel('Net Avoided Emissions (Mg CO2e/ha)')
    plt.ylabel('Frequency')
    plt.show()

def descriptive_statistics(df, yield_column):
    print(f"\nDescriptive Statistics for {yield_column}:")
    print(df[yield_column].describe())

def segmentation_analysis(df, area_column='Coca_2022', yield_column='Avoided_Emissions_BECCS_MgCO2_ha'):
    median_area = df[area_column].median()
    larger_areas_df = df[df[area_column] > median_area]
    smaller_areas_df = df[df[area_column] <= median_area]
    
    print("\n--- Segmentation Analysis (BECCS) ---")
    print("Larger Coca Areas:")
    print(larger_areas_df[yield_column].describe())
    print("\nSmaller Coca Areas:")
    print(smaller_areas_df[yield_column].describe())

if 'Avoided_Emissions_BECCS_MgCO2_ha' in beccs_df.columns:
    generate_histograms(beccs_df, 'Avoided_Emissions_BECCS_MgCO2_ha', bins=20)
    descriptive_statistics(beccs_df, 'Avoided_Emissions_BECCS_MgCO2_ha')
    segmentation_analysis(beccs_df)

beccs_df.fillna(0, inplace=True)

#%% 
#*8. Printing National Results (Detailed Breakdown)

total_area = beccs_df["Coca_2022"].sum()

# Aggregate National Totals (Convert to Mt CO2e)
substitution_mt = beccs_df['Fossil_Fuel_Substitution_MgCO2'].sum() / 10**6
lifecycle_mt    = beccs_df['Lifecycle_Emissions_Gross_MgCO2'].sum() / 10**6
ccs_mt          = beccs_df['CCS_Mitigation_MgCO2'].sum() / 10**6
net_avoided_mt  = beccs_df['Avoided_Emissions_BECCS_MgCO2'].sum() / 10**6
net_std_mt      = beccs_df['Avoided_Emissions_BECCS_STD_MgCO2'].sum() / 10**6

print("-" * 60)
print(f"Total Available Area: {total_area:,.2f} ha")
print(f"1. Fossil Fuel Substitution (Gross):   {substitution_mt:,.4f} Mt CO2eq")
print(f"2. Life Cycle Emissions (Gross):       {lifecycle_mt:,.4f} Mt CO2eq")
print(f"3. Mitigation from CCS (Capture):      {ccs_mt:,.4f} Mt CO2eq")
print("-" * 60)
print(f"4. Net Avoided Emissions (BECCS):      {net_avoided_mt:,.4f} Mt CO2eq")
print(f"   (Calculation: Sub. - (Life - CCS))")
print(f"   Intra-cell Variability Uncertainty (STD):              {net_std_mt:,.4f} Mt CO2eq")
print("-" * 60)

#%% 
#*9. Exporting the Processed Data

def export_data(df, filename):
    try:
        # Export all 4 component columns + Net + Uncertainty
        cols_to_keep = [
            'GRI_1K_F_1', 
            'Coca_2022',
            'Cane_Yield_Kg_ha',
            'Fossil_Fuel_Substitution_MgCO2',  # 1. Substitution
            'Lifecycle_Emissions_Gross_MgCO2', # 2. Lifecycle
            'CCS_Mitigation_MgCO2',            # 3. CCS
            'Avoided_Emissions_BECCS_MgCO2',   # 4. Net Avoided
            'Avoided_Emissions_BECCS_STD_MgCO2',
            'Avoided_Emissions_BECCS_MgCO2_ha'
        ]
        
        cols_final = [c for c in cols_to_keep if c in df.columns]
        
        df_export = df[cols_final].copy()
        df_export.to_excel(filename, index=False)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {e}")

BECCS_Scenario_path = results_path / 'BECCS_Scenario.xlsx'
export_data(beccs_df, BECCS_Scenario_path)