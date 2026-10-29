import mysql.connector

db_config = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "123456",
    "database": "educate_db2"
}

def export_db_to_txt(filename="database_export.txt"):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        with open(filename, "w") as f:
            f.write("=== DATABASE EXPORT: educate_db ===\n\n")
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                f.write(f"--- TABLE: {table_name} ---\n")
                
                # Get table schema
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                f.write("SCHEMA:\n")
                for col in columns:
                    f.write(f"  {col[0]} ({col[1]})\n")
                
                # Get table data
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                f.write("\nDATA:\n")
                if not rows:
                    f.write("  (No data)\n")
                for row in rows:
                    f.write(f"  {row}\n")
                    
                f.write("\n" + "="*40 + "\n\n")
                
        print(f"Successfully exported database to {filename}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    export_db_to_txt()
