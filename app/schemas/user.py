from pydantic import BaseModel, EmailStr, Field

# 회원가입 요청 데이터
class UserCreate(BaseModel):
    email: EmailStr  # 이메일 형식이 맞는지 자동 검사
    password: str = Field(..., min_length=8) # 최소 8자 이상
    user_name: str

# 로그인 요청 데이터
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# API 응답 시 유저 정보를 보여줄 때 (비밀번호는 제외!)
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    user_name: str
    
    class Config:
        from_attributes = True # DB 객체를 Pydantic 모델로 변환 허용