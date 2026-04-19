"""
India Economic Analysis — Data Cleaning Script
Sources: World Bank Open Data
Indicators: GDP, Unemployment, Governance/Economic Policy, Country Overview
Author: [Your Name]
"""

import pandas as pd
import os

# ─────────────────────────────────────────
# FILE PATHS — update if your folder is different
# ─────────────────────────────────────────
RAW_FOLDER = "data/raw/"
OUTPUT_PATH = "data/india_economy_clean.csv"

os.makedirs("data", exist_ok=True)

FILES = {
    "gdp":          "API_NY.GDP.MKTP.CD_DS2_en_csv_v2_24.csv",
    "unemployment": "API_SL.UEM.TOTL.ZS_DS2_en_csv_v2_36.csv",
    "governance":   "API_IQ.CPA.PROT.XQ_DS2_en_csv_v2_9206.csv",
    "overview":     "API_IND_DS2_en_csv_v2_2968.csv",
}


# ─────────────────────────────────────────
# HELPER — Load a World Bank CSV
# World Bank CSVs have 4 junk header rows
# Columns are: Country Name, Country Code,
#              Indicator Name, Indicator Code,
#              then years 1960, 1961 ... 2023
# ─────────────────────────────────────────
def load_wb_csv(filename):
    path = os.path.join(RAW_FOLDER, filename)
    df = pd.read_csv(path, skiprows=4)
    # Drop unnamed trailing columns World Bank sometimes adds
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    print(f"✅ Loaded: {filename} → {df.shape}")
    return df


# ─────────────────────────────────────────
# 1. LOAD GDP DATA
# ─────────────────────────────────────────
gdp_raw = load_wb_csv(FILES["gdp"])

# Filter for India only
gdp_india = gdp_raw[gdp_raw["Country Code"] == "IND"].copy()

# Melt year columns into rows
year_cols = [str(y) for y in range(2000, 2024) if str(y) in gdp_india.columns]
gdp_long = gdp_india.melt(
    id_vars=["Country Name", "Country Code", "Indicator Name"],
    value_vars=year_cols,
    var_name="Year",
    value_name="GDP_USD"
)

gdp_long["Year"] = gdp_long["Year"].astype(int)
gdp_long = gdp_long[["Year", "GDP_USD"]].dropna()
gdp_long["GDP_Trillion_USD"] = (gdp_long["GDP_USD"] / 1e12).round(3)
print(f"   GDP rows after cleaning: {len(gdp_long)}")


# ─────────────────────────────────────────
# 2. LOAD UNEMPLOYMENT DATA
# ─────────────────────────────────────────
unem_raw = load_wb_csv(FILES["unemployment"])

unem_india = unem_raw[unem_raw["Country Code"] == "IND"].copy()

year_cols_u = [str(y) for y in range(2000, 2024) if str(y) in unem_india.columns]
unem_long = unem_india.melt(
    id_vars=["Country Name", "Country Code", "Indicator Name"],
    value_vars=year_cols_u,
    var_name="Year",
    value_name="Unemployment_Rate"
)

unem_long["Year"] = unem_long["Year"].astype(int)
unem_long = unem_long[["Year", "Unemployment_Rate"]].dropna()
unem_long["Unemployment_Rate"] = unem_long["Unemployment_Rate"].round(2)
print(f"   Unemployment rows after cleaning: {len(unem_long)}")


# ─────────────────────────────────────────
# 3. LOAD GOVERNANCE / ECONOMIC POLICY DATA
# ─────────────────────────────────────────
gov_raw = load_wb_csv(FILES["governance"])

gov_india = gov_raw[gov_raw["Country Code"] == "IND"].copy()

year_cols_g = [str(y) for y in range(2000, 2024) if str(y) in gov_india.columns]
gov_long = gov_india.melt(
    id_vars=["Country Name", "Country Code", "Indicator Name"],
    value_vars=year_cols_g,
    var_name="Year",
    value_name="Policy_Score"
)

gov_long["Year"] = gov_long["Year"].astype(int)
gov_long = gov_long[["Year", "Policy_Score"]].dropna()
gov_long["Policy_Score"] = gov_long["Policy_Score"].round(2)
print(f"   Governance rows after cleaning: {len(gov_long)}")


# ─────────────────────────────────────────
# 4. MERGE ALL INTO ONE CLEAN DATAFRAME
# ─────────────────────────────────────────
df = gdp_long.merge(unem_long, on="Year", how="outer")
df = df.merge(gov_long, on="Year", how="outer")
df = df.sort_values("Year").reset_index(drop=True)


# ─────────────────────────────────────────
# 5. ADD DERIVED COLUMNS
# ─────────────────────────────────────────

# GDP Year-on-Year Growth Rate
df["GDP_Growth_Rate"] = df["GDP_USD"].pct_change().mul(100).round(2)

# Economic Era labels
def get_era(year):
    if year <= 2004:
        return "Early 2000s"
    elif year <= 2009:
        return "Pre-GFC Boom"
    elif year <= 2014:
        return "Post-GFC Recovery"
    elif year <= 2019:
        return "Reform Era"
    else:
        return "COVID & Recovery"

df["Economic_Era"] = df["Year"].apply(get_era)

# GDP in readable format
df["GDP_Label"] = df["GDP_Trillion_USD"].apply(
    lambda x: f"${x:.2f}T" if pd.notna(x) else "N/A"
)

print(f"\n✅ Merged dataframe shape: {df.shape}")


# ─────────────────────────────────────────
# 6. FINAL CHECK
# ─────────────────────────────────────────
print("\n" + "=" * 50)
print("CLEANED DATA OVERVIEW")
print("=" * 50)
print(df.to_string(index=False))
print(f"\nNull values:\n{df.isnull().sum()}")
print(f"\nYears covered: {df['Year'].min()} – {df['Year'].max()}")
print(f"Peak GDP: {df.loc[df['GDP_Trillion_USD'].idxmax(), 'GDP_Label']} in {df.loc[df['GDP_Trillion_USD'].idxmax(), 'Year']}")
print(f"Lowest Unemployment: {df['Unemployment_Rate'].min()}% in {df.loc[df['Unemployment_Rate'].idxmin(), 'Year']}")


# ─────────────────────────────────────────
# 7. EXPORT
# ─────────────────────────────────────────
df.to_csv(OUTPUT_PATH, index=False)
print(f"\n✅ Clean file saved to: {OUTPUT_PATH}")
print("Ready for visualization in Python (matplotlib/seaborn) or Power BI!")
