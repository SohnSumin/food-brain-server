from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.ai_service import analyze_meal_image
from app.schemas.meal import AIAnalysisResponse

router = APIRouter()

@router.post("/", response_model=AIAnalysisResponse)
async def analyze_diet_image(image: UploadFile = File(...)):
    """
    1. 사용자가 올린 사진을 받음
    2. AI Service를 통해 Gemini 분석 수행
    3. 분석된 영양 성분 결과를 반환 (DB 저장 X)
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    image_bytes = await image.read()
    # ai_service.py에 정의된 함수 호출
    analysis_result = await analyze_meal_image(image_bytes, image.content_type)
    
    return analysis_result