import os
from fastapi import FastAPI, APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from database import init_database

from token_ import verify_token
from api.auth import router as auth_router
from api.study_room import router as studyroom_router
from api.study_session import router as study_router
from api.issue import router as issue_router
from api.registration import router as registration_router
# from api.student.registration import router as registration_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
def roooot():
    return "ga111o!"

# @app.middleware("http")
# async def token_validator(request: Request, call_next):
#     except_path = ["/", "/docs", "/auth/", "/openapi.json", "/registration/", "/studyroom/"]
    
#     if request.url.path in except_path:
#         print(f"except path: {request.url.path}")
#         return await call_next(request)
    
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return JSONResponse(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             content={"detail": "not auth header"}
#         )
    
#     token = auth_header.split(" ")[1]
#     # print(f"token: {token}")
#     payload = verify_token(token)
#     print(f"payload: {payload}")
#     if not payload:
#         return JSONResponse(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             content={"detail": "not payload"}
#         )

#     return await call_next(request)


init_database()
app.include_router(router=auth_router, prefix="/auth", tags=["auth"])
app.include_router(router=studyroom_router, prefix="/studyroom", tags=["studyroom"])
app.include_router(router=study_router, prefix="/session", tags=["session"])
app.include_router(router=issue_router, prefix="/issue", tags=["issue"])
app.include_router(router=registration_router, prefix="/registration", tags=["registration"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=44920, reload=True)