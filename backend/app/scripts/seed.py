import csv
import os
import sys
import pymysql

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_db_connection():
    # Use absolute imports for -m execution
    from app.config import get_settings
    settings = get_settings()
    url = settings.database_url
    
    if url.startswith("mysql"):
        # Format: mysql+pymysql://user:pass@host:port/db
        try:
            parts = url.replace("mysql+pymysql://", "").split("@")
            creds = parts[0].split(":")
            addr = parts[1].split("/")
            host_port = addr[0].split(":")
            
            ssl_config = None
            if settings.database_ssl:
                ssl_config = {}
                if settings.database_ssl_ca:
                    ssl_config["ca"] = settings.database_ssl_ca

            return pymysql.connect(
                user=creds[0],
                password=creds[1],
                host=host_port[0],
                port=int(host_port[1]) if len(host_port) > 1 else 3306,
                database=addr[1],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5,
                ssl=ssl_config
            )
        except Exception as e:
            print(f"Error parsing database URL: {e}")
            return None
    elif url.startswith("sqlite"):
        import sqlite3
        path = url.replace("sqlite:///", "")
        return sqlite3.connect(path)
    return None

def seed_data():
    print("Starting seed script...")
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database.")
            return
        
        cursor = conn.cursor()
        
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        if not os.path.exists(data_dir):
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            
        # 1. Seed Roles
        role_file = os.path.join(data_dir, "role.txt")
        if os.path.exists(role_file):
            print("Seeding roles...")
            with open(role_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["Tên"]
                    desc = row["Mô tả"]
                    cursor.execute("SELECT id FROM role WHERE name = %s", (name,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO role (name, description) VALUES (%s, %s)", (name, desc))
            conn.commit()

        # 2. Seed Departments
        dept_file = os.path.join(data_dir, "departure.txt")
        if os.path.exists(dept_file):
            print("Seeding departments...")
            with open(dept_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row["Tên"]
                    name = row["Mô tả"]
                    cursor.execute("SELECT id FROM department WHERE code = %s", (code,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO department (code, name, is_deleted) VALUES (%s, %s, %s)", (code, name, 0))
            conn.commit()

        # 3. Seed Users
        user_file = os.path.join(data_dir, "user.txt")
        if os.path.exists(user_file):
            print("Seeding users...")
            from app.core.security import get_password_hash
            with open(user_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["Name"]
                    email = row["Email"]
                    pwd = row["Password"]
                    cursor.execute("SELECT id FROM user WHERE email = %s", (email,))
                    if not cursor.fetchone():
                        hashed = get_password_hash(pwd)
                        username = email.split("@")[0]
                        cursor.execute(
                            "INSERT INTO user (username, email, hashed_password, system_role, is_active) VALUES (%s, %s, %s, %s, %s)",
                            (username, email, hashed, "admin", 1)
                        )
            conn.commit()

        # 4. Seed Members
        member_file = os.path.join(data_dir, "member.txt")
        if os.path.exists(member_file):
            print("Seeding members...")
            cursor.execute("SELECT id FROM department LIMIT 1")
            default_dept = cursor.fetchone()
            dept_id = default_dept['id'] if default_dept and isinstance(default_dept, dict) else (default_dept[0] if default_dept else None)
            
            if not dept_id:
                print("No department found. Cannot seed members.")
            else:
                with open(member_file, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = row["EMAIL"]
                        name = row["NAME"]
                        phone = row.get("PHONE", "").strip()
                        mid = int(row["ID"])
                        cursor.execute("SELECT id FROM member WHERE email = %s", (email,))
                        if not cursor.fetchone():
                            cursor.execute("SELECT id FROM user WHERE email = %s", (email,))
                            user_row = cursor.fetchone()
                            uid = user_row['id'] if user_row and isinstance(user_row, dict) else (user_row[0] if user_row else None)
                            
                            cursor.execute(
                                "INSERT INTO member (id, full_name, email, phone, department_id, user_id, default_role, is_deleted) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (mid, name, email, phone, dept_id, uid, "Staff", 0)
                            )
                conn.commit()

        print("Seeding completed successfully!")
    except Exception as e:
        print(f"Error seeding data: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    seed_data()
