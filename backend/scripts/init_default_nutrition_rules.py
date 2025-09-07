"""Initialize default nutrition rules for Nigerian foods."""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.feedback import NutritionRule


def init_default_nutrition_rules():
    """Initialize default nutrition rules."""

    db: Session = SessionLocal()

    try:
        # Define default nutrition rules
        default_rules = [
            {
                "rule_name": "Balanced Meal Check",
                "condition_logic": {
                    "type": "food_group_balance",
                    "min_groups": 3
                },
                "feedback_template": "Great start! Try to include foods from at least 3 different groups for a more balanced meal. Consider adding {missing_groups} to complete your nutrition.",
                "priority": 1,
                "is_active": True
            },
            {
                "rule_name": "Protein Deficiency Check",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["proteins"]
                },
                "feedback_template": "Your meal could use some protein! Try adding beans (moimoi, akara), fish, chicken, or eggs to help build and repair your body tissues.",
                "priority": 2,
                "is_active": True
            },
            {
                "rule_name": "Vegetable Reminder",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["vitamins"]
                },
                "feedback_template": "Don't forget your vegetables! Add some efo riro, ugwu, or waterleaf to get essential vitamins and minerals for good health.",
                "priority": 3,
                "is_active": True
            },
            {
                "rule_name": "Carbohydrate Balance",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["carbohydrates"]
                },
                "feedback_template": "You need some energy foods! Consider adding rice, yam, plantain, or amala to fuel your daily activities.",
                "priority": 4,
                "is_active": True
            },
            {
                "rule_name": "Complete Nigerian Meal",
                "condition_logic": {
                    "type": "food_group_balance",
                    "min_groups": 4
                },
                "feedback_template": "Excellent! You have a well-balanced Nigerian meal with foods from multiple groups. This provides good nutrition for your body and mind.",
                "priority": 5,
                "is_active": True
            },
            {
                "rule_name": "Traditional Combination Check",
                "condition_logic": {
                    "type": "specific_food_present",
                    "required_foods": ["jollof rice", "amala", "pounded yam"]
                },
                "feedback_template": "Nice choice of traditional Nigerian food! To make it more nutritious, pair it with vegetables like efo riro or okra soup, and add some protein.",
                "priority": 6,
                "is_active": True
            },
            {
                "rule_name": "Healthy Fats Reminder",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["fats"]
                },
                "feedback_template": "Consider adding some healthy fats like palm oil (in moderation), groundnuts, or avocado to help your body absorb vitamins better.",
                "priority": 7,
                "is_active": True
            },
            {
                "rule_name": "Mineral Rich Foods",
                "condition_logic": {
                    "type": "missing_food_groups",
                    "required_groups": ["minerals"]
                },
                "feedback_template": "Add some mineral-rich foods like leafy vegetables, fish, or dairy products to support strong bones and healthy blood.",
                "priority": 8,
                "is_active": True
            },
            {
                "rule_name": "Student Budget Meal",
                "condition_logic": {
                    "type": "specific_food_present",
                    "required_foods": ["beans", "rice", "plantain", "bread"]
                },
                "feedback_template": "Good budget-friendly choice! These foods provide good nutrition at affordable prices. Try to add some vegetables when possible.",
                "priority": 9,
                "is_active": True
            },
            {
                "rule_name": "Single Food Group Warning",
                "condition_logic": {
                    "type": "food_group_balance",
                    "min_groups": 2
                },
                "feedback_template": "Your meal has foods from only one group. For better nutrition and energy throughout the day, try to combine different types of foods.",
                "priority": 10,
                "is_active": True
            }
        ]

        # Create rules if they don't exist
        created_count = 0
        for rule_data in default_rules:
            existing_rule = db.query(NutritionRule).filter(
                NutritionRule.rule_name == rule_data["rule_name"]
            ).first()

            if not existing_rule:
                rule = NutritionRule(**rule_data)
                db.add(rule)
                created_count += 1
                print(f"Created rule: {rule_data['rule_name']}")
            else:
                print(f"Rule already exists: {rule_data['rule_name']}")

        # Commit all changes
        db.commit()
        print(
            f"\nSuccessfully initialized {created_count} new nutrition rules")
        print(f"Total rules in database: {db.query(NutritionRule).count()}")

    except Exception as e:
        print(f"Error initializing nutrition rules: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_default_nutrition_rules()
