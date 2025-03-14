from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from token_ import generate_token

router = APIRouter()

class TokenRequest(BaseModel):
    key: str

@router.post("/")
def get_token(request: TokenRequest):
    """
    인증 키를 받아 JWT 토큰을 발급합니다.
    
    Args:
        request: 인증 키가 포함된 요청 객체
        
    Returns:
        성공 시 JWT 토큰, 실패 시 401 Unauthorized 에러
    """
    token = generate_token(request.key)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 키가 올바르지 않습니다."
        )
    
    return {"token": token, "token_type": "bearer"}
