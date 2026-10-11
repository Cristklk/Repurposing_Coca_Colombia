# Repurposing Coca Cultivation in Colombia for Climate Mitigation

## Project Overview
This project quantifies the GHG emissions produced by the cocaine production in 2022 accounting for Land-Use change emissions and life cycle emissions along the value chain.  At the same time climate benefits of transitioning illegal coca cultivation areas in Colombia toward four alternative land-use scenarios. By integrating agroclimatic potential yields within high-resolution spatial data (1km² grid) delimiting illegal coca cultivation in 2022.



## 1. Scenarios & Methodology

### **Scenario 1: Natural Regrowth (NR)**
* **Logic:** Passive forest restoration (Natural Regeneration).
* **Conversion:** Applied a stoichiometric factor of **3.67** to convert Carbon ($C$) accumulation to $CO_2$.
* **Assumptions:** Primary strategy for areas overlapping with National Parks and Forest Reserves.

### **Scenario 2: Agroforestry Systems (AFS)**
* **Logic:** Multi-strata systems (Rubber, Cocoa, Banana).
* **Normalization:** Yields normalized against GAEZ maximum potential (Rubber: 2501 kg/ha).
* **LCA:** Net mitigation = Gross Carbon Stock ($15.68\ Mg\ CO_2/ha$) - Lifecycle Emissions ($3.38\ Mg\ CO_2/ha$).

### **Scenario 3 & 4: Bioenergy (BE) & BECCS**
* **Logic:** Conversion of Sugarcane to Anhydrous Ethanol (Scenario S4, Ordonez et al. 2018).
* **Substitution:** Avoided emissions from displacing gasoline ($94.0\ gCO_2/MJ$).
* **BECCS:** Incorporates Carbon Capture and Storage (CCS) with a capture efficiency of $33.8\ gCO_2/MJ$.

## 2. Spatial Analysis Framework
The spatial analysis was conducted in **ArcGIS Pro** using a conservative "Centroid-in-Polygon" approach.

* **Regional Splits:** The national dataset was partitioned into five key regions for granular data engineering:
    * Pacific
    * Putumayo-Caqueta
    * Catatumbo
    * Central
    * Eastern Savannas

## 3. How to Use This Repository

### **Spatial Integration**
1. Open the ArcGIS Pro project.
2. Run the notebooks in the corresponding order; the outputs of the three first notebooks serve as inputs for the data analysis.
3. The notebook will automatically join the Excel results to the 1km² centroids identifier "GRI_1K_F_1"

### **Data Analysis**
Run the scripts in the `data_analysis` folder in order. Each script outputs an Excel file in `/data/results` containing grid-level mitigation and intra-cell variability uncertainty (STD).

## **Spatial Analysis**
Run the last script of the spatial analysis incorportating the outputs from the data_analysis.

---

## ⚠️ Important: Data Access & Licensing
**The code in this repository relies on proprietary primary data from the Integrated Illicit Crops Monitoring System (SIMCI).**

Due to licensing restrictions, the raw spatial datasets (e.g., coca density grids) **cannot be hosted in this public repository**.
* **Availability:** The specific datasets are available upon author request LUC_emissions_reprojected.tif, Protected_Areas.shp due to the use of primary data referenced in supplementary table 1.
* **Licensing:** Users must obtain the necessary permissions from **BIESIMCI** to access the raw spatial data.

**To reproduce the analysis:**
1. Obtain the raw data files from BIESIMCI.

2. Place the files in the data/raw/ directory following the naming conventions listed below.

3. For editors verifying reproducibility: All data is available following the repository structure. Once the paper is published, the restrictions mentioned above will be in place.
---

## 📂 Repository Structure

Run the code in the following order

/Repurposing_Coca_Colombia
│
├── /data
│   ├── /raw            # Colombia_basemap.shp, Grillas1k.shp,G5k_Coca_22 Regions.shp, Protected_Areas.shp
│   ├── /interim        # Protected:Areas.shp., LUC_emissions_reprojected.tif, Results from the spatial analysis 1
│   └── /results        # Scenario Excel files from the data analysis & Regional_Exports shapefiles Results from the Spatial analysis
│
├── /spatial_analysis         # ArcGIS Pro Spatial Workflow The noteboo should be used in the following order
│   ├── 1_Spatial_analysis_LUC_emissions.ipynb
│   ├── 2_Spatial_analysis_NR_Potential.ipynb
│   ├── 3_Spatial_analysis_Agroclimatic_Potential_yields.ipynb
│
├── /data_analysis            # Standalone Python Analysis
│   ├── 1_NR_Scenario.py
│   ├── 2_AFS_Scenario.py
│   ├── 3_BE_Scenario.py
│   └── 4_BECCS_Scenario.py
│
├── /spatial_analysis         # 
│   ├── 4_Regional_results_and_Scenario_integrations.ipynb
│


│
├── README.md           # Project Documentation
└── environment.yml     # needed packages
