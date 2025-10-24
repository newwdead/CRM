#!/usr/bin/env python3
"""
Reset admin password script
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

def reset_admin_password():
    """Reset admin password to 'admin'"""
    db = SessionLocal()
    try:
        # Find admin user
        admin = db.query(User).filter(User.username == 'admin').first()
        
        if not admin:
            print("❌ Admin user not found!")
            return False
        
        # Reset password
        new_password = "admin"
        admin.hashed_password = get_password_hash(new_password)
        admin.is_active = True
        admin.is_admin = True
        
        db.commit()
        
        print("✅ Admin password reset successfully!")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Password: {new_password}")
        print(f"   Active: {admin.is_active}")
        print(f"   Admin: {admin.is_admin}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()

