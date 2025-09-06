-- Database initialization script
-- This script sets up the initial database structure and sample data

-- Create database if it doesn't exist
-- (This is handled by Docker environment variables)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual table creation will be handled by Alembic migrations
-- This file can be used for initial data seeding after migrations are run

-- Sample Nigerian food data (will be inserted after table creation)
-- INSERT INTO nigerian_foods (food_name, local_names, food_class, nutritional_info, cultural_context) VALUES
-- ('Jollof Rice', '{"yoruba": "Jollof", "igbo": "Jollof", "hausa": "Jollof"}', 'carbohydrates', '{"calories_per_100g": 150, "carbs": 30, "protein": 3, "fat": 2}', 'Popular West African rice dish, often served at celebrations'),
-- ('Amala', '{"yoruba": "Àmàlà"}', 'carbohydrates', '{"calories_per_100g": 120, "carbs": 25, "protein": 2, "fat": 1}', 'Traditional Yoruba dish made from yam flour'),
-- ('Efo Riro', '{"yoruba": "Ẹ̀fọ́ rírò"}', 'vitamins', '{"calories_per_100g": 80, "carbs": 8, "protein": 4, "fat": 5}', 'Nigerian spinach stew rich in vegetables'),
-- ('Suya', '{"hausa": "Suya"}', 'proteins', '{"calories_per_100g": 250, "carbs": 5, "protein": 25, "fat": 15}', 'Spiced grilled meat popular across Nigeria'),
-- ('Moi Moi', '{"yoruba": "Mọ́í mọ́í", "igbo": "Moi moi"}', 'proteins', '{"calories_per_100g": 180, "carbs": 15, "protein": 12, "fat": 8}', 'Steamed bean pudding, protein-rich traditional dish');

-- Sample nutrition rules (will be inserted after table creation)
-- INSERT INTO nutrition_rules (rule_name, condition_logic, feedback_template, priority, is_active) VALUES
-- ('Missing Protein Check', '{"missing_food_groups": ["proteins"]}', 'Your meal looks good, but try adding some protein like beans, fish, or meat to make it more balanced. Consider adding moi moi or suya!', 1, true),
-- ('Missing Vegetables Check', '{"missing_food_groups": ["vitamins"]}', 'Great choice of foods! To make your meal even healthier, add some vegetables like efo riro or ugwu for vitamins and minerals.', 1, true),
-- ('Balanced Meal Praise', '{"all_food_groups_present": true}', 'Excellent! Your meal has a great balance of all food groups. Keep up the healthy eating habits!', 2, true),
-- ('Too Much Carbs Warning', '{"carbohydrate_ratio": ">0.7"}', 'You have plenty of energy foods (carbohydrates), but try to balance with more proteins and vegetables for better nutrition.', 1, true);