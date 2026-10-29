import mysql.connector

db_config_no_db = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "123456"
}

def create_database_and_tables():
    try:
        # Connect to MySQL server (no specific database yet)
        print("Connecting to MySQL server...")
        conn = mysql.connector.connect(**db_config_no_db)
        cursor = conn.cursor()

        # Create Database
        print("Creating database 'educate_db2'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS educate_db2")
        cursor.execute("USE educate_db2")

        # 1. Create Users table (username, email, password)
        print("Creating 'users' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Create Login History table (login history and exit timing data)
        print("Creating 'login_history' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                session_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP NULL DEFAULT NULL,
                ip_address VARCHAR(45) DEFAULT '127.0.0.1',
                status VARCHAR(20) DEFAULT 'ACTIVE',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # 3. Create Predictions table (prediction data)
        print("Creating 'predictions' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                study_hours FLOAT NOT NULL,
                attendance FLOAT NOT NULL,
                online_courses INT NOT NULL,
                assignment_completion FLOAT NOT NULL,
                stress_level FLOAT NOT NULL,
                predicted_score FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # 4. Create Individual Performance table (aggregated performance metrics)
        print("Creating 'individual_performance' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individual_performance (
                performance_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                total_scenarios_run INT DEFAULT 0,
                average_predicted_score FLOAT DEFAULT 0.0,
                highest_score FLOAT DEFAULT 0.0,
                lowest_score FLOAT DEFAULT 0.0,
                risk_level VARCHAR(20) DEFAULT 'Low Risk',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("Database and all tables created successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    create_database_and_tables()
