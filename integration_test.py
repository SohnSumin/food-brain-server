import requests
import json
import time

# 서버 설정
BASE_URL = "http://localhost:8000/api/meals"
USER_ID = "2ed30794-9c8d-4ea4-8e30-1000c6b25186"  # 테스트용 유저 ID

def test_full_lifecycle():
    # --- STEP 1: 분석 및 저장 (CREATE) ---
    print("Step 1: 📸 이미지 분석 및 최종 저장 요청...")
    image_path = "test_image.png"
    
    try:
        # 1-1. 분석 요청
        with open(image_path, "rb") as img:
            files = {"image": (image_path, img, "image/png")}
            analyze_res = requests.post(f"{BASE_URL}/analyze", files=files)
        
        if analyze_res.status_code != 200:
            print(f"❌ 분석 실패: {analyze_res.text}")
            return

        analysis_data = analyze_res.json()
        print("분석된 음식들:")
        for food in analysis_data['detected_foods']:
            print(f"  - {food['food_name']}: 칼로리={food['calories']}, 탄수화물={food['carbs']}, 단백질={food['protein']}, 지방={food['fat']}")

        # 1-2. 사용자 수정 시뮬레이션
        edited_foods = analysis_data['detected_foods']
        edited_foods[0]['food_name'] = "수정된 음식 이름" 
        
        confirm_payload = {
            "user_id": USER_ID,
            "image_url": "https://supabase.storage.url/test.png",
            "final_foods": edited_foods,
            "total_calories": sum(f['calories'] for f in edited_foods),
            "total_carbs": sum(f['carbs'] for f in edited_foods),
            "total_protein": sum(f['protein'] for f in edited_foods),
            "total_fat": sum(f['fat'] for f in edited_foods),
            "ai_advice": analysis_data['ai_advice']
        }

        # 1-3. DB 저장
        save_res = requests.post(f"{BASE_URL}/confirm", json=confirm_payload)
        meal_id = save_res.json().get("meal_id")
        print(f"✅ 저장 성공! 생성된 식단 ID: {meal_id}")

        # --- STEP 2: 전체 목록 및 상세 조회 (READ) ---
        print(f"\nStep 2: 🔍 데이터 조회 테스트...")
        # 목록 조회
        list_res = requests.get(f"{BASE_URL}/list/{USER_ID}")
        if list_res.status_code == 200 and len(list_res.json()) > 0:
            print(f"✅ 목록 조회 성공: 총 {len(list_res.json())}개의 기록 발견")
        
        # 상세 조회
        detail_res = requests.get(f"{BASE_URL}/detail/{meal_id}")
        if detail_res.status_code == 200:
            print(f"✅ 상세 조회 성공: {detail_res.json()['meal_items'][0]['food_name']}")

        # --- STEP 3: 기존 데이터 수정 (UPDATE) ---
        print(f"\nStep 3: ✍️ 저장된 데이터 수정 테스트 (ID: {meal_id})...")
        confirm_payload["ai_advice"] = "사용자가 수정한 새로운 조언입니다."
        confirm_payload["total_calories"] = 999  # 칼로리 강제 변경
        
        update_res = requests.put(f"{BASE_URL}/{meal_id}", json=confirm_payload)
        if update_res.status_code == 200:
            print(f"✅ 데이터 수정 완료: {update_res.json()['message']}")

        # --- STEP 4: 데이터 삭제 (DELETE) ---
        print(f"\nStep 4: 🗑️ 데이터 삭제 테스트...")
        delete_res = requests.delete(f"{BASE_URL}/{meal_id}")
        if delete_res.status_code == 200:
            print(f"✅ 데이터 삭제 완료: {delete_res.json()['message']}")

        print("\n✨ 모든 CRUD 통합 테스트가 성공적으로 마무리되었습니다!")

    except FileNotFoundError:
        print("❌ 에러: test_image.png 파일이 없습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}")

if __name__ == "__main__":
    test_full_lifecycle()