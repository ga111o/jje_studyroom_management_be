from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import sqlite3
import json
import uuid
from database import get_db_dependency
from datetime import datetime
from token_ import verify_token

router = APIRouter()

class CreateStudySessionRequest(BaseModel):
    name: str
    start_time: str
    end_time: str
    one_grade: bool
    two_grade: bool
    three_grade: bool
    minutes_before: int
    minutes_after: int
    room_id: str

class UpdateStudySessionRequest(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    one_grade: Optional[bool] = None
    two_grade: Optional[bool] = None
    three_grade: Optional[bool] = None
    minutes_before: Optional[int] = None
    minutes_after: Optional[int] = None
    room_id: Optional[str] = None

@router.post("/")
def create_study_session(request: CreateStudySessionRequest, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if study room exists
    cursor.execute("SELECT id FROM study_room WHERE id = ?", (request.room_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Study room not found")
    
    # Check if study session with the same name already exists
    cursor.execute("SELECT id FROM study_session WHERE name = ?", (request.name,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Study session with this name already exists")
    
    # Insert into database with auto-incrementing ID
    cursor.execute(
        """INSERT INTO study_session 
           (name, start_time, end_time, one_grade, two_grade, three_grade, 
            minutes_before, minutes_after, room_id) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request.name, request.start_time, request.end_time, 
         request.one_grade, request.two_grade, request.three_grade,
         request.minutes_before, request.minutes_after, request.room_id)
    )
    db.commit()
    
    # Get the auto-generated ID
    session_id = cursor.lastrowid
    
    return {
        "message": "Study session created successfully",
        "study_session": {
            "id": session_id,
            "name": request.name,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "one_grade": request.one_grade,
            "two_grade": request.two_grade,
            "three_grade": request.three_grade,
            "minutes_before": request.minutes_before,
            "minutes_after": request.minutes_after,
            "room_id": request.room_id
        }
    }

@router.get("/")
def get_study_sessions(db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.name, s.start_time, s.end_time, 
               s.one_grade, s.two_grade, s.three_grade,
               s.minutes_before, s.minutes_after, 
               s.room_id, r.name as room_name
        FROM study_session s
        JOIN study_room r ON s.room_id = r.id
    """)
    
    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "id": row["id"],
            "name": row["name"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "one_grade": bool(row["one_grade"]),
            "two_grade": bool(row["two_grade"]),
            "three_grade": bool(row["three_grade"]),
            "minutes_before": row["minutes_before"],
            "minutes_after": row["minutes_after"],
            "room": {
                "id": row["room_id"],
                "name": row["room_name"]
            }
        })
    
    return {"study_sessions": sessions}

@router.get("/{session_id}")
def get_specific_study_session(session_id: str, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.name, s.start_time, s.end_time, 
               s.one_grade, s.two_grade, s.three_grade,
               s.minutes_before, s.minutes_after, 
               s.room_id, r.name as room_name
        FROM study_session s
        JOIN study_room r ON s.room_id = r.id
        WHERE s.id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    return {
        "study_session": {
            "id": row["id"],
            "name": row["name"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "one_grade": bool(row["one_grade"]),
            "two_grade": bool(row["two_grade"]),
            "three_grade": bool(row["three_grade"]),
            "minutes_before": row["minutes_before"],
            "minutes_after": row["minutes_after"],
            "room": {
                "id": row["room_id"],
                "name": row["room_name"]
            }
        }
    }

@router.put("/{session_id}")
def update_specific_study_session(session_id: str, request: UpdateStudySessionRequest, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if study session exists
    cursor.execute("SELECT * FROM study_session WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    # Check if room exists if room_id is provided
    if request.room_id:
        cursor.execute("SELECT id FROM study_room WHERE id = ?", (request.room_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Study room not found")
    
    # Check if new name is already taken by another session
    if request.name and request.name != row["name"]:
        cursor.execute("SELECT id FROM study_session WHERE name = ? AND id != ?", (request.name, session_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Another study session with this name already exists")
    
    # Prepare update data
    update_fields = []
    params = []
    
    for field, value in request.dict(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = ?")
            params.append(value)
    
    if not update_fields:
        return {"message": "No fields to update"}
    
    # Add session_id to params
    params.append(session_id)
    
    # Update database
    cursor.execute(
        f"UPDATE study_session SET {', '.join(update_fields)} WHERE id = ?",
        params
    )
    db.commit()
    
    # Get updated session
    cursor.execute("""
        SELECT s.id, s.name, s.start_time, s.end_time, 
               s.one_grade, s.two_grade, s.three_grade,
               s.minutes_before, s.minutes_after, 
               s.room_id, r.name as room_name
        FROM study_session s
        JOIN study_room r ON s.room_id = r.id
        WHERE s.id = ?
    """, (session_id,))
    
    updated_row = cursor.fetchone()
    
    return {
        "message": "Study session updated successfully",
        "study_session": {
            "id": updated_row["id"],
            "name": updated_row["name"],
            "start_time": updated_row["start_time"],
            "end_time": updated_row["end_time"],
            "one_grade": bool(updated_row["one_grade"]),
            "two_grade": bool(updated_row["two_grade"]),
            "three_grade": bool(updated_row["three_grade"]),
            "minutes_before": updated_row["minutes_before"],
            "minutes_after": updated_row["minutes_after"],
            "room": {
                "id": updated_row["room_id"],
                "name": updated_row["room_name"]
            }
        }
    }

@router.delete("/{session_id}")
def delete_specific_study_session(session_id: str, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if study session exists and get its details before deletion
    cursor.execute("""
        SELECT s.id, s.name, s.start_time, s.end_time, 
               s.one_grade, s.two_grade, s.three_grade,
               s.minutes_before, s.minutes_after, 
               s.room_id, r.name as room_name
        FROM study_session s
        JOIN study_room r ON s.room_id = r.id
        WHERE s.id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    # Delete from database
    cursor.execute("DELETE FROM study_session WHERE id = ?", (session_id,))
    db.commit()
    
    return {
        "message": "Study session deleted successfully",
        "study_session": {
            "id": row["id"],
            "name": row["name"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "one_grade": bool(row["one_grade"]),
            "two_grade": bool(row["two_grade"]),
            "three_grade": bool(row["three_grade"]),
            "minutes_before": row["minutes_before"],
            "minutes_after": row["minutes_after"],
            "room": {
                "id": row["room_id"],
                "name": row["room_name"]
            }
        }
    }

@router.get("/{session_id}/registrations/{yyyy}/{mm}/{dd}")
def get_session_registrations_by_date(
    session_id: str, 
    yyyy: str, 
    mm: str, 
    dd: str, 
    request: Request,
    db: sqlite3.Connection = Depends(get_db_dependency)
):
    # 토큰 검증
    is_authenticated = False
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if payload:
            is_authenticated = True
    
    cursor = db.cursor()

    date = f"{yyyy}-{mm}-{dd}"
    
    # Check if study session exists
    cursor.execute("SELECT * FROM study_session WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    
    # Get the room layout
    cursor.execute("SELECT layout FROM study_room WHERE id = ?", (session["room_id"],))
    room = cursor.fetchone()
    if not room or not room["layout"]:
        raise HTTPException(status_code=404, detail="Room layout not found")
    
    layout = json.loads(room["layout"])
    
    # Get all registrations for this session and date
    cursor.execute("""
        SELECT r.id, r.name, r.grade, r.class, r.number, r.student_id,
               r.seat_id_row, r.seat_id_col, r.registered_at, r.cancelled
        FROM registration r
        WHERE r.session_id = ? AND r.date = ? AND r.cancelled = 0
    """, (session_id, date))
    
    registrations = {}
    for reg in cursor.fetchall():
        registrations[(reg["seat_id_row"], reg["seat_id_col"])] = {
            "id": reg["id"],
            "name": reg["name"],
            "grade": reg["grade"],
            "class": reg["class"],
            "number": reg["number"],
            "student_id": reg["student_id"],
            "registered_at": reg["registered_at"]
        }
    
    # Create a layout with student information
    seat_layout = []
    for row_idx, row in enumerate(layout):
        seat_row = []
        for col_idx, seat in enumerate(row):
            if seat == "aisle":
                seat_row.append({"type": "aisle"})
            else:
                seat_info = {
                    "type": "seat",
                    "id": seat,
                    "row": row_idx,
                    "col": col_idx,
                    "occupied": False,
                    "student": None
                }
                
                # Check if this seat is occupied
                if (str(row_idx), str(col_idx)) in registrations:
                    seat_info["occupied"] = True
                    
                    # 인증된 사용자에게만 학생 정보 제공
                    if is_authenticated:
                        seat_info["student"] = registrations[(str(row_idx), str(col_idx))]
                    else:
                        # 인증되지 않은 사용자에게는 학생 정보를 가림
                        seat_info["student"] = {
                            "id": "",
                            "name": "",
                            "grade": 0,
                            "class": 0,
                            "number": 0,
                            "student_id": "",
                            "registered_at": ""
                        }
                
                seat_row.append(seat_info)
        
        seat_layout.append(seat_row)
    
    # Get total registration count
    registration_count = len(registrations)
    
    return {
        "session_id": session_id,
        "date": date,
        "layout": seat_layout,
        "registration_count": registration_count
    }
