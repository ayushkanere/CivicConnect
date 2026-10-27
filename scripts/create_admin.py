"""
CivicConnect - Admin Account Creation Script
Prompts securely for administrator credentials to initialize the portal.
No hardcoded passwords exist in this repository.
"""
import sys
import getpass
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models import User


def create_admin_interactive(name=None, email=None, password=None):
    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        print("\n" + "=" * 50)
        print(" CivicConnect Administrator Setup")
        print("=" * 50)

        # 1. Name
        if not name:
            while True:
                name = input("Enter Admin Full Name: ").strip()
                if name:
                    break
                print("Error: Name cannot be empty.")

        # 2. Email
        if not email:
            while True:
                email = input("Enter Admin Email (optional, press Enter to skip): ").strip()
                if not email:
                    email = None
                    break
                if "@" in email and "." in email:
                    break
                print("Error: Please enter a valid email address or leave blank.")

        # Check existing user
        existing = User.query.filter((User.name == name) | (User.email == email if email else False)).first()
        if existing:
            print(f"\n[!] A user with name '{name}' or email '{email}' already exists.")
            update = input("Do you want to update their password? (y/N): ").strip().lower()
            if update != "y":
                print("Aborted.")
                return

        # 3. Password
        if not password:
            while True:
                p1 = getpass.getpass("Enter Admin Password (min 8 characters): ")
                if len(p1) < 8:
                    print("Error: Password must be at least 8 characters.")
                    continue
                p2 = getpass.getpass("Confirm Admin Password: ")
                if p1 != p2:
                    print("Error: Passwords do not match.")
                    continue
                password = p1
                break

        # Save user
        if existing:
            existing.set_password(password)
            db.session.commit()
            print(f"\n[+] Successfully updated password for admin '{existing.name}'.")
        else:
            admin_user = User(
                name=name,
                email=email,
                role="admin"
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"\n[+] Administrator '{name}' created successfully (User ID: {admin_user.user_id}).")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a CivicConnect administrator account.")
    parser.add_argument("--name", help="Admin display name")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password (for non-interactive automation)")
    args = parser.parse_args()

    create_admin_interactive(args.name, args.email, args.password)
