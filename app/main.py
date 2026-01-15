from fastapi import FastAPI
from app.api.meals import router as meals_router
from app.api.analyze import router as analyze_router

app = FastAPI(title="FoodBrain API")

# 라우터 등록
app.include_router(meals_router, prefix="/api/meals", tags=["Meals"])

@app.get("/")
async def root():
    return {"message": "FoodBrain API is running on Docker!"}