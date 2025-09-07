"""Create default super admin user."""

import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.admin import AdminUser, AdminRole
from app.core.auth import get_password_hash


def create_super_admin(email: str, name: str, password: str):
    """Create a super admin user."""

    db: Session = SessionLocal()

    try:
        # Check if super admin already exists
        existing_admin = db.query(AdminUser).filter(
            AdminUser.email == email
        ).first()

        if existing_admin:
            print(f"Admin user with email {email} already exists")
            return False

        # Create super admin user
        super_admin = AdminUser(
            email=email,
            name=name,
            password_hash=get_password_hash(password),
            role=AdminRole.SUPER_ADMIN.value,
            is_active=True
        )

        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)

        print(f"Super admin user created successfully:")
        print(f"  Email: {super_admin.email}")
        print(f"  Name: {super_admin.name}")
        print(f"  Role: {super_admin.role}")
        print(f"  ID: {super_admin.id}")

        return True

    except Exception as e:
        print(f"Error creating super admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_super_admin.py <email> <name> <password>")
        print("Example: python create_super_admin.py admin@example.com 'Super Admin' 'securepassword123'")
        sys.exit(1)

    email = sys.argv[1]
    name = sys.argv[2]
    password = sys.argv[3]

    if len(password) < 8:
        print("Password must be at least 8 characters long")
        sys.exit(1)

    success = create_super_admin(email, name, password)
    sys.exit(0 if success else 1)
