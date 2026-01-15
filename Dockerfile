FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (이미지 처리 등을 위해 필요할 수 있음)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI 실행 (0.0.0.0으로 열어야 도커 외부에서 접속 가능)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]