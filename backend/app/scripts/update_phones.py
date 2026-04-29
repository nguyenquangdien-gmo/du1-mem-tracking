import csv
import os
import sys

# Add parent directory to sys.path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models.member import Member

def update_phones():
    db = SessionLocal()
    file_path = os.path.join('app', 'data', 'member.txt')
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    try:
        updated_count = 0
        not_found_emails = []
        
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row['EMAIL'].strip().lower()
                phone = row['PHONE'].strip()
                
                member = db.query(Member).filter(Member.email == email).first()
                if member:
                    member.phone = phone
                    updated_count += 1
                else:
                    not_found_emails.append(email)
        
        db.commit()
        print(f"Successfully updated {updated_count} members.")
        if not_found_emails:
            print(f"Emails not found in database: {', '.join(not_found_emails)}")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_phones()
