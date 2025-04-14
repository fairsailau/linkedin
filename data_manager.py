import pandas as pd
import os
import json
import logging
from datetime import datetime

class DataManager:
    """
    Class to handle data processing, cleaning, and storage for LinkedIn leads
    """
    
    def __init__(self, storage_type="file", db_path=None, data_dir="data"):
        """
        Initialize the DataManager
        
        Args:
            storage_type (str): Type of storage to use ('file' or 'database')
            db_path (str): Path to the database file (if storage_type is 'database')
            data_dir (str): Directory to store data files (if storage_type is 'file')
        """
        self.storage_type = storage_type
        self.db_path = db_path or "linkedin_leads.db"
        self.data_dir = data_dir
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('DataManager')
        
        # Create data directory if it doesn't exist
        if storage_type == "file" and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            self.logger.info(f"Created data directory: {data_dir}")
    
    def clean_data(self, leads_df):
        """
        Clean and normalize the leads data
        
        Args:
            leads_df (DataFrame): DataFrame containing leads data
            
        Returns:
            DataFrame: Cleaned and normalized DataFrame
        """
        if leads_df.empty:
            return leads_df
        
        # Make a copy to avoid modifying the original
        df = leads_df.copy()
        
        # Fill missing values
        df['name'] = df['name'].fillna('Unknown')
        df['title'] = df['title'].fillna('Unknown')
        df['company'] = df['company'].fillna('Unknown')
        df['location'] = df['location'].fillna('Unknown')
        df['industry'] = df['industry'].fillna('Unknown')
        df['company_size'] = df['company_size'].fillna('Unknown')
        df['connections'] = df['connections'].fillna('Unknown')
        df['profile_url'] = df['profile_url'].fillna('')
        
        # Ensure is_qualified column exists and is boolean
        if 'is_qualified' not in df.columns:
            df['is_qualified'] = False
        else:
            df['is_qualified'] = df['is_qualified'].fillna(False).astype(bool)
        
        # Ensure notes column exists
        if 'notes' not in df.columns:
            df['notes'] = ''
        
        # Remove duplicates based on profile_url
        df = df.drop_duplicates(subset=['profile_url'], keep='first')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        self.logger.info(f"Cleaned data: {len(df)} leads after cleaning")
        return df
    
    def save_leads(self, leads_df):
        """
        Save leads data to storage
        
        Args:
            leads_df (DataFrame): DataFrame containing leads data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if leads_df.empty:
            self.logger.warning("No leads to save")
            return True
        
        try:
            if self.storage_type == "file":
                # Save to CSV file
                file_path = os.path.join(self.data_dir, "leads.csv")
                leads_df.to_csv(file_path, index=False)
                self.logger.info(f"Saved {len(leads_df)} leads to {file_path}")
                return True
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Save to database
                leads_df.to_sql("leads", conn, if_exists="replace", index=False)
                
                # Close connection
                conn.close()
                
                self.logger.info(f"Saved {len(leads_df)} leads to database {self.db_path}")
                return True
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return False
        except Exception as e:
            self.logger.error(f"Error saving leads: {str(e)}")
            return False
    
    def load_leads(self):
        """
        Load leads data from storage
        
        Returns:
            DataFrame: DataFrame containing leads data
        """
        try:
            if self.storage_type == "file":
                # Load from CSV file
                file_path = os.path.join(self.data_dir, "leads.csv")
                if os.path.exists(file_path):
                    leads_df = pd.read_csv(file_path)
                    self.logger.info(f"Loaded {len(leads_df)} leads from {file_path}")
                    return leads_df
                else:
                    self.logger.warning(f"Leads file not found: {file_path}")
                    return pd.DataFrame()
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Check if table exists
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
                if cursor.fetchone():
                    # Load from database
                    leads_df = pd.read_sql("SELECT * FROM leads", conn)
                    
                    # Close connection
                    conn.close()
                    
                    self.logger.info(f"Loaded {len(leads_df)} leads from database {self.db_path}")
                    return leads_df
                else:
                    # Close connection
                    conn.close()
                    
                    self.logger.warning(f"Leads table not found in database {self.db_path}")
                    return pd.DataFrame()
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error loading leads: {str(e)}")
            return pd.DataFrame()
    
    def save_search_history(self, search_history):
        """
        Save search history to storage
        
        Args:
            search_history (list): List of search history entries
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.storage_type == "file":
                # Save to JSON file
                file_path = os.path.join(self.data_dir, "search_history.json")
                with open(file_path, "w") as f:
                    json.dump(search_history, f)
                
                self.logger.info(f"Saved {len(search_history)} search history entries to {file_path}")
                return True
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Create table if it doesn't exist
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keywords TEXT,
                    location TEXT,
                    date TEXT,
                    results INTEGER
                )
                """)
                
                # Clear existing data
                cursor.execute("DELETE FROM search_history")
                
                # Insert new data
                for entry in search_history:
                    cursor.execute(
                        "INSERT INTO search_history (keywords, location, date, results) VALUES (?, ?, ?, ?)",
                        (entry["keywords"], entry["location"], entry["date"], entry["results"])
                    )
                
                # Commit changes
                conn.commit()
                
                # Close connection
                conn.close()
                
                self.logger.info(f"Saved {len(search_history)} search history entries to database {self.db_path}")
                return True
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return False
        except Exception as e:
            self.logger.error(f"Error saving search history: {str(e)}")
            return False
    
    def load_search_history(self):
        """
        Load search history from storage
        
        Returns:
            list: List of search history entries
        """
        try:
            if self.storage_type == "file":
                # Load from JSON file
                file_path = os.path.join(self.data_dir, "search_history.json")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        search_history = json.load(f)
                    
                    self.logger.info(f"Loaded {len(search_history)} search history entries from {file_path}")
                    return search_history
                else:
                    self.logger.warning(f"Search history file not found: {file_path}")
                    return []
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Check if table exists
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_history'")
                if cursor.fetchone():
                    # Load from database
                    cursor.execute("SELECT keywords, location, date, results FROM search_history")
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    search_history = [
                        {
                            "keywords": row[0],
                            "location": row[1],
                            "date": row[2],
                            "results": row[3]
                        }
                        for row in rows
                    ]
                    
                    # Close connection
                    conn.close()
                    
                    self.logger.info(f"Loaded {len(search_history)} search history entries from database {self.db_path}")
                    return search_history
                else:
                    # Close connection
                    conn.close()
                    
                    self.logger.warning(f"Search history table not found in database {self.db_path}")
                    return []
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return []
        except Exception as e:
            self.logger.error(f"Error loading search history: {str(e)}")
            return []
    
    def save_filters(self, filters):
        """
        Save filters to storage
        
        Args:
            filters (list): List of filter dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.storage_type == "file":
                # Save to JSON file
                file_path = os.path.join(self.data_dir, "filters.json")
                with open(file_path, "w") as f:
                    json.dump(filters, f)
                
                self.logger.info(f"Saved {len(filters)} filters to {file_path}")
                return True
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Create table if it doesn't exist
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS filters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_data TEXT
                )
                """)
                
                # Clear existing data
                cursor.execute("DELETE FROM filters")
                
                # Insert new data
                for filter_item in filters:
                    cursor.execute(
                        "INSERT INTO filters (filter_data) VALUES (?)",
                        (json.dumps(filter_item),)
                    )
                
                # Commit changes
                conn.commit()
                
                # Close connection
                conn.close()
                
                self.logger.info(f"Saved {len(filters)} filters to database {self.db_path}")
                return True
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return False
        except Exception as e:
            self.logger.error(f"Error saving filters: {str(e)}")
            return False
    
    def load_filters(self):
        """
        Load filters from storage
        
        Returns:
            list: List of filter dictionaries
        """
        try:
            if self.storage_type == "file":
                # Load from JSON file
                file_path = os.path.join(self.data_dir, "filters.json")
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        filters = json.load(f)
                    
                    self.logger.info(f"Loaded {len(filters)} filters from {file_path}")
                    return filters
                else:
                    self.logger.warning(f"Filters file not found: {file_path}")
                    return []
            elif self.storage_type == "database":
                # Import SQLite
                import sqlite3
                
                # Connect to database
                conn = sqlite3.connect(self.db_path)
                
                # Check if table exists
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filters'")
                if cursor.fetchone():
                    # Load from database
                    cursor.execute("SELECT filter_data FROM filters")
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    filters = [json.loads(row[0]) for row in rows]
                    
                    # Close connection
                    conn.close()
                    
                    self.logger.info(f"Loaded {len(filters)} filters from database {self.db_path}")
                    return filters
                else:
                    # Close connection
                    conn.close()
                    
                    self.logger.warning(f"Filters table not found in database {self.db_path}")
                    return []
            else:
                self.logger.error(f"Unsupported storage type: {self.storage_type}")
                return []
        except Exception as e:
            self.logger.error(f"Error loading filters: {str(e)}")
            return []
    
    def export_leads(self, leads_df, format="csv", output_dir=None):
        """
        Export leads to a file in the specified format
        
        Args:
            leads_df (DataFrame): DataFrame containing leads data
            format (str): Export format ('csv', 'excel', or 'json')
            output_dir (str): Directory to save the exported file (defaults to data_dir)
            
        Returns:
            str: Path to the exported file, or None if export failed
        """
        if leads_df.empty:
            self.logger.warning("No leads to export")
            return None
        
        # Use data_dir if output_dir is not specified
        output_dir = output_dir or self.data_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if format.lower() == "csv":
                # Export to CSV
                file_path = os.path.join(output_dir, f"linkedin_leads_{timestamp}.csv")
                leads_df.to_csv(file_path, index=False)
                self.logger.info(f"Exported {len(leads_df)} leads to CSV: {file_path}")
                return file_path
            elif format.lower() == "excel":
                # Export to Excel
                file_path = os.path.join(output_dir, f"linkedin_leads_{timestamp}.xlsx")
                leads_df.to_excel(file_path, index=False)
                self.logger.info(f"Exported {len(leads_df)} leads to Excel: {file_path}")
                return file_path
            elif format.lower() == "json":
                # Export to JSON
                file_path = os.path.join(output_dir, f"linkedin_leads_{timestamp}.json")
                leads_df.to_json(file_path, orient="records", indent=4)
                self.logger.info(f"Exported {len(leads_df)} leads to JSON: {file_path}")
                return file_path
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return None
        except Exception as e:
            self.logger.error(f"Error exporting leads: {str(e)}")
            return None
    
    def get_lead_statistics(self, leads_df):
        """
        Calculate statistics for the leads data
        
        Args:
            leads_df (DataFrame): DataFrame containing leads data
            
        Returns:
            dict: Dictionary containing statistics
        """
        if leads_df.empty:
            return {
                'total_leads': 0,
                'qualified_leads': 0,
                'qualification_rate': 0,
                'top_companies': {},
                'top_titles': {},
                'top_locations': {},
                'connections_distribution': {}
            }
        
        # Calculate basic statistics
        total_leads = len(leads_df)
        qualified_leads = len(leads_df[leads_df['is_qualified'] == True])
        qualification_rate = round((qualified_leads / total_leads) * 100, 2) if total_leads > 0 else 0
        
        # Calculate top companies
        top_companies = leads_df['company'].value_counts().head(5).to_dict()
        
        # Calculate top titles
        top_titles = leads_df['title'].value_counts().head(5).to_dict()
        
        # Calculate top locations
        top_locations = leads_df['location'].value_counts().head(5).to_dict()
        
        # Calculate connections distribution
        connections_distribution = leads_df['connections'].value_counts().to_dict()
        
        return {
            'total_leads': total_leads,
            'qualified_leads': qualified_leads,
            'qualification_rate': qualification_rate,
            'top_companies': top_companies,
            'top_titles': top_titles,
            'top_locations': top_locations,
            'connections_distribution': connections_distribution
        }
