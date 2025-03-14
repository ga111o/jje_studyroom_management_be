from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3
import uuid
from database import get_db_dependency
from datetime import datetime, time, timedelta

router = APIRouter()

class RegistrationRequest(BaseModel):
    name: str
    grade: int
    class_number: int
    student_number: int
    session_id: int
    seat_row: str
    seat_col: str

class CancelRegistrationRequest(BaseModel):
    reason: Optional[str] = None


# 야자 신청
@router.post("/")
def register_study_session(request: RegistrationRequest, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Generate unique ID for registration
    registration_id = str(uuid.uuid4())
    
    # Get current date in YYYY-MM-DD format
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get current timestamp
    now = datetime.now()
    registered_at = now.isoformat()
    
    # Create student_id in format grade-class-number
    student_id = f"{request.grade}-{request.class_number}-{request.student_number}"
    
    # Check if study session exists
    cursor.execute("SELECT * FROM study_session WHERE id = ?", (request.session_id,))
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    # Check if registration is within the allowed time window
    start_time_str = session["start_time"]
    
    # 시간 문자열("HH:MM" 형식)을 datetime 객체로 변환
    today = datetime.now().date()
    hour, minute = map(int, start_time_str.split(':'))
    start_time = datetime.combine(today, time(hour=hour, minute=minute))
    
    minutes_before = session["minutes_before"]
    minutes_after = session["minutes_after"]
    
    registration_start = start_time - timedelta(minutes=minutes_before)
    registration_end = start_time + timedelta(minutes=minutes_after)
    
    if now < registration_start or now > registration_end:
        formatted_start = registration_start.strftime("%H:%M")
        formatted_end = registration_end.strftime("%H:%M")
        raise HTTPException(
            status_code=403, 
            detail=f"신청 가능 시간이 아닙니다! 신청 가능 시간: {formatted_start} ~ {formatted_end}"
        )
    
    # Check if student is eligible for this session based on grade
    grade_field = f"{['one', 'two', 'three'][request.grade-1]}_grade"
    if not session[grade_field]:
        raise HTTPException(status_code=403, detail=f"Grade {request.grade} is not eligible for this study session")
    
    # Check if the seat exists in the room
    cursor.execute("SELECT layout FROM study_room WHERE id = ?", (session["room_id"],))
    room = cursor.fetchone()
    if not room:
        raise HTTPException(status_code=404, detail="Study room not found")
    
    import json
    layout = json.loads(room["layout"])
    
    # Validate seat coordinates
    try:
        row_idx = int(request.seat_row)
        col_idx = int(request.seat_col)
        
        if row_idx < 0 or row_idx >= len(layout) or col_idx < 0 or col_idx >= len(layout[row_idx]):
            raise HTTPException(status_code=400, detail="Invalid seat coordinates")
        
        if layout[row_idx][col_idx] == "aisle":
            raise HTTPException(status_code=400, detail="Cannot register for an aisle")
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid seat coordinates")
    
    # Check if seat is already taken for this session and date
    cursor.execute("""
        SELECT * FROM registration 
        WHERE session_id = ? AND date = ? AND seat_id_row = ? AND seat_id_col = ? AND cancelled = 0
    """, (request.session_id, current_date, request.seat_row, request.seat_col))
    
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="This seat is already taken")
    
    # Check if student already has a registration for this session and date
    cursor.execute("""
        SELECT * FROM registration 
        WHERE session_id = ? AND date = ? AND student_id = ? AND cancelled = 0
    """, (request.session_id, current_date, student_id))
    
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="You already have a registration for this session")
    
    # Insert registration
    cursor.execute("""
        INSERT INTO registration 
        (id, name, grade, class, number, student_id, session_id, seat_id_row, seat_id_col, 
         date, registered_at, cancelled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        registration_id, request.name, request.grade, request.class_number, request.student_number,
        student_id, request.session_id, request.seat_row, request.seat_col, 
        current_date, registered_at
    ))
    
    db.commit()
    
    return {
        "message": "Registration successful",
        "registration": {
            "id": registration_id,
            "name": request.name,
            "grade": request.grade,
            "class": request.class_number,
            "number": request.student_number,
            "student_id": student_id,
            "session_id": request.session_id,
            "seat": {
                "row": request.seat_row,
                "col": request.seat_col
            },
            "date": current_date,
            "registered_at": registered_at
        }
    }

