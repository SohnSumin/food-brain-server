from pydantic import BaseModel
from typing import List, Optional

class FoodItemBase(BaseModel):
    food_name: str
    calories: float
    carbs: float
    protein: float
    fat: float

class AIAnalysisResponse(BaseModel):
    detected_foods: List[FoodItemBase]
    ai_advice: str

class MealCreateRequest(BaseModel):
    user_id: str
    image_url: Optional[str] = None
    final_foods: List[FoodItemBase]
    total_calories: float
    total_carbs: float
    total_protein: float
    total_fat: float
    ai_advice: str