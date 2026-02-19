#!/usr/bin/env python3
"""
Chicago Data Analysis Project
=============================
This script analyzes three Chicago datasets using SQL queries.
It loads data from CSV files into a SQLite database and answers 10 analytical questions.

Datasets:
1. Chicago Census Data (Socioeconomic Indicators)
2. Chicago Public Schools Progress Report
3. Chicago Crime Data (2001-Present)

Author: Data Analysis Project
"""

import pandas as pd
import sqlite3
from sqlite3 import Error
import os
import ssl
import urllib.request


class ChicagoDataAnalysis:
    """Handle Chicago data loading and SQL analysis."""
    
    def __init__(self, db_name="FinalDB.db"):
        """Initialize the database connection."""
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        
        # Handle SSL certificate verification
        self._setup_ssl_context()
        
    def _setup_ssl_context(self):
        """Setup SSL context to handle certificate verification."""
        try:
            import ssl
            # Create an SSL context that doesn't verify certificates
            # (Note: Only for trusted sources like IBM Cloud)
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        except Exception as e:
            print(f"Warning: Could not setup SSL context: {e}")
            self.ssl_context = None
        
    def connect_db(self):
        """Establish connection to SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {self.db_name}")
        except Error as e:
            print(f"✗ Error connecting to database: {e}")
            
    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print(f"✓ Database connection closed")
            
    def load_data_from_urls(self):
        """Load datasets from URLs and create database tables."""
        print("\n" + "="*70)
        print("LOADING DATASETS")
        print("="*70)
        
        # Dataset URLs
        census_url = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DB0201EN-SkillsNetwork/labs/FinalModule_Coursera_V5/data/ChicagoCensusData.csv"
        schools_url = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DB0201EN-SkillsNetwork/labs/FinalModule_Coursera_V5/data/ChicagoPublicSchools.csv"
        crime_url = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DB0201EN-SkillsNetwork/labs/FinalModule_Coursera_V5/data/ChicagoCrimeData.csv"
        
        try:
            # Load Census Data
            print("\n→ Loading Chicago Census Data...")
            census_df = pd.read_csv(census_url, on_bad_lines='skip')
            print(f"  ✓ Loaded {len(census_df)} records")
            
            # Load Schools Data
            print("→ Loading Chicago Public Schools Data...")
            schools_df = pd.read_csv(schools_url, on_bad_lines='skip')
            print(f"  ✓ Loaded {len(schools_df)} records")
            
            # Load Crime Data
            print("→ Loading Chicago Crime Data...")
            crime_df = pd.read_csv(crime_url, on_bad_lines='skip')
            print(f"  ✓ Loaded {len(crime_df)} records")
            
            # Store dataframes to database
            self.store_data_to_db(census_df, schools_df, crime_df)
            
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            print("  Trying alternative method with SSL bypass...")
            try:
                # Try with SSL context bypass
                import urllib.request
                import ssl
                
                # Create an SSL context that doesn't verify certificates
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Load with SSL bypass
                print("\n→ Loading Chicago Census Data (SSL bypass)...")
                with urllib.request.urlopen(census_url, context=ssl_context) as response:
                    census_df = pd.read_csv(response, on_bad_lines='skip')
                print(f"  ✓ Loaded {len(census_df)} records")
                
                print("→ Loading Chicago Public Schools Data (SSL bypass)...")
                with urllib.request.urlopen(schools_url, context=ssl_context) as response:
                    schools_df = pd.read_csv(response, on_bad_lines='skip')
                print(f"  ✓ Loaded {len(schools_df)} records")
                
                print("→ Loading Chicago Crime Data (SSL bypass)...")
                with urllib.request.urlopen(crime_url, context=ssl_context) as response:
                    crime_df = pd.read_csv(response, on_bad_lines='skip')
                print(f"  ✓ Loaded {len(crime_df)} records")
                
                # Store dataframes to database
                self.store_data_to_db(census_df, schools_df, crime_df)
                
            except Exception as e2:
                print(f"✗ Error with SSL bypass: {e2}")
            
    def store_data_to_db(self, census_df, schools_df, crime_df):
        """Store dataframes into SQLite database tables."""
        print("\n→ Creating database tables...")
        
        try:
            # Store Census Data
            census_df.to_sql("CENSUS_DATA", self.conn, if_exists="replace", index=False)
            print("  ✓ Created CENSUS_DATA table")
            
            # Store Schools Data
            schools_df.to_sql("CHICAGO_PUBLIC_SCHOOLS", self.conn, if_exists="replace", index=False)
            print("  ✓ Created CHICAGO_PUBLIC_SCHOOLS table")
            
            # Store Crime Data
            crime_df.to_sql("CHICAGO_CRIME_DATA", self.conn, if_exists="replace", index=False)
            print("  ✓ Created CHICAGO_CRIME_DATA table")
            
            self.conn.commit()
            print("\n✓ All tables created successfully!")
            
        except Error as e:
            print(f"✗ Error storing data: {e}")
            
    def execute_query(self, query_num, query):
        """Execute a single SQL query and display results."""
        try:
            result = pd.read_sql_query(query, self.conn)
            return result
        except Error as e:
            print(f"✗ Error executing query {query_num}: {e}")
            return None
            
    def display_results(self, problem_num, title, result):
        """Display query results in a formatted manner."""
        print("\n" + "="*70)
        print(f"PROBLEM {problem_num}: {title}")
        print("="*70)
        if result is not None and not result.empty:
            print(result.to_string(index=False))
            print(f"\n  → Total records: {len(result)}")
        else:
            print("No results found or error occurred.")
            
    def run_analysis(self):
        """Run all 10 analysis problems."""
        print("\n" + "="*70)
        print("RUNNING SQL ANALYSIS PROBLEMS")
        print("="*70)
        
        # Problem 1: Total number of crimes
        query1 = """
        SELECT COUNT(*) as TOTAL_CRIMES
        FROM CHICAGO_CRIME_DATA;
        """
        result1 = self.execute_query(1, query1)
        self.display_results(1, "Find the total number of crimes recorded", result1)
        
        # Problem 2: Community areas with per capita income < 11000
        query2 = """
        SELECT COMMUNITY_AREA_NUMBER, COMMUNITY_AREA_NAME, PER_CAPITA_INCOME
        FROM CENSUS_DATA
        WHERE PER_CAPITA_INCOME < 11000
        ORDER BY PER_CAPITA_INCOME DESC;
        """
        result2 = self.execute_query(2, query2)
        self.display_results(2, "Community areas with per capita income < $11,000", result2)
        
        # Problem 3: Case numbers for crimes involving minors
        query3 = """
        SELECT DISTINCT CASE_NUMBER
        FROM CHICAGO_CRIME_DATA
        WHERE DESCRIPTION LIKE '%MINOR%'
        ORDER BY CASE_NUMBER;
        """
        result3 = self.execute_query(3, query3)
        self.display_results(3, "Crime case numbers involving minors", result3)
        
        # Problem 4: Kidnapping crimes involving a child
        query4 = """
        SELECT CASE_NUMBER, ID, DESCRIPTION
        FROM CHICAGO_CRIME_DATA
        WHERE PRIMARY_TYPE = 'KIDNAPPING'
        AND DESCRIPTION LIKE '%CHILD%'
        ORDER BY CASE_NUMBER;
        """
        result4 = self.execute_query(4, query4)
        self.display_results(4, "Kidnapping crimes involving a child", result4)
        
        # Problem 5: Types of crimes at schools (no repetitions)
        query5 = """
        SELECT DISTINCT PRIMARY_TYPE
        FROM CHICAGO_CRIME_DATA
        WHERE LOCATION_DESCRIPTION LIKE '%SCHOOL%'
        ORDER BY PRIMARY_TYPE;
        """
        result5 = self.execute_query(5, query5)
        self.display_results(5, "Types of crimes recorded at schools", result5)
        
        # Problem 6: Type of schools and average safety score
        query6 = """
        SELECT "Elementary, Middle, or High School" as SCHOOL_TYPE, AVG(SAFETY_SCORE) as AVG_SAFETY_SCORE
        FROM CHICAGO_PUBLIC_SCHOOLS
        WHERE SAFETY_SCORE IS NOT NULL
        GROUP BY "Elementary, Middle, or High School"
        ORDER BY AVG_SAFETY_SCORE DESC;
        """
        result6 = self.execute_query(6, query6)
        self.display_results(6, "School types with average safety scores", result6)
        
        # Problem 7: Top 5 community areas with highest poverty percentage
        query7 = """
        SELECT COMMUNITY_AREA_NUMBER, COMMUNITY_AREA_NAME, PERCENT_HOUSEHOLDS_BELOW_POVERTY
        FROM CENSUS_DATA
        ORDER BY PERCENT_HOUSEHOLDS_BELOW_POVERTY DESC
        LIMIT 5;
        """
        result7 = self.execute_query(7, query7)
        self.display_results(7, "Top 5 community areas with highest poverty rate", result7)
        
        # Problem 8: Most crime-prone community area
        query8 = """
        SELECT COMMUNITY_AREA_NUMBER, COUNT(*) as CRIME_COUNT
        FROM CHICAGO_CRIME_DATA
        WHERE COMMUNITY_AREA_NUMBER IS NOT NULL
        GROUP BY COMMUNITY_AREA_NUMBER
        ORDER BY CRIME_COUNT DESC
        LIMIT 1;
        """
        result8 = self.execute_query(8, query8)
        self.display_results(8, "Most crime-prone community area", result8)
        
        # Problem 9: Community area with highest hardship index (using subquery)
        query9 = """
        SELECT COMMUNITY_AREA_NAME
        FROM CENSUS_DATA
        WHERE HARDSHIP_INDEX = (
            SELECT MAX(HARDSHIP_INDEX)
            FROM CENSUS_DATA
        );
        """
        result9 = self.execute_query(9, query9)
        self.display_results(9, "Community area with highest hardship index (subquery)", result9)
        
        # Problem 10: Community area with most crimes (using subquery)
        query10 = """
        SELECT COMMUNITY_AREA_NAME
        FROM CENSUS_DATA
        WHERE COMMUNITY_AREA_NUMBER = (
            SELECT COMMUNITY_AREA_NUMBER
            FROM CHICAGO_CRIME_DATA
            WHERE COMMUNITY_AREA_NUMBER IS NOT NULL
            GROUP BY COMMUNITY_AREA_NUMBER
            ORDER BY COUNT(*) DESC
            LIMIT 1
        );
        """
        result10 = self.execute_query(10, query10)
        self.display_results(10, "Community area with most crimes (subquery)", result10)
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70 + "\n")


def main():
    """Main execution function."""
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║          CHICAGO DATA ANALYSIS - SQL PROJECT                      ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Initialize analysis
    analyzer = ChicagoDataAnalysis()
    analyzer.connect_db()
    
    # Load data and create tables
    analyzer.load_data_from_urls()
    
    # Run analysis
    analyzer.run_analysis()
    
    # Close connection
    analyzer.close_db()
    
    print("✓ Project completed successfully!")


if __name__ == "__main__":
    main()
