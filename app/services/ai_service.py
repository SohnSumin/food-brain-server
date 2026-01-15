import os
from google import genai
from google.genai import types
from app.schemas.meal import AIAnalysisResponse

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def analyze_meal_image(image_bytes: bytes, mime_type: str) -> AIAnalysisResponse:
    prompt = "이 식단 사진을 분석해서 각 음식의 영양 성분과 총평을 JSON으로 알려줘."
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIAnalysisResponse
        )
    )
    return AIAnalysisResponse.model_validate_json(response.text)