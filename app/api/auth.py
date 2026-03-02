import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.schemas.user import UserRead  # 이미 작성하신 유저 읽기용 스키마 임포트

# 클라이언트 헤더에서 'Bearer <TOKEN>'을 추출
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserRead:
    """
    JWT를 검증하고, 유저 정보를 스키마 객체에 담아 반환합니다.
    """
    token = credentials.credentials

    try:
        # 1. 토큰 해독 (Supabase JWT Secret 사용)
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )

        # 2. 유저 식별자 추출 (Supabase는 'sub' 필드에 UUID를 담음)
        user_id: str = payload.get("sub")
        user_email: str = payload.get("email") # Supabase 토큰에는 이메일도 포함되어 있음

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다. (ID 누락)"
            )

        # 3. schema/user.py에서 정의한 모델로 변환하여 반환
        # (DB 조회가 굳이 필요 없다면 토큰 정보만으로 객체 생성 가능)
        return UserRead(
            id=user_id,
            email=user_email,
            # 스키마에 정의된 다른 필드들이 있다면 payload에서 꺼내어 매핑
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="인증 토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 인증 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인증 처리 중 오류: {str(e)}")