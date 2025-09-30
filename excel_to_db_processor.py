import pandas as pd
import duckdb
import numpy as np
import json
from typing import List, Dict, Set
import os
from datetime import datetime
from config import Config
import google.generativeai as genai

class ExcelToDBProcessor:
    def __init__(self):
        self.db_file = Config.DB_FILE
        # Initialize Gemini AI
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.embed_content(model="models/embedding-001", task_type="retrieval_document")
        self.con = None
        self.setup_database()

    def setup_database(self):
        """Setup DuckDB database and create incidents table if it doesn't exist"""
        try:
            # Connect to database in read-write mode
            self.con = duckdb.connect(database=self.db_file, read_only=False)

            # Create incidents table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS incidents (
                INC VARCHAR PRIMARY KEY,
                "Short Desc" TEXT,
                "Created Date" TIMESTAMP,
                "Updated Date" TIMESTAMP,
                Assignee VARCHAR,
                "Group" VARCHAR,
                "Created By" VARCHAR,
                "Updated By " VARCHAR,
                vector FLOAT[],
                json_file_path VARCHAR
            )
            """
            self.con.execute(create_table_sql)
            print("✅ Database setup completed")

        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            raise

    def read_excel_file(self, excel_path: str) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Excel file not found: {excel_path}")

            df = pd.read_excel(excel_path)
            print(f"✅ Successfully read Excel file with {len(df)} rows")
            return df

        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            raise

    def convert_to_json(self, df: pd.DataFrame, json_dir: str):
        """Convert DataFrame to individual JSON files for each INC record"""
        try:
            # Ensure JSON directory exists
            os.makedirs(json_dir, exist_ok=True)

            json_files_created = []

            for _, row in df.iterrows():
                inc_number = str(row.get('INC', ''))

                # Skip if INC is empty or None
                if not inc_number or inc_number == 'nan':
                    continue

                # Create individual JSON data for this record
                record_data = {
                    'INC': inc_number,
                    'Short Desc': str(row.get('Short Desc', '')),
                    'Created Date': pd.to_datetime(row.get('Created Date', None)).isoformat() if row.get('Created Date') else None,
                    'Updated Date': pd.to_datetime(row.get('Updated Date', None)).isoformat() if row.get('Updated Date') else None,
                    'Assignee': str(row.get('Assignee', '')),
                    'Group': str(row.get('Group', '')),
                    'Created By': str(row.get('Created By', '')),
                    'Updated By ': str(row.get('Updated By ', ''))
                }

                # Create JSON file path for this INC
                json_file_path = os.path.join(json_dir, f"{inc_number}.json")

                # Write individual JSON file
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(record_data, f, indent=2, ensure_ascii=False)

                json_files_created.append(json_file_path)
                print(f"✅ Created JSON file: {json_file_path}")

            print(f"✅ Created {len(json_files_created)} individual JSON files")
            return json_files_created

        except Exception as e:
            print(f"❌ Error creating JSON files: {e}")
            raise

    def get_existing_incidents(self) -> Set[str]:
        """Get set of existing INC numbers from database"""
        try:
            result = self.con.execute("SELECT INC FROM incidents").fetchall()
            existing_incs = {row[0] for row in result}
            print(f"✅ Found {len(existing_incs)} existing incidents in database")
            return existing_incs

        except Exception as e:
            print(f"❌ Error fetching existing incidents: {e}")
            return set()

    def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text using Gemini"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return []

    def prepare_incident_data(self, df: pd.DataFrame, json_dir: str) -> List[Dict]:
        """Prepare incident data with embeddings and JSON file paths"""
        existing_incs = self.get_existing_incidents()
        new_incidents = []

        for _, row in df.iterrows():
            inc_number = str(row.get('INC', ''))

            # Skip if INC already exists
            if inc_number in existing_incs:
                print(f"⏭️  Skipping existing INC: {inc_number}")
                continue

            # Skip if INC is empty or None
            if not inc_number or inc_number == 'nan':
                continue

            # Create JSON file path for this INC
            json_file_path = os.path.join(json_dir, f"{inc_number}.json")

            # Prepare incident data
            incident = {
                'INC': inc_number,
                'Short Desc': str(row.get('Short Desc', '')),
                'Created Date': pd.to_datetime(row.get('Created Date', None)).isoformat() if row.get('Created Date') else None,
                'Updated Date': pd.to_datetime(row.get('Updated Date', None)).isoformat() if row.get('Updated Date') else None,
                'Assignee': str(row.get('Assignee', '')),
                'Group': str(row.get('Group', '')),
                'Created By': str(row.get('Created By', '')),
                'Updated By ': str(row.get('Updated By ', '')),
                'json_file_path': json_file_path
            }

            # Generate embedding for short description
            short_desc = incident['Short Desc']
            if short_desc:
                incident['vector'] = self.generate_embedding(short_desc)
            else:
                incident['vector'] = []

            new_incidents.append(incident)

        print(f"✅ Prepared {len(new_incidents)} new incidents for insertion")
        return new_incidents

    def insert_incidents(self, incidents: List[Dict]):
        """Insert incidents into database"""
        if not incidents:
            print("ℹ️  No new incidents to insert")
            return

        try:
            # Insert incidents in batches
            batch_size = 100
            total_inserted = 0

            for i in range(0, len(incidents), batch_size):
                batch = incidents[i:i + batch_size]

                # Prepare values for batch insert
                values = []
                for incident in batch:
                    values.append((
                        incident['INC'],
                        incident['Short Desc'],
                        incident['Created Date'],
                        incident['Updated Date'],
                        incident['Assignee'],
                        incident['Group'],
                        incident['Created By'],
                        incident['Updated By '],
                        incident['vector'],
                        incident['json_file_path']
                    ))

                # Insert batch
                self.con.executemany("""
                    INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, values)

                total_inserted += len(batch)
                print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} incidents")

            print(f"✅ Successfully inserted {total_inserted} new incidents into database")

        except Exception as e:
            print(f"❌ Error inserting incidents: {e}")
            raise

    def process_excel_to_db(self, excel_path: str, json_dir: str = None):
        """Main function to process Excel file and store in database"""
        try:
            print(f"🚀 Starting Excel to Database processing...")
            print(f"📁 Excel file: {excel_path}")

            # Read Excel file
            df = self.read_excel_file(excel_path)

            # Convert to JSON if directory provided
            if json_dir:
                json_files = self.convert_to_json(df, json_dir)

            # Prepare incident data with embeddings
            incidents = self.prepare_incident_data(df, json_dir)

            # Insert into database
            self.insert_incidents(incidents)

            print("✅ Excel to Database processing completed successfully!")

            # Print summary
            total_rows = len(df)
            existing_count = len(self.get_existing_incidents())
            print("""
📊 Summary:""")
            print(f"   • Total rows in Excel: {total_rows}")
            print(f"   • Existing incidents in DB: {existing_count}")
            print(f"   • New incidents added: {len(incidents)}")

        except Exception as e:
            print(f"❌ Error in process_excel_to_db: {e}")
            raise

    def close_connection(self):
        """Close database connection"""
        if self.con:
            self.con.close()
            print("✅ Database connection closed")

def main():
    """Main function for command line usage"""
    excel_path = "input/INC.xlsx"
    json_dir = "output/json_records"

    # Ensure output directory exists
    os.makedirs(json_dir, exist_ok=True)

    processor = ExcelToDBProcessor()

    try:
        processor.process_excel_to_db(excel_path, json_dir)
    finally:
        processor.close_connection()

if __name__ == "__main__":
    main()
