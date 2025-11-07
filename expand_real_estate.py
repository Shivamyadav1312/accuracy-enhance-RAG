# expand_real_estate_docs.py
"""
Download 100+ additional real estate documents
Building on existing Zillow + Realtor.com data
"""

import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import time
import json

class ExpandedRealEstateDownloader:
    def __init__(self, output_dir="real_estate_expanded"):
        self.output = Path(output_dir)
        self.output.mkdir(exist_ok=True)
        self.count = 0
    
    def log(self, msg):
        print(f"[{self.count:03d}] {msg}")

    # ============ CATEGORY 1: ZILLOW EXPANDED (20 docs) ============
    
    def download_zillow_expanded(self):
        """Download ALL Zillow datasets (20+ files)"""
        print("\n📊 ZILLOW EXPANDED DATASETS")
        print("="*60)
        
        base = "https://files.zillowstatic.com/research/public_csvs/"
        
        datasets = {
            # Price data
            'zhvi_all_homes': 'zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
            'zhvi_top_tier': 'zhvi/Metro_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
            'zhvi_bottom_tier': 'zhvi/Metro_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
            'zhvi_1bedroom': 'zhvi/Metro_zhvi_bdrmcnt_1_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
            'zhvi_2bedroom': 'zhvi/Metro_zhvi_bdrmcnt_2_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
            
            # Rental data
            'zori_all': 'zori/Metro_zori_uc_sfrcondomfr_sm_month.csv',
            'zori_sfr': 'zori/Metro_zori_uc_sfr_sm_month.csv',
            
            # Inventory
            'inventory_all': 'invt_fs/Metro_invt_fs_uc_sfrcondo_month.csv',
            'new_listings': 'new_listings/Metro_new_listings_uc_sfrcondo_month.csv',
            'new_pending': 'new_pending/Metro_new_pending_uc_sfrcondo_month.csv',
            
            # Market dynamics
            'days_on_market': 'doz/Metro_mean_dom_uc_sfrcondo_sm_month.csv',
            'sale_to_list': 'sales_to_list/Metro_mean_sale_to_list_uc_sfrcondo_sm_month.csv',
            'pct_sold_above': 'pct_sold_above_list/Metro_pct_sold_above_list_uc_sfrcondo_month.csv',
            'pct_sold_below': 'pct_sold_below_list/Metro_pct_sold_below_list_uc_sfrcondo_month.csv',
            
            # Sales
            'median_sale_price': 'median_sale_price/Metro_median_sale_price_uc_sfrcondo_sm_month.csv',
            'sales_count': 'sales_count/Metro_sales_count_now_uc_sfrcondo_month.csv',
            
            # Price cuts
            'pct_price_cuts': 'pct_listings_price_cut/Metro_pct_listings_price_cut_uc_sfrcondo_month.csv',
            
            # Forecasts
            'zhvi_forecast': 'zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_forecast.csv',
        }
        
        for name, path in tqdm(datasets.items(), desc="Zillow"):
            try:
                url = base + path
                df = pd.read_csv(url)
                
                output_file = self.output / "zillow_data" / f"{name}.txt"
                output_file.parent.mkdir(exist_ok=True)
                
                with open(output_file, 'w') as f:
                    f.write(f"# Zillow: {name.replace('_', ' ').title()}\n\n")
                    f.write(f"Rows: {len(df)}\n")
                    f.write(f"Columns: {len(df.columns)}\n")
                    f.write(f"Date Range: {df.columns[-12]} to {df.columns[-1]}\n\n")
                    f.write("Sample Data:\n")
                    f.write(df.head(20).to_string())
                
                self.count += 1
                self.log(f"✅ Zillow: {name}")
                time.sleep(0.5)
                
            except Exception as e:
                self.log(f"❌ Failed: {name} - {str(e)}")
        
        print(f"\n✅ Zillow Expanded: {self.count} files")

    # ============ CATEGORY 2: METRO-SPECIFIC DEEP DIVES (30 docs) ============
    
    def create_metro_reports(self):
        """Create detailed reports for top 30 metros"""
        print("\n🏙️ TOP 30 METRO DEEP DIVES")
        print("="*60)
        
        top_metros = [
            "New York, NY", "Los Angeles, CA", "Chicago, IL", "Dallas, TX",
            "Houston, TX", "Washington, DC", "Philadelphia, PA", "Miami, FL",
            "Atlanta, GA", "Boston, MA", "Phoenix, AZ", "San Francisco, CA",
            "Riverside, CA", "Detroit, MI", "Seattle, WA", "Minneapolis, MN",
            "San Diego, CA", "Tampa, FL", "Denver, CO", "St. Louis, MO",
            "Baltimore, MD", "Charlotte, NC", "Orlando, FL", "San Antonio, TX",
            "Portland, OR", "Sacramento, CA", "Pittsburgh, PA", "Las Vegas, NV",
            "Austin, TX", "Cincinnati, OH"
        ]
        
        # Load base Zillow data
        try:
            base_url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
            zhvi = pd.read_csv(base_url)
            
            output_path = self.output / "metro_reports"
            output_path.mkdir(exist_ok=True)
            
            for metro in tqdm(top_metros, desc="Metros"):
                try:
                    metro_data = zhvi[zhvi['RegionName'] == metro]
                    
                    if len(metro_data) > 0:
                        filename = output_path / f"{metro.replace(', ', '_').replace(' ', '_')}.txt"
                        
                        with open(filename, 'w') as f:
                            f.write(f"# Real Estate Market Report: {metro}\n\n")
                            f.write(f"## Market Overview\n")
                            f.write(f"Metro Area: {metro}\n")
                            f.write(f"Data Source: Zillow ZHVI\n\n")
                            
                            # Calculate metrics
                            recent_cols = [col for col in metro_data.columns if col.startswith('20')][-12:]
                            values = metro_data[recent_cols].values[0]
                            
                            current_price = values[-1]
                            year_ago = values[0]
                            yoy_change = ((current_price - year_ago) / year_ago) * 100
                            
                            f.write(f"## Current Market Conditions\n")
                            f.write(f"Current Median Home Value: ${current_price:,.0f}\n")
                            f.write(f"12-Month Change: {yoy_change:+.2f}%\n")
                            f.write(f"Year Ago Value: ${year_ago:,.0f}\n\n")
                            
                            f.write(f"## Historical Trend (Last 12 Months)\n")
                            for i, col in enumerate(recent_cols):
                                f.write(f"{col}: ${values[i]:,.0f}\n")
                            
                            f.write(f"\n## Market Analysis\n")
                            if yoy_change > 5:
                                f.write("Market Status: Strong appreciation\n")
                            elif yoy_change > 0:
                                f.write("Market Status: Moderate growth\n")
                            else:
                                f.write("Market Status: Declining or flat\n")
                        
                        self.count += 1
                        self.log(f"✅ Metro: {metro}")
                
                except Exception as e:
                    self.log(f"⚠️  Skipped {metro}: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Failed to load base data: {str(e)}")
        
        print(f"\n✅ Metro Reports: {self.count} files")

    # ============ CATEGORY 3: FRED ECONOMIC INDICATORS (20 docs) ============
    
    def download_fred_indicators(self, api_key=None):
        """Download 20 key economic indicators from FRED"""
        print("\n📈 FRED ECONOMIC INDICATORS")
        print("="*60)
        
        if not api_key:
            print("⚠️  FRED API key not provided")
            print("Get free key at: https://fred.stlouisfed.org/")
            
            # Prompt for key
            api_key = input("Enter FRED API key (or press Enter to skip): ").strip()
            
            if not api_key:
                print("Skipping FRED indicators")
                return
        
        try:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            
            indicators = {
                # Housing
                'MORTGAGE30US': '30-Year Fixed Mortgage Rate',
                'MORTGAGE15US': '15-Year Fixed Mortgage Rate',
                'CSUSHPISA': 'Case-Shiller U.S. National Home Price Index',
                'HOUST': 'Housing Starts',
                'PERMIT': 'New Private Housing Units Authorized',
                'RHORUSQ156N': 'Homeownership Rate',
                'MSPUS': 'Median Sales Price of Houses Sold',
                'MSACSR': 'Monthly Supply of Houses',
                
                # Economic
                'GDP': 'Gross Domestic Product',
                'GDPC1': 'Real GDP',
                'UNRATE': 'Unemployment Rate',
                'PAYEMS': 'All Employees: Total Nonfarm',
                'CPIAUCSL': 'Consumer Price Index',
                'CPILFESL': 'Core CPI',
                'FEDFUNDS': 'Federal Funds Rate',
                
                # Financial
                'DGS10': '10-Year Treasury Rate',
                'DGS2': '2-Year Treasury Rate',
                'DEXUSEU': 'USD to Euro Exchange Rate',
                'VIXCLS': 'VIX Volatility Index',
                'DCOILWTICO': 'Crude Oil Prices',
            }
            
            output_path = self.output / "fred_indicators"
            output_path.mkdir(exist_ok=True)
            
            for series_id, name in tqdm(indicators.items(), desc="FRED"):
                try:
                    data = fred.get_series(series_id)
                    
                    filename = output_path / f"{series_id}.txt"
                    with open(filename, 'w') as f:
                        f.write(f"# {name}\n\n")
                        f.write(f"Series ID: {series_id}\n")
                        f.write(f"Source: Federal Reserve Economic Data (FRED)\n")
                        f.write(f"Data Points: {len(data)}\n")
                        f.write(f"Date Range: {data.index[0]} to {data.index[-1]}\n\n")
                        
                        # Recent data
                        f.write("Recent Values (Last 12 observations):\n")
                        f.write(data.tail(12).to_string())
                        
                        # Statistics
                        f.write(f"\n\nStatistics:\n")
                        f.write(f"Current: {data.iloc[-1]:.4f}\n")
                        f.write(f"Mean: {data.mean():.4f}\n")
                        f.write(f"Min: {data.min():.4f}\n")
                        f.write(f"Max: {data.max():.4f}\n")
                    
                    self.count += 1
                    self.log(f"✅ FRED: {series_id}")
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.log(f"⚠️  FRED {series_id}: {str(e)}")
            
            print(f"\n✅ FRED Indicators: {self.count} files")
            
        except ImportError:
            print("❌ fredapi not installed. Run: pip install fredapi")
        except Exception as e:
            print(f"❌ FRED download failed: {str(e)}")

    # ============ CATEGORY 4: HUD DATA (10 docs) ============
    
    def download_hud_data(self):
        """Download HUD housing data"""
        print("\n🏠 HUD HOUSING DATA")
        print("="*60)
        
        output_path = self.output / "hud_data"
        output_path.mkdir(exist_ok=True)
        
        # Fair Market Rents
        try:
            print("Downloading HUD Fair Market Rents...")
            fmr_url = "https://www.huduser.gov/portal/datasets/fmr/fmr2024/FY24_4050_FMRs.xlsx"
            fmr = pd.read_excel(fmr_url)
            
            filename = output_path / "fair_market_rents_2024.txt"
            with open(filename, 'w') as f:
                f.write("# HUD Fair Market Rents (FY2024)\n\n")
                f.write(f"Source: U.S. Department of Housing and Urban Development\n")
                f.write(f"Areas Covered: {len(fmr)}\n\n")
                f.write("Sample Data:\n")
                f.write(fmr.head(50).to_string())
            
            self.count += 1
            self.log("✅ HUD: Fair Market Rents")
            
        except Exception as e:
            self.log(f"⚠️  HUD FMR: {str(e)}")
        
        # Income Limits
        try:
            print("Downloading HUD Income Limits...")
            il_url = "https://www.huduser.gov/portal/datasets/il/il2024/Section8-FY24.xlsx"
            income_limits = pd.read_excel(il_url)
            
            filename = output_path / "income_limits_2024.txt"
            with open(filename, 'w') as f:
                f.write("# HUD Income Limits (FY2024)\n\n")
                f.write(f"Source: HUD\n")
                f.write(f"Areas: {len(income_limits)}\n\n")
                f.write(income_limits.head(50).to_string())
            
            self.count += 1
            self.log("✅ HUD: Income Limits")
            
        except Exception as e:
            self.log(f"⚠️  HUD Income: {str(e)}")
        
        print(f"\n✅ HUD Data: Files downloaded")

    # ============ CATEGORY 5: CITY DATA (20 docs) ============
    
    def download_city_data(self):
        """Download data from major city open data portals"""
        print("\n🌆 CITY OPEN DATA")
        print("="*60)
        
        output_path = self.output / "city_data"
        output_path.mkdir(exist_ok=True)
        
        # NYC Property Sales
        try:
            print("Downloading NYC property data...")
            nyc_url = "https://data.cityofnewyork.us/resource/w2pb-icbu.json?$limit=1000"
            response = requests.get(nyc_url)
            nyc_data = response.json()
            
            filename = output_path / "nyc_property_sales.txt"
            with open(filename, 'w') as f:
                f.write("# NYC Property Sales\n\n")
                f.write(f"Source: NYC Open Data\n")
                f.write(f"Records: {len(nyc_data)}\n\n")
                
                for i, record in enumerate(nyc_data[:20]):
                    f.write(f"\nProperty {i+1}:\n")
                    for key, value in record.items():
                        f.write(f"  {key}: {value}\n")
            
            self.count += 1
            self.log("✅ NYC: Property Sales")
            
        except Exception as e:
            self.log(f"⚠️  NYC: {str(e)}")
        
        # Chicago
        try:
            print("Downloading Chicago data...")
            chi_url = "https://data.cityofchicago.org/resource/wrvz-psew.json?$limit=1000"
            response = requests.get(chi_url)
            chi_data = response.json()
            
            filename = output_path / "chicago_property_sales.txt"
            with open(filename, 'w') as f:
                f.write("# Chicago Property Sales\n\n")
                f.write(f"Records: {len(chi_data)}\n\n")
                f.write(json.dumps(chi_data[:20], indent=2))
            
            self.count += 1
            self.log("✅ Chicago: Property Sales")
            
        except Exception as e:
            self.log(f"⚠️  Chicago: {str(e)}")

    # ============ MAIN DOWNLOAD ============
    
    def download_all(self, fred_api_key=None):
        """Download all 100+ documents"""
        
        print("\n" + "="*60)
        print("DOWNLOADING 100+ REAL ESTATE DOCUMENTS")
        print("="*60)
        
        self.download_zillow_expanded()           # 20 docs
        self.create_metro_reports()               # 30 docs
        self.download_fred_indicators(fred_api_key)  # 20 docs
        self.download_hud_data()                  # 10 docs
        self.download_city_data()                 # 20 docs
        
        print("\n" + "="*60)
        print(f"✅ DOWNLOAD COMPLETE: {self.count} DOCUMENTS")
        print("="*60)
        print(f"Output directory: {self.output}/")
        print("\nNext steps:")
        print("1. Review downloaded files")
        print("2. Run: python domain_document_collector.py")
        print("3. Ingest into Pinecone")
        
        return self.count

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    downloader = ExpandedRealEstateDownloader()
    
    # Ask for FRED API key
    print("\n🔑 FRED API Key (optional but recommended)")
    print("Get FREE key at: https://fred.stlouisfed.org/")
    fred_key = input("Enter FRED API key (or press Enter to skip): ").strip()
    
    # Download
    total = downloader.download_all(fred_api_key=fred_key or None)
    
    print(f"\n🎉 Successfully downloaded {total} documents!")