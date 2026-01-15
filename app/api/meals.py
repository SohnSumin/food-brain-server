from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.ai_service import analyze_meal_image
from app.schemas.meal import MealCreateRequest, AIAnalysisResponse
from app.core.config import supabase

router = APIRouter()

# 1. 이미지 분석
@router.post("/analyze", response_model=AIAnalysisResponse)
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

# 2. 식단 기록 생성 (Create)
@router.post("/confirm")
async def confirm_and_save_meal(request: MealCreateRequest):
    """
    1. 사용자가 수정한 최종 데이터를 받음
    2. Supabase의 meal_logs 테이블에 부모 데이터 삽입
    3. 생성된 ID를 가지고 meal_items에 개별 음식들 삽입
    """
    try:
        # Step 1: 부모 로그 저장
        log_data = {
            "user_id": request.user_id,
            "total_calories": request.total_calories,
            "total_carbs": request.total_carbs,
            "total_protein": request.total_protein,
            "total_fat": request.total_fat,
            "ai_advice": request.ai_advice,
            "image_url": request.image_url
        }
        log_res = supabase.table("meal_logs").insert(log_data).execute()
        meal_id = log_res.data[0]['id']

        # Step 2: 자식 아이템들 저장
        items_data = []
        for item in request.final_foods:
            items_data.append({
                "meal_id": meal_id,
                "food_name": item.food_name,
                "calories": item.calories,
                "carbs": item.carbs,
                "protein": item.protein,
                "fat": item.fat
            })
        supabase.table("meal_items").insert(items_data).execute()

        return {"status": "success", "message": "식단이 성공적으로 기록되었습니다.", "meal_id": meal_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 중 오류 발생: {str(e)}")
    
# 3. 전체 목록 조회 (Read - List)
@router.get("/list/{user_id}")
async def get_meal_list(user_id: str):
    # 유저의 식단 로그를 최신순으로 가져옴
    res = supabase.table("meal_logs")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

# 4. 상세 조회 (Read - Detail)
@router.get("/detail/{meal_id}")
async def get_meal_detail(meal_id: str):
    # 특정 식단의 정보와 그에 속한 모든 음식(meal_items)을 가져옴
    res = supabase.table("meal_logs")\
        .select("*, meal_items(*)")\
        .eq("id", meal_id)\
        .single()\
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="식단 정보를 찾을 수 없습니다.")
    return res.data

# 5. 삭제 (Delete)
@router.delete("/{meal_id}")
async def delete_meal(meal_id: str):
    # meal_items는 외래키 설정(On Delete Cascade)에 의해 자동 삭제되거나, 
    # 수동으로 먼저 지워줘야 할 수도 있습니다.
    try:
        # 1. 음식 아이템들 먼저 삭제 (Cascade 설정 안 되어 있을 경우 대비)
        supabase.table("meal_items").delete().eq("meal_id", meal_id).execute()
        # 2. 부모 로그 삭제
        res = supabase.table("meal_logs").delete().eq("id", meal_id).execute()
        
        return {"status": "success", "message": "삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 중 오류 발생: {str(e)}")

# 6. 수정 (Update)
@router.put("/{meal_id}")
async def update_meal(meal_id: str, request: MealCreateRequest):
    try:
        # 1. 부모 정보 업데이트
        supabase.table("meal_logs").update({
            "total_calories": request.total_calories,
            "total_carbs": request.total_carbs,
            "total_protein": request.total_protein,
            "total_fat": request.total_fat,
            "ai_advice": request.ai_advice
        }).eq("id", meal_id).execute()

        # 2. 기존 음식 아이템 싹 지우고 새로 갈아끼우기 (가장 깔끔한 방식)
        supabase.table("meal_items").delete().eq("meal_id", meal_id).execute()
        
        items_data = []
        for item in request.final_foods:
            items_data.append({
                "meal_id": meal_id,
                "food_name": item.food_name,
                "calories": item.calories,
                "carbs": item.carbs,
                "protein": item.protein,
                "fat": item.fat
            })
        supabase.table("meal_items").insert(items_data).execute()

        return {"status": "success", "message": "수정되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수정 중 오류 발생: {str(e)}")