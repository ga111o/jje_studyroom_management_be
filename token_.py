import jwt
import datetime
from typing import Dict, Optional, Union

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SECRET_KEY = "ㅑ'ㅡ ㅈㅁㅅ초ㅑㅜㅎ ㅠㅁ딬'ㄴ ㅣㅑㅍㄷ ㄴㅅㄱㄷ므 ㅜㅐㅈ, ㅑ 소ㅑㅜㅏ 녿 ㅑㄴ 내ㅐㅐㅐ 려ㅜㅜㅛ"
ALGORITHM = "HS256"
ACCESS_KEY = "gudrnToa"

def generate_token(input_key: str) -> Optional[str]:
    if input_key != ACCESS_KEY:
        return None
    
    payload = {
        "sub": "user",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12) 
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    logger.debug(f"token: {token}")
    return token

def verify_token(token: str) -> Union[Dict, bool]:
    try:
        logger.debug("토큰 검증 시도 중...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.error(f"ExpiredSignatureError: {e}")
        return False
    except jwt.InvalidTokenError as e:
        logger.error(f"InvalidTokenError: {e}")
        return False
    except Exception as e:
        logger.error(f"Exception: {e}")
        return False

if __name__ == "__main__":
    token = generate_token(ACCESS_KEY)
    print(f"token: {token}")
    payload = verify_token(token)
    print(f"payload: {payload}")
