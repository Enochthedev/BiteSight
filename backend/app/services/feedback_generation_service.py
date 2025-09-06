"""Culturally relevant feedback generation service."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import random
import logging

from app.core.nutrition_engine import NutritionProfile, NutritionRule

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback messages."""
    ENCOURAGEMENT = "encouragement"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    CELEBRATION = "celebration"
    EDUCATIONAL = "educational"


class CulturalContext(Enum):
    """Cultural contexts for feedback."""
    NIGERIAN_GENERAL = "nigerian_general"
    YORUBA = "yoruba"
    IGBO = "igbo"
    HAUSA = "hausa"
    STUDENT_FRIENDLY = "student_friendly"


@dataclass
class FeedbackTemplate:
    """Template for generating feedback messages."""
    template_id: str
    message_template: str
    feedback_type: FeedbackType
    cultural_context: CulturalContext
    food_examples: List[str]
    priority: int = 1

    def format_message(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.message_template.format(**kwargs)
        except KeyError as e:
            logger.warning(
                f"Missing template variable {e} in template {self.template_id}")
            return self.message_template


class NigerianFeedbackGenerator:
    """Generator for culturally relevant Nigerian nutrition feedback."""

    def __init__(self):
        self.templates = self._initialize_templates()
        self.food_suggestions = self._initialize_food_suggestions()
        self.encouragement_phrases = self._initialize_encouragement_phrases()

    def _initialize_templates(self) -> List[FeedbackTemplate]:
        """Initialize feedback templates with Nigerian cultural context."""
        return [
            # Encouragement templates
            FeedbackTemplate(
                template_id="balanced_meal_celebration",
                message_template="Excellent choice! Your meal shows good balance - this is how our ancestors ate for strength and health. {encouragement}",
                feedback_type=FeedbackType.CELEBRATION,
                cultural_context=CulturalContext.NIGERIAN_GENERAL,
                food_examples=[],
                priority=10
            ),
            FeedbackTemplate(
                template_id="traditional_combo_praise",
                message_template="Beautiful traditional combination! {food_combo} is a classic that provides both energy and nutrients. Our grandmothers knew best! {encouragement}",
                feedback_type=FeedbackType.CELEBRATION,
                cultural_context=CulturalContext.NIGERIAN_GENERAL,
                food_examples=["amala and efo riro",
                               "rice and beans", "yam and egg sauce"],
                priority=8
            ),

            # Suggestion templates
            FeedbackTemplate(
                template_id="missing_protein_suggestion",
                message_template="Your meal needs some protein power! Try adding {protein_suggestions} to make it more complete. Protein helps build strong muscles for your studies! {encouragement}",
                feedback_type=FeedbackType.SUGGESTION,
                cultural_context=CulturalContext.STUDENT_FRIENDLY,
                food_examples=["beans", "fish", "chicken", "moimoi", "eggs"],
                priority=5
            ),
            FeedbackTemplate(
                template_id="missing_vegetables_suggestion",
                message_template="Add some green power to your plate! {vegetable_suggestions} will give you the vitamins and minerals your brain needs. {encouragement}",
                feedback_type=FeedbackType.SUGGESTION,
                cultural_context=CulturalContext.STUDENT_FRIENDLY,
                food_examples=["efo riro", "ugwu soup", "okra soup",
                               "vegetable soup", "bitter leaf soup"],
                priority=4
            ),
            FeedbackTemplate(
                template_id="missing_carbs_suggestion",
                message_template="You need energy foods for your busy day! Consider adding {carb_suggestions} to fuel your body and mind. {encouragement}",
                feedback_type=FeedbackType.SUGGESTION,
                cultural_context=CulturalContext.STUDENT_FRIENDLY,
                food_examples=["rice", "yam", "amala", "fufu", "eba", "bread"],
                priority=3
            ),

            # Educational templates
            FeedbackTemplate(
                template_id="balanced_nutrition_education",
                message_template="A balanced Nigerian meal should have: energy foods (rice, yam), body-building foods (beans, fish), and protective foods (vegetables, fruits). {encouragement}",
                feedback_type=FeedbackType.EDUCATIONAL,
                cultural_context=CulturalContext.NIGERIAN_GENERAL,
                food_examples=[],
                priority=6
            ),
            FeedbackTemplate(
                template_id="traditional_wisdom",
                message_template="Our traditional foods are naturally balanced! Combining {traditional_combo} gives you complete nutrition the Nigerian way. {encouragement}",
                feedback_type=FeedbackType.EDUCATIONAL,
                cultural_context=CulturalContext.NIGERIAN_GENERAL,
                food_examples=["beans and plantain",
                               "rice and stew", "yam and palm oil"],
                priority=7
            ),

            # Warning templates
            FeedbackTemplate(
                template_id="too_much_carbs_warning",
                message_template="Your meal has plenty of energy foods, but don't forget the other food groups! Balance it with {balance_suggestions} next time. {encouragement}",
                feedback_type=FeedbackType.WARNING,
                cultural_context=CulturalContext.STUDENT_FRIENDLY,
                food_examples=["vegetables", "proteins", "fruits"],
                priority=2
            ),

            # Regional variations
            FeedbackTemplate(
                template_id="yoruba_traditional_praise",
                message_template="Ẹ ku àárẹ! Your {food_name} looks delicious and nutritious. This is good Yoruba food that will keep you strong! {encouragement}",
                feedback_type=FeedbackType.CELEBRATION,
                cultural_context=CulturalContext.YORUBA,
                food_examples=["amala", "efo riro", "gbegiri"],
                priority=9
            ),
            FeedbackTemplate(
                template_id="igbo_traditional_praise",
                message_template="Ndewo! Your {food_name} is a wonderful Igbo choice. This kind of food gives strength and wisdom! {encouragement}",
                feedback_type=FeedbackType.CELEBRATION,
                cultural_context=CulturalContext.IGBO,
                food_examples=["fufu", "oha soup", "ugwu"],
                priority=9
            ),
            FeedbackTemplate(
                template_id="hausa_traditional_praise",
                message_template="Sannu! Your {food_name} is excellent Northern Nigerian food. This will give you energy for the whole day! {encouragement}",
                feedback_type=FeedbackType.CELEBRATION,
                cultural_context=CulturalContext.HAUSA,
                food_examples=["tuwo", "miyan kuka", "kilishi"],
                priority=9
            )
        ]

    def _initialize_food_suggestions(self) -> Dict[str, List[str]]:
        """Initialize culturally appropriate food suggestions."""
        return {
            "proteins": [
                "beans (ewa)", "moimoi", "akara", "fish (eja)", "chicken",
                "beef", "eggs", "groundnuts", "suya", "kilishi"
            ],
            "vegetables": [
                "efo riro (spinach stew)", "ugwu soup", "okra soup",
                "bitter leaf soup", "vegetable soup", "waterleaf soup",
                "oha soup", "egusi soup", "afang soup"
            ],
            "carbohydrates": [
                "jollof rice", "white rice", "amala", "fufu", "pounded yam",
                "eba", "tuwo", "yam", "plantain", "sweet potato", "bread"
            ],
            "fruits": [
                "orange", "banana", "pineapple", "mango", "pawpaw",
                "watermelon", "apple", "guava", "coconut"
            ],
            "traditional_combos": [
                "rice and beans", "amala and efo riro", "fufu and soup",
                "yam and egg sauce", "plantain and beans", "bread and tea"
            ]
        }

    def _initialize_encouragement_phrases(self) -> List[str]:
        """Initialize encouraging phrases in Nigerian context."""
        return [
            "Keep up the good work!",
            "You're doing great!",
            "Your body will thank you!",
            "This is how champions eat!",
            "Smart food choices for a smart student!",
            "You're building healthy habits!",
            "Excellent food wisdom!",
            "Your future self will be grateful!",
            "This is the way to stay strong and focused!",
            "Good nutrition, good grades!",
            "Healthy body, healthy mind!",
            "You're investing in your health!",
            "This is proper Nigerian nutrition!",
            "Your ancestors would be proud!",
            "Food is medicine - you're doing it right!"
        ]

    def generate_feedback(self,
                          nutrition_profile: NutritionProfile,
                          detected_foods: List[Dict[str, Any]],
                          matching_rules: List[NutritionRule],
                          cultural_context: CulturalContext = CulturalContext.NIGERIAN_GENERAL) -> Dict[str, Any]:
        """Generate culturally relevant feedback."""

        feedback_messages = []
        recommendations = []

        # Process matching rules first
        for rule in matching_rules[:3]:  # Limit to top 3 rules
            template = self._find_template_for_rule(rule, cultural_context)
            if template:
                message = self._generate_message_from_template(
                    template, nutrition_profile, detected_foods
                )
                feedback_messages.append({
                    "message": message,
                    "type": template.feedback_type.value,
                    "priority": template.priority
                })

        # Generate general recommendations
        recommendations = self._generate_recommendations(
            nutrition_profile, detected_foods)

        # Add encouragement
        encouragement = self._get_encouragement_message(
            nutrition_profile, detected_foods)

        # Generate overall feedback message
        overall_message = self._generate_overall_message(
            nutrition_profile, detected_foods, cultural_context
        )

        return {
            "overall_message": overall_message,
            "specific_feedback": feedback_messages,
            "recommendations": recommendations,
            "encouragement": encouragement,
            "cultural_context": cultural_context.value,
            "balance_score": nutrition_profile.calculate_balance_score()
        }

    def _find_template_for_rule(self, rule: NutritionRule,
                                cultural_context: CulturalContext) -> Optional[FeedbackTemplate]:
        """Find appropriate template for a rule."""
        # Map rule types to template patterns
        rule_template_mapping = {
            "missing_protein": "missing_protein_suggestion",
            "missing_vegetables": "missing_vegetables_suggestion",
            "missing_carbs": "missing_carbs_suggestion",
            "well_balanced": "balanced_meal_celebration",
            "too_much_carbs": "too_much_carbs_warning",
            "traditional_combo": "traditional_combo_praise",
            "rice_and_beans": "traditional_combo_praise"
        }

        template_id = rule_template_mapping.get(rule.rule_id)
        if template_id:
            # Find template matching the ID and cultural context
            for template in self.templates:
                if (template.template_id == template_id and
                    (template.cultural_context == cultural_context or
                     template.cultural_context == CulturalContext.NIGERIAN_GENERAL or
                     template.cultural_context == CulturalContext.STUDENT_FRIENDLY)):
                    return template

        return None

    def _generate_message_from_template(self,
                                        template: FeedbackTemplate,
                                        nutrition_profile: NutritionProfile,
                                        detected_foods: List[Dict[str, Any]]) -> str:
        """Generate message from template with context."""

        # Prepare template variables
        variables = {
            "encouragement": random.choice(self.encouragement_phrases),
            "balance_score": f"{nutrition_profile.calculate_balance_score():.1%}"
        }

        # Add food-specific suggestions
        if "protein_suggestions" in template.message_template:
            suggestions = random.sample(self.food_suggestions["proteins"],
                                        min(3, len(self.food_suggestions["proteins"])))
            variables["protein_suggestions"] = ", ".join(suggestions)

        if "vegetable_suggestions" in template.message_template:
            suggestions = random.sample(self.food_suggestions["vegetables"],
                                        min(3, len(self.food_suggestions["vegetables"])))
            variables["vegetable_suggestions"] = ", ".join(suggestions)

        if "carb_suggestions" in template.message_template:
            suggestions = random.sample(self.food_suggestions["carbohydrates"],
                                        min(3, len(self.food_suggestions["carbohydrates"])))
            variables["carb_suggestions"] = ", ".join(suggestions)

        if "food_combo" in template.message_template:
            variables["food_combo"] = random.choice(
                self.food_suggestions["traditional_combos"])

        if "traditional_combo" in template.message_template:
            variables["traditional_combo"] = random.choice(
                self.food_suggestions["traditional_combos"])

        if "balance_suggestions" in template.message_template:
            missing_groups = nutrition_profile.get_missing_groups()
            suggestions = []
            for group in missing_groups[:2]:  # Top 2 missing groups
                if group in ["proteins", "vegetables", "carbohydrates"]:
                    suggestions.extend(
                        self.food_suggestions.get(group, [])[:2])
            variables["balance_suggestions"] = ", ".join(
                suggestions) if suggestions else "vegetables and proteins"

        # Add detected food names
        if detected_foods:
            food_names = [food.get("food_name", "").replace(
                "_", " ") for food in detected_foods]
            variables["food_name"] = food_names[0] if food_names else "your meal"
            variables["food_names"] = ", ".join(food_names)

        return template.format_message(**variables)

    def _generate_recommendations(self,
                                  nutrition_profile: NutritionProfile,
                                  detected_foods: List[Dict[str, Any]]) -> List[str]:
        """Generate specific food recommendations."""
        recommendations = []
        missing_groups = nutrition_profile.get_missing_groups()

        # Map nutrition groups to food suggestion categories
        group_mapping = {
            "proteins": "proteins",
            "carbohydrates": "carbohydrates",
            "fats": "proteins",  # Include protein sources that have fats
            "vitamins": "fruits",  # Fruits are good sources of vitamins
            "minerals": "vegetables",  # Vegetables are good sources of minerals
            "water": "fruits"  # Fruits have high water content
        }

        for group in missing_groups:
            suggestion_category = group_mapping.get(group)
            if suggestion_category and suggestion_category in self.food_suggestions:
                suggestion = random.choice(
                    self.food_suggestions[suggestion_category])
                recommendations.append(f"Add {suggestion} for {group}")

        # Add combination suggestions
        if len(detected_foods) == 1:
            food_name = detected_foods[0].get("food_name", "")
            if "rice" in food_name.lower():
                recommendations.append(
                    "Pair with beans or stew for complete nutrition")
            elif "beans" in food_name.lower():
                recommendations.append("Add rice or bread for energy")
            elif any(veg in food_name.lower() for veg in ["efo", "ugwu", "okra"]):
                recommendations.append("Serve with amala, fufu, or rice")

        return recommendations[:4]  # Limit to 4 recommendations

    def _get_encouragement_message(self,
                                   nutrition_profile: NutritionProfile,
                                   detected_foods: List[Dict[str, Any]]) -> str:
        """Get contextual encouragement message."""
        balance_score = nutrition_profile.calculate_balance_score()

        if balance_score > 0.7:
            return random.choice([
                "Outstanding nutritional choices!",
                "You're eating like a champion!",
                "This is how healthy Nigerians eat!",
                "Your body is getting everything it needs!"
            ])
        elif balance_score > 0.4:
            return random.choice([
                "Good start! A few tweaks will make it perfect.",
                "You're on the right track!",
                "Nice food choices - let's make them even better!",
                "Your nutrition game is improving!"
            ])
        else:
            return random.choice([
                "Every meal is a chance to nourish your body!",
                "Small changes can make a big difference!",
                "You're learning - that's what matters!",
                "Tomorrow's meal can be even better!"
            ])

    def _generate_overall_message(self,
                                  nutrition_profile: NutritionProfile,
                                  detected_foods: List[Dict[str, Any]],
                                  cultural_context: CulturalContext) -> str:
        """Generate overall feedback message."""
        balance_score = nutrition_profile.calculate_balance_score()
        missing_count = len(nutrition_profile.get_missing_groups())

        if balance_score > 0.7 and missing_count <= 1:
            return "Excellent! Your meal shows great nutritional balance. This is the kind of eating that builds strong, healthy bodies and sharp minds!"

        elif balance_score > 0.4:
            return f"Good meal choice! You're getting {len(detected_foods)} food types, but adding a bit more variety would make it even better for your health."

        else:
            return "This is a start! Nigerian cuisine offers so many nutritious options - let's explore ways to make your next meal even more balanced and delicious."

    def localize_feedback(self, feedback: Dict[str, Any],
                          language: str = "english") -> Dict[str, Any]:
        """Localize feedback to different Nigerian languages."""
        # Placeholder for future localization
        # Could add Yoruba, Igbo, Hausa translations

        if language.lower() == "yoruba":
            # Add Yoruba greetings and phrases
            feedback["cultural_greeting"] = "Ẹ ku àárẹ! (Good afternoon!)"
            feedback["closing"] = "Ẹ ku àárẹ o! (Have a good afternoon!)"
        elif language.lower() == "igbo":
            feedback["cultural_greeting"] = "Ndewo! (Hello!)"
            feedback["closing"] = "Ka ọ dị! (Take care!)"
        elif language.lower() == "hausa":
            feedback["cultural_greeting"] = "Sannu! (Hello!)"
            feedback["closing"] = "Sai an jima! (See you later!)"

        return feedback


# Global feedback generator instance
nigerian_feedback_generator = NigerianFeedbackGenerator()
