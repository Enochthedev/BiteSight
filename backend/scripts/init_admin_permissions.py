"""Initialize default admin permissions and roles."""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.admin import AdminPermission, AdminRolePermission, AdminRole
from app.services.admin_service import AdminService


def init_admin_permissions():
    """Initialize default admin permissions and role mappings."""

    db: Session = SessionLocal()

    try:
        # Define default permissions
        default_permissions = [
            # Dataset management permissions
            {
                "name": "dataset_view",
                "description": "View food dataset items",
                "resource": "dataset",
                "action": "view"
            },
            {
                "name": "dataset_create",
                "description": "Create new food dataset items",
                "resource": "dataset",
                "action": "create"
            },
            {
                "name": "dataset_update",
                "description": "Update existing food dataset items",
                "resource": "dataset",
                "action": "update"
            },
            {
                "name": "dataset_delete",
                "description": "Delete food dataset items",
                "resource": "dataset",
                "action": "delete"
            },
            {
                "name": "dataset_manage",
                "description": "Full dataset management access",
                "resource": "dataset",
                "action": "manage"
            },

            # Nutrition rules permissions
            {
                "name": "nutrition_rules_view",
                "description": "View nutrition rules",
                "resource": "nutrition_rules",
                "action": "view"
            },
            {
                "name": "nutrition_rules_create",
                "description": "Create new nutrition rules",
                "resource": "nutrition_rules",
                "action": "create"
            },
            {
                "name": "nutrition_rules_update",
                "description": "Update existing nutrition rules",
                "resource": "nutrition_rules",
                "action": "update"
            },
            {
                "name": "nutrition_rules_delete",
                "description": "Delete nutrition rules",
                "resource": "nutrition_rules",
                "action": "delete"
            },
            {
                "name": "nutrition_rules_manage",
                "description": "Full nutrition rules management access",
                "resource": "nutrition_rules",
                "action": "manage"
            },

            # User management permissions
            {
                "name": "users_view",
                "description": "View user accounts",
                "resource": "users",
                "action": "view"
            },
            {
                "name": "users_manage",
                "description": "Manage user accounts",
                "resource": "users",
                "action": "manage"
            },

            # System administration permissions
            {
                "name": "system_admin",
                "description": "System administration access",
                "resource": "system",
                "action": "admin"
            },
            {
                "name": "system_monitor",
                "description": "System monitoring access",
                "resource": "system",
                "action": "monitor"
            }
        ]

        # Create permissions if they don't exist
        created_permissions = {}
        for perm_data in default_permissions:
            existing_perm = db.query(AdminPermission).filter(
                AdminPermission.name == perm_data["name"]
            ).first()

            if not existing_perm:
                permission = AdminPermission(**perm_data)
                db.add(permission)
                db.flush()  # Get the ID
                created_permissions[perm_data["name"]] = permission
                print(f"Created permission: {perm_data['name']}")
            else:
                created_permissions[perm_data["name"]] = existing_perm
                print(f"Permission already exists: {perm_data['name']}")

        # Define role-permission mappings
        role_permissions = {
            AdminRole.SUPER_ADMIN.value: [
                # Super admin gets all permissions
                perm["name"] for perm in default_permissions
            ],
            AdminRole.ADMIN.value: [
                "dataset_view", "dataset_create", "dataset_update", "dataset_manage",
                "nutrition_rules_view", "nutrition_rules_create", "nutrition_rules_update", "nutrition_rules_manage",
                "users_view", "users_manage",
                "system_monitor"
            ],
            AdminRole.NUTRITIONIST.value: [
                "dataset_view", "dataset_create", "dataset_update",
                "nutrition_rules_view", "nutrition_rules_create", "nutrition_rules_update", "nutrition_rules_manage",
                "users_view"
            ],
            AdminRole.DATASET_MANAGER.value: [
                "dataset_view", "dataset_create", "dataset_update", "dataset_manage",
                "nutrition_rules_view"
            ]
        }

        # Create role-permission mappings
        for role, permission_names in role_permissions.items():
            for perm_name in permission_names:
                if perm_name in created_permissions:
                    # Check if mapping already exists
                    existing_mapping = db.query(AdminRolePermission).filter(
                        AdminRolePermission.role == role,
                        AdminRolePermission.permission_id == created_permissions[perm_name].id
                    ).first()

                    if not existing_mapping:
                        role_permission = AdminRolePermission(
                            role=role,
                            permission_id=created_permissions[perm_name].id
                        )
                        db.add(role_permission)
                        print(f"Mapped {role} -> {perm_name}")
                    else:
                        print(f"Mapping already exists: {role} -> {perm_name}")

        # Commit all changes
        db.commit()
        print("Successfully initialized admin permissions and role mappings")

    except Exception as e:
        print(f"Error initializing admin permissions: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_admin_permissions()
