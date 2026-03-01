from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0"}

@router.post("/process")
async def process_data(payload: dict):
    result = transform(payload)
    return {"result": result}
