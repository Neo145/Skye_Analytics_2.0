import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables (if you have them in a .env file)
# Otherwise, just use the hardcoded values you provided
# load_dotenv()

# Database connection parameters
DB_HOST = "ipl-db-0824.c5aso8akkkbg.eu-north-1.rds.amazonaws.com"
DB_USER = "skye"
DB_PASSWORD = "skyeneo4280"  # In a real production app, don't hardcode this
DB_NAME = "postgres"
DB_PORT = 5432

def inspect_database():
    """Connect to the database and list all tables with their information"""
    
    # Connect to the PostgreSQL database
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Get a list of all tables in the public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables in the database:")
        
        # For each table, get column information and row count
        for table in tables:
            table_name = table[0]
            
            # Get column information
            cursor.execute(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            print(f"\nTable: {table_name}")
            print(f"Row count: {row_count}")
            print("Columns:")
            
            for column in columns:
                col_name, data_type, max_length = column
                type_info = f"{data_type}"
                if max_length:
                    type_info += f"({max_length})"
                print(f"  - {col_name}: {type_info}")
                
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_database()