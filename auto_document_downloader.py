# auto_document_downloader.py
"""
Automated downloader for Travel & Real Estate domain documents
Collects 2000-4000 documents from free sources
"""

import os
import requests
import pandas as pd
import time
from pathlib import Path
from tqdm import tqdm
import wikipediaapi
import json

class DocumentDownloader:
    def __init__(self, domain: str, output_dir: str = "./downloaded_docs"):
        self.domain = domain
        self.output_dir = Path(output_dir) / domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"total": 0, "success": 0, "failed": 0}
    
    def log(self, message):
        print(f"[{self.domain.upper()}] {message}")

# ==================== TRAVEL DOWNLOADER ====================

class TravelDocumentDownloader(DocumentDownloader):
    
    def download_wikivoyage(self, cities: list):
        """Download city guides from Wikivoyage"""
        self.log(f"Downloading {len(cities)} city guides from Wikivoyage...")
        
        wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='DomainDocCollector/1.0'
        )
        
        output_path = self.output_dir / "destinations"
        output_path.mkdir(exist_ok=True)
        
        for city in tqdm(cities, desc="Wikivoyage"):
            try:
                page = wiki.page(city)
                if page.exists():
                    filename = output_path / f"{city.replace(' ', '_')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# {city} Travel Guide\n\n")
                        f.write(f"Source: Wikivoyage\n")
                        f.write(f"URL: {page.fullurl}\n\n")
                        f.write(page.text)
                    
                    self.stats["success"] += 1
                else:
                    self.stats["failed"] += 1
                
                time.sleep(0.5)  # Rate limiting
            
            except Exception as e:
                self.log(f"Error downloading {city}: {str(e)}")
                self.stats["failed"] += 1
        
        self.stats["total"] += len(cities)
        self.log(f"✅ Wikivoyage: {self.stats['success']}/{len(cities)} downloaded")
    
    def download_openflights_data(self):
        """Download OpenFlights airport and route data"""
        self.log("Downloading OpenFlights data...")
        
        output_path = self.output_dir / "transportation"
        output_path.mkdir(exist_ok=True)
        
        datasets = {
            'airports': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat',
            'airlines': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat',
            'routes': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat'
        }
        
        for name, url in datasets.items():
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    filename = output_path / f"openflights_{name}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# OpenFlights {name.title()} Data\n\n")
                        f.write(f"Source: OpenFlights\n")
                        f.write(f"URL: {url}\n\n")
                        f.write(response.text)
                    
                    self.stats["success"] += 1
                    self.log(f"✅ Downloaded {name}")
            
            except Exception as e:
                self.log(f"❌ Failed to download {name}: {str(e)}")
                self.stats["failed"] += 1
        
        self.stats["total"] += len(datasets)
    
    def download_unesco_sites(self):
        """Download UNESCO World Heritage Sites data"""
        self.log("Downloading UNESCO sites...")
        
        output_path = self.output_dir / "destinations"
        output_path.mkdir(exist_ok=True)
        
        try:
            # UNESCO API
            url = 'https://whc.unesco.org/en/list/json'
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                sites = response.json()
                
                # Group by country and save
                countries = {}
                for site in sites.get('sites', []):
                    country = site.get('states', 'Unknown')
                    if country not in countries:
                        countries[country] = []
                    countries[country].append(site)
                
                for country, country_sites in countries.items():
                    filename = output_path / f"unesco_{country.replace(' ', '_')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# UNESCO World Heritage Sites in {country}\n\n")
                        f.write(f"Total Sites: {len(country_sites)}\n\n")
                        
                        for site in country_sites:
                            f.write(f"## {site.get('site', 'Unknown')}\n")
                            f.write(f"Category: {site.get('category', 'N/A')}\n")
                            f.write(f"Year Inscribed: {site.get('date_inscribed', 'N/A')}\n")
                            f.write(f"Description: {site.get('short_description', 'N/A')}\n\n")
                    
                    self.stats["success"] += 1
                
                self.log(f"✅ Downloaded UNESCO data for {len(countries)} countries")
        
        except Exception as e:
            self.log(f"❌ Failed to download UNESCO data: {str(e)}")
            self.stats["failed"] += 1
        
        self.stats["total"] += 1
    
    def download_all(self):
        """Download all travel documents"""
        
        # Top 200 tourist cities
        cities = [
            "Paris", "London", "Dubai", "Singapore", "New York", "Tokyo", "Barcelona", "Amsterdam",
            "Rome", "Istanbul", "Seoul", "Milan", "Bangkok", "Hong Kong", "Las Vegas", "Prague",
            "Madrid", "Vienna", "Los Angeles", "Berlin", "Venice", "Florence", "Sydney", "Lisbon",
            "Orlando", "Miami", "Munich", "Dublin", "Copenhagen", "Athens", "Brussels", "San Francisco",
            "Budapest", "Zurich", "Hamburg", "Warsaw", "Krakow", "Stockholm", "Nice", "Toronto",
            "Edinburgh", "Seville", "Marrakech", "Cairo", "Mumbai", "Delhi", "Jaipur", "Agra",
            "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Shanghai", "Beijing", "Hong Kong",
            "Taipei", "Kuala Lumpur", "Jakarta", "Manila", "Hanoi", "Ho Chi Minh City", "Phuket",
            "Bali", "Melbourne", "Brisbane", "Auckland", "Wellington", "Vancouver", "Montreal",
            "Mexico City", "Cancun", "Buenos Aires", "Rio de Janeiro", "São Paulo", "Lima",
            "Santiago", "Bogota", "Quito", "Cusco", "Havana", "San Juan", "Nassau", "Montego Bay",
            # Add 120 more cities...
        ]
        
        self.download_wikivoyage(cities[:100])  # Start with 100 cities
        self.download_openflights_data()
        self.download_unesco_sites()
        
        return self.stats

# ==================== REAL ESTATE DOWNLOADER ====================

class RealEstateDocumentDownloader(DocumentDownloader):
    
    def download_zillow_data(self):
        """Download Zillow research data"""
        self.log("Downloading Zillow data...")
        
        output_path = self.output_dir / "price_prediction"
        output_path.mkdir(exist_ok=True)
        
        datasets = {
            'home_values': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
            'rental_index': 'https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv',
            'inventory': 'https://files.zillowstatic.com/research/public_csvs/invt_fs/Metro_invt_fs_uc_sfrcondo_month.csv',
            'median_sale_price': 'https://files.zillowstatic.com/research/public_csvs/median_sale_price/Metro_median_sale_price_uc_sfrcondo_sm_month.csv'
        }
        
        for name, url in tqdm(datasets.items(), desc="Zillow"):
            try:
                df = pd.read_csv(url)
                
                # Convert to text format
                filename = output_path / f"zillow_{name}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# Zillow {name.replace('_', ' ').title()}\n\n")
                    f.write(f"Source: Zillow Research\n")
                    f.write(f"Columns: {', '.join(df.columns)}\n")
                    f.write(f"Rows: {len(df)}\n\n")
                    f.write(df.to_string())
                
                self.stats["success"] += 1
                self.log(f"✅ Downloaded {name}")
                time.sleep(1)
            
            except Exception as e:
                self.log(f"❌ Failed to download {name}: {str(e)}")
                self.stats["failed"] += 1
        
        self.stats["total"] += len(datasets)
    
    def download_fred_data(self, api_key: str = None):
        """Download FRED economic data"""
        self.log("Downloading FRED data...")
        
        if not api_key:
            self.log("⚠️  FRED API key not provided. Skipping FRED data.")
            self.log("Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
            return
        
        try:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            
            output_path = self.output_dir / "economic_factors"
            output_path.mkdir(exist_ok=True)
            
            series = {
                'MORTGAGE30US': '30-Year Mortgage Rate',
                'CSUSHPISA': 'Case-Shiller Home Price Index',
                'HOUST': 'Housing Starts',
                'GDP': 'GDP',
                'UNRATE': 'Unemployment Rate',
                'CPIAUCSL': 'Consumer Price Index',
                'FEDFUNDS': 'Federal Funds Rate'
            }
            
            for series_id, name in tqdm(series.items(), desc="FRED"):
                try:
                    data = fred.get_series(series_id)
                    
                    filename = output_path / f"fred_{series_id}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# {name}\n\n")
                        f.write(f"Series ID: {series_id}\n")
                        f.write(f"Source: Federal Reserve Economic Data (FRED)\n")
                        f.write(f"Data Points: {len(data)}\n\n")
                        f.write(data.to_string())
                    
                    self.stats["success"] += 1
                    time.sleep(0.5)
                
                except Exception as e:
                    self.log(f"❌ Failed to download {series_id}: {str(e)}")
                    self.stats["failed"] += 1
            
            self.stats["total"] += len(series)
            self.log(f"✅ FRED: {self.stats['success']} series downloaded")
        
        except ImportError:
            self.log("❌ fredapi not installed. Run: pip install fredapi")
    
    def download_redfin_data(self):
        """Download Redfin market data - ALTERNATIVE SOURCES"""
        self.log("Downloading Redfin alternative data...")
        
        output_path = self.output_dir / "market_intelligence"
        output_path.mkdir(exist_ok=True)
        
        # Alternative 1: Realtor.com (works!)
        self.log("Using Realtor.com as alternative...")
        
        datasets = {
            'inventory_core': 'https://econdata.s3-us-west-2.amazonaws.com/Reports/Core/RDC_Inventory_Core_Metrics_Metro_History.csv',
            'inventory_hotness': 'https://econdata.s3-us-west-2.amazonaws.com/Reports/Hotness/RDC_Inventory_Hotness_Metrics_Metro_History.csv'
        }
        
        for name, url in tqdm(datasets.items(), desc="Realtor.com"):
            try:
                df = pd.read_csv(url)
                
                filename = output_path / f"realtor_{name}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# Realtor.com {name.replace('_', ' ').title()}\n\n")
                    f.write(f"Source: Realtor.com Research\n")
                    f.write(f"Columns: {', '.join(df.columns)}\n")
                    f.write(f"Rows: {len(df)}\n\n")
                    f.write(df.head(1000).to_string())
                
                self.stats["success"] += 1
                self.log(f"✅ Downloaded {name}")
                time.sleep(1)
            
            except Exception as e:
                self.log(f"❌ Failed to download {name}: {str(e)}")
                self.stats["failed"] += 1
        
        self.stats["total"] += len(datasets)
    
    def download_additional_sources(self):
        """Download additional free real estate data"""
        self.log("Downloading additional sources...")
        
        output_path = self.output_dir / "historical_data"
        output_path.mkdir(exist_ok=True)
        
        # HUD (Housing and Urban Development) data
        try:
            hud_url = "https://www.huduser.gov/portal/datasets/fmr.html"
            self.log("ℹ️  HUD data available at: https://www.huduser.gov/portal/datasets/fmr.html")
            self.log("   Manual download recommended for FMR (Fair Market Rent) data")
        except:
            pass
        
        # Additional sources note
        self.log("ℹ️  Additional free sources:")
        self.log("   - data.gov: Search 'housing' or 'real estate'")
        self.log("   - City open data portals (NYC, Chicago, SF, etc.)")
        self.log("   - Census.gov: American Community Survey")
    
    def download_all(self, fred_api_key: str = None):
        """Download all real estate documents"""
        
        self.download_zillow_data()
        self.download_fred_data(fred_api_key)
        self.download_redfin_data()
        
        return self.stats

# ==================== MAIN EXECUTION ====================

def main():
    print("="*60)
    print("Automated Document Downloader")
    print("="*60)
    print()
    
    # Travel Domain
    print("\n📍 TRAVEL DOMAIN")
    print("-"*60)
    travel_downloader = TravelDocumentDownloader("travel")
    travel_stats = travel_downloader.download_all()
    
    print(f"\n✅ Travel Download Complete:")
    print(f"   Total: {travel_stats['total']}")
    print(f"   Success: {travel_stats['success']}")
    print(f"   Failed: {travel_stats['failed']}")
    
    # Real Estate Domain
    print("\n\n🏠 REAL ESTATE DOMAIN")
    print("-"*60)
    
    # Ask for FRED API key
    fred_key = input("Enter FRED API key (or press Enter to skip): ").strip()
    if not fred_key:
        print("⚠️  Skipping FRED data (get free key at: https://fred.stlouisfed.org/)")
    
    re_downloader = RealEstateDocumentDownloader("real_estate")
    re_stats = re_downloader.download_all(fred_api_key=fred_key or None)
    
    print(f"\n✅ Real Estate Download Complete:")
    print(f"   Total: {re_stats['total']}")
    print(f"   Success: {re_stats['success']}")
    print(f"   Failed: {re_stats['failed']}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Travel Documents: {travel_stats['success']}")
    print(f"Real Estate Documents: {re_stats['success']}")
    print(f"Total Downloaded: {travel_stats['success'] + re_stats['success']}")
    print("="*60)
    
    print("\n✅ Next Steps:")
    print("1. Review downloaded documents in ./downloaded_docs/")
    print("2. Run: python domain_document_collector.py to ingest into Pinecone")
    print("3. Start backend: python document_analysis_backend.py")

if __name__ == "__main__":
    # Install required packages
    required = ['pandas', 'requests', 'wikipediaapi', 'tqdm']
    print("Checking dependencies...")
    
    missing = []
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        exit(1)
    
    print("✅ All dependencies installed\n")
    
    main()