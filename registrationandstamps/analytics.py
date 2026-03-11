"""
Property Transaction Analytics
Generates price trends, volume trends, and locality rankings from scraped IGRS data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

class PropertyAnalytics:
    
    def __init__(self, data_path="data/"):
        """Initialize with path to scraped CSV files"""
        self.data_path = Path(data_path)
        self.df = None
        
    def load_data(self, batch_files=None):
        """Load and combine all batch CSV files"""
        if batch_files is None:
            # Load all batch files
            batch_files = list(self.data_path.glob("batch_*_results.csv"))
        
        if not batch_files:
            raise FileNotFoundError(f"No batch files found in {self.data_path}")
        
        dfs = []
        for file in batch_files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        self.df = pd.concat(dfs, ignore_index=True)
        
        # Ensure date parsing
        self.df["transaction_date"] = pd.to_datetime(self.df["transaction_date"], errors="coerce")
        
        # Remove duplicates based on document_number
        self.df = self.df.drop_duplicates(subset=["document_number"], keep="first")
        
        print(f"✅ Loaded {len(self.df)} unique transactions")
        return self.df
    
    def price_trends(self, group_by="quarter", property_type=None, village=None):
        """
        Calculate price trends over time
        
        Args:
            group_by: 'month', 'quarter', or 'year'
            property_type: Filter by property type (optional)
            village: Filter by village/locality (optional)
        
        Returns:
            DataFrame with price trends
        """
        df = self.df.copy()
        
        # Apply filters
        if property_type:
            df = df[df["property_type"] == property_type]
        if village:
            df = df[df["village"] == village]
        
        # Remove outliers (optional)
        df = df[df["price_per_sqft"].notna()]
        df = df[df["price_per_sqft"] > 0]
        
        # Group by time period
        time_col = f"year_{group_by}" if group_by in ["month", "quarter"] else "year"
        
        trends = df.groupby(time_col).agg({
            "price_per_sqft": ["mean", "median", "std", "count"],
            "sale_consideration_value": ["sum", "mean", "median"]
        }).reset_index()
        
        trends.columns = [
            "period",
            "avg_price_per_sqft",
            "median_price_per_sqft",
            "std_price_per_sqft",
            "transaction_count",
            "total_transaction_value",
            "avg_transaction_value",
            "median_transaction_value"
        ]
        
        # Calculate YoY growth
        trends["yoy_growth_pct"] = trends["avg_price_per_sqft"].pct_change(periods=4 if group_by == "quarter" else 12 if group_by == "month" else 1) * 100
        
        return trends
    
    def volume_trends(self, group_by="quarter", property_type=None):
        """
        Calculate transaction volume trends
        
        Returns:
            DataFrame with volume metrics
        """
        df = self.df.copy()
        
        if property_type:
            df = df[df["property_type"] == property_type]
        
        time_col = f"year_{group_by}" if group_by in ["month", "quarter"] else "year"
        
        volume = df.groupby(time_col).agg({
            "document_number": "count",
            "sale_consideration_value": "sum",
            "extent_area": "sum"
        }).reset_index()
        
        volume.columns = [
            "period",
            "total_registrations",
            "total_registered_value",
            "total_area_transacted"
        ]
        
        # Calculate growth rates
        volume["registration_growth_pct"] = volume["total_registrations"].pct_change() * 100
        volume["value_growth_pct"] = volume["total_registered_value"].pct_change() * 100
        
        return volume
    
    def locality_rankings(self, time_period=None, top_n=20):
        """
        Rank localities by price per sqft
        
        Args:
            time_period: Filter by specific period (e.g., "2024Q4")
            top_n: Number of top localities to return
        
        Returns:
            DataFrame with ranked localities
        """
        df = self.df.copy()
        
        if time_period:
            df = df[df["year_quarter"].astype(str) == time_period]
        
        # Remove invalid data
        df = df[df["price_per_sqft"].notna()]
        df = df[df["price_per_sqft"] > 0]
        
        rankings = df.groupby("village").agg({
            "price_per_sqft": ["mean", "median", "std"],
            "document_number": "count",
            "sale_consideration_value": "sum"
        }).reset_index()
        
        rankings.columns = [
            "locality",
            "avg_price_per_sqft",
            "median_price_per_sqft",
            "std_price_per_sqft",
            "transaction_count",
            "total_value"
        ]
        
        # Rank by average price
        rankings["rank"] = rankings["avg_price_per_sqft"].rank(ascending=False, method="dense")
        rankings = rankings.sort_values("rank")
        
        return rankings.head(top_n)
    
    def rank_movement(self, period1, period2):
        """
        Track how locality rankings changed between two periods
        
        Args:
            period1: Earlier period (e.g., "2023Q1")
            period2: Later period (e.g., "2024Q1")
        
        Returns:
            DataFrame showing rank changes
        """
        rank1 = self.locality_rankings(time_period=period1, top_n=50)
        rank2 = self.locality_rankings(time_period=period2, top_n=50)
        
        rank1 = rank1[["locality", "rank", "avg_price_per_sqft"]].rename(
            columns={"rank": "rank_period1", "avg_price_per_sqft": "price_period1"}
        )
        
        rank2 = rank2[["locality", "rank", "avg_price_per_sqft"]].rename(
            columns={"rank": "rank_period2", "avg_price_per_sqft": "price_period2"}
        )
        
        movement = pd.merge(rank1, rank2, on="locality", how="outer")
        movement["rank_change"] = movement["rank_period1"] - movement["rank_period2"]
        movement["price_change_pct"] = ((movement["price_period2"] - movement["price_period1"]) / movement["price_period1"]) * 100
        
        movement = movement.sort_values("rank_period2")
        
        return movement
    
    def property_type_analysis(self):
        """Analyze trends by property type"""
        analysis = self.df.groupby("property_type").agg({
            "document_number": "count",
            "sale_consideration_value": ["sum", "mean", "median"],
            "price_per_sqft": ["mean", "median"],
            "extent_area": "mean"
        }).reset_index()
        
        analysis.columns = [
            "property_type",
            "total_transactions",
            "total_value",
            "avg_value",
            "median_value",
            "avg_price_per_sqft",
            "median_price_per_sqft",
            "avg_area"
        ]
        
        analysis = analysis.sort_values("total_transactions", ascending=False)
        
        return analysis
    
    def export_trends_json(self, output_file="trends_data.json"):
        """Export all trends to JSON for frontend consumption"""
        
        data = {
            "price_trends": {
                "quarterly": self.price_trends(group_by="quarter").to_dict(orient="records"),
                "monthly": self.price_trends(group_by="month").to_dict(orient="records"),
                "yearly": self.price_trends(group_by="year").to_dict(orient="records")
            },
            "volume_trends": {
                "quarterly": self.volume_trends(group_by="quarter").to_dict(orient="records"),
                "monthly": self.volume_trends(group_by="month").to_dict(orient="records")
            },
            "locality_rankings": {
                "current": self.locality_rankings(top_n=30).to_dict(orient="records"),
                "by_quarter": {}
            },
            "property_type_analysis": self.property_type_analysis().to_dict(orient="records"),
            "summary_stats": {
                "total_transactions": int(len(self.df)),
                "total_value": float(self.df["sale_consideration_value"].sum()),
                "avg_price_per_sqft": float(self.df["price_per_sqft"].mean()),
                "date_range": {
                    "start": str(self.df["transaction_date"].min()),
                    "end": str(self.df["transaction_date"].max())
                }
            }
        }
        
        # Add quarterly rankings
        quarters = self.df["year_quarter"].dropna().unique()
        for quarter in sorted(quarters, reverse=True)[:8]:  # Last 8 quarters
            data["locality_rankings"]["by_quarter"][str(quarter)] = \
                self.locality_rankings(time_period=str(quarter), top_n=20).to_dict(orient="records")
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Exported trends to {output_file}")
        return data
    
    def generate_report(self):
        """Generate a comprehensive text report"""
        print("\n" + "="*80)
        print("PROPERTY TRANSACTION ANALYTICS REPORT")
        print("="*80)
        
        print(f"\n📊 Dataset Overview:")
        print(f"   Total Transactions: {len(self.df):,}")
        print(f"   Date Range: {self.df['transaction_date'].min()} to {self.df['transaction_date'].max()}")
        print(f"   Total Value: ₹{self.df['sale_consideration_value'].sum():,.0f}")
        
        print(f"\n💰 Price Metrics:")
        print(f"   Average Price/Sqft: ₹{self.df['price_per_sqft'].mean():,.0f}")
        print(f"   Median Price/Sqft: ₹{self.df['price_per_sqft'].median():,.0f}")
        
        print(f"\n🏘️  Top 10 Localities by Price:")
        top_localities = self.locality_rankings(top_n=10)
        for idx, row in top_localities.iterrows():
            print(f"   {int(row['rank'])}. {row['locality']}: ₹{row['avg_price_per_sqft']:,.0f}/sqft ({int(row['transaction_count'])} transactions)")
        
        print(f"\n🏗️  Property Type Distribution:")
        prop_analysis = self.property_type_analysis()
        for idx, row in prop_analysis.iterrows():
            print(f"   {row['property_type']}: {int(row['total_transactions'])} transactions, Avg ₹{row['avg_price_per_sqft']:,.0f}/sqft")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    # Example usage
    analytics = PropertyAnalytics(data_path="data/")
    
    # Load data
    analytics.load_data()
    
    # Generate report
    analytics.generate_report()
    
    # Export trends for frontend
    analytics.export_trends_json("frontend/data/trends_data.json")
    
    # Get specific analyses
    quarterly_trends = analytics.price_trends(group_by="quarter")
    print("\n📈 Quarterly Price Trends:")
    print(quarterly_trends.tail(8))
    
    volume = analytics.volume_trends(group_by="quarter")
    print("\n📊 Quarterly Volume Trends:")
    print(volume.tail(8))
