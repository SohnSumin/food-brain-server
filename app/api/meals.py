from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from app.services.ai_service import analyze_meal_image
from app.schemas.meal import MealCreateRequest, AIAnalysisResponse
from app.core.config import supabase
from app.api.auth import get_current_user  # 인증 의존성 추가
from app.schemas.user import UserRead        # 유저 스키마 추가

router = APIRouter()

# 1. 이미지 분석 (인증 필요)
@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_diet_image(
    image: UploadFile = File(...),
    current_user: UserRead = Depends(get_current_user) # 인증 추가
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    image_bytes = await image.read()
    analysis_result = await analyze_meal_image(image_bytes, image.content_type)
    
    return analysis_result

# 2. 식단 기록 생성 (인증된 유저 ID 사용)
@router.post("/confirm")
async def confirm_and_save_meal(
    request: MealCreateRequest,
    current_user: UserRead = Depends(get_current_user) # 인증 추가
):
    try:
        # request.user_id 대신 토큰에서 추출한 current_user.id 사용
        log_data = {
            "user_id": current_user.id, 
            "total_calories": request.total_calories,
            "total_carbs": request.total_carbs,
            "total_protein": request.total_protein,
            "total_fat": request.total_fat,
            "ai_advice": request.ai_advice,
            "image_url": request.image_url
        }
        log_res = supabase.table("meal_logs").insert(log_data).execute()
        meal_id = log_res.data[0]['id']

        items_data = [
            {
                "meal_id": meal_id,
                "food_name": item.food_name,
                "calories": item.calories,
                "carbs": item.carbs,
                "protein": item.protein,
                "fat": item.fat
            } for item in request.final_foods
        ]
        supabase.table("meal_items").insert(items_data).execute()

        return {"status": "success", "meal_id": meal_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 중 오류 발생: {str(e)}")

# 3. 내 식단 목록 조회 (로그인한 유저 본인 것만)
@router.get("/list") # 경로에서 {user_id} 제거 (토큰에서 가져오므로)
async def get_meal_list(current_user: UserRead = Depends(get_current_user)):
    res = supabase.table("meal_logs")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

# 4. 상세 조회 (본인 확인 로직 추가 권장)
@router.get("/detail/{meal_id}")
async def get_meal_detail(
    meal_id: str,
    current_user: UserRead = Depends(get_current_user)
):
    res = supabase.table("meal_logs")\
        .select("*, meal_items(*)")\
        .eq("id", meal_id)\
        .eq("user_id", current_user.id)\
        .single()\
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="식단 정보를 찾을 수 없거나 권한이 없습니다.")
    return res.data

# 5. 삭제 (본인 확인 로직 포함)
@router.delete("/{meal_id}")
async def delete_meal(
    meal_id: str,
    current_user: UserRead = Depends(get_current_user)
):
    try:
        # 내 식단이 맞는지 확인하며 삭제
        res = supabase.table("meal_logs").delete().eq("id", meal_id).eq("user_id", current_user.id).execute()
        
        if not res.data:
            raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
            
        return {"status": "success", "message": "삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 중 오류 발생: {str(e)}")

# 6. 수정 (Update)
@router.put("/{meal_id}")
async def update_meal(
    meal_id: str, 
    request: MealCreateRequest,
    current_user: UserRead = Depends(get_current_user)
):
    try:
        # 1. 먼저 해당 식단이 현재 로그인한 유저의 것인지 확인 (보안)
        check_res = supabase.table("meal_logs")\
            .select("id")\
            .eq("id", meal_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not check_res.data:
            raise HTTPException(status_code=403, detail="수정 권한이 없거나 존재하지 않는 식단입니다.")

        # 2. 부모 정보(meal_logs) 업데이트
        supabase.table("meal_logs").update({
            "total_calories": request.total_calories,
            "total_carbs": request.total_carbs,
            "total_protein": request.total_protein,
            "total_fat": request.total_fat,
            "ai_advice": request.ai_advice
            # image_url은 수정 시 변경될 수도 있고 아닐 수도 있으니 상황에 맞춰 추가
        }).eq("id", meal_id).execute()

        # 3. 기존 음식 아이템(meal_items) 싹 지우고 새로 삽입
        # 이 방식이 하나하나 비교해서 수정하는 것보다 정확하고 코드가 깔끔합니다.
        supabase.table("meal_items").delete().eq("meal_id", meal_id).execute()
        
        items_data = [
            {
                "meal_id": meal_id,
                "food_name": item.food_name,
                "calories": item.calories,
                "carbs": item.carbs,
                "protein": item.protein,
                "fat": item.fat
            } for item in request.final_foods
        ]
        supabase.table("meal_items").insert(items_data).execute()

        return {"status": "success", "message": "식단 정보가 성공적으로 수정되었습니다."}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수정 중 오류 발생: {str(e)}")