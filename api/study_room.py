from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
import sqlite3
import json
import uuid
from database import get_db_dependency

router = APIRouter()

class CreateStudyroomRequest(BaseModel):
    name: str
    layout: List[List[str]]  # Format: [["1", "2", "3", "aisle", "4", "5", "6"], ["7", "8", "9", "aisle", "10", "11", "12"], ...]

class UpdateStudyroomRequest(BaseModel):
    name: Optional[str] = None
    layout: Optional[List[List[str]]] = None

@router.post("/")
def create_studyroom(request: CreateStudyroomRequest, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if studyroom with the same name already exists
    cursor.execute("SELECT id FROM study_room WHERE name = ?", (request.name,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Studyroom with this name already exists")
        
    # Insert into database with auto-incrementing ID
    cursor.execute(
        "INSERT INTO study_room (name, layout) VALUES (?, ?)",
        (request.name, json.dumps(request.layout))
    )
    db.commit()
    
    # Get the auto-generated ID
    room_id = cursor.lastrowid
    
    return {
        "message": "Studyroom created successfully", 
        "studyroom": {
            "id": room_id,
            "name": request.name,
            "layout": request.layout
        }
    }

@router.get("/")
def get_studyrooms(db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    cursor.execute("SELECT id, name, layout FROM study_room")
    
    studyrooms = []
    for row in cursor.fetchall():
        layout = json.loads(row["layout"]) if row["layout"] else {}
        # Calculate seats from layout
        
        studyrooms.append({
            "id": row["id"],
            "name": row["name"],
            "layout": layout
        })
    
    return {"studyrooms": studyrooms}

@router.get("/{room_id}")
def get_studyroom(room_id: str, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    cursor.execute("SELECT id, name, layout FROM study_room WHERE id = ?", (room_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Studyroom not found")
    
    layout = json.loads(row["layout"]) if row["layout"] else {}
    # Calculate seats from layout
    
    return {
        "studyroom": {
            "id": row["id"],
            "name": row["name"],
            "layout": layout
        }
    }

@router.put("/{room_id}")
def update_studyroom(room_id: str, request: UpdateStudyroomRequest, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if studyroom exists
    cursor.execute("SELECT name, layout FROM study_room WHERE id = ?", (room_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Studyroom not found")
    
    current_name = row["name"]
    current_layout = json.loads(row["layout"]) if row["layout"] else {}
    # Calculate current seats from layout
    
    # Check if new name is already taken by another studyroom
    if request.name and request.name != current_name:
        cursor.execute("SELECT id FROM study_room WHERE name = ? AND id != ?", (request.name, room_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Another studyroom with this name already exists")
    
    # Prepare update data
    new_name = request.name if request.name is not None else current_name
    new_layout = request.layout if request.layout is not None else current_layout
    

    # Update database - removed seat_count column
    cursor.execute(
        "UPDATE study_room SET name = ?, layout = ? WHERE id = ?",
        (new_name, json.dumps(new_layout), room_id)
    )
    db.commit()
    
    return {
        "message": "Studyroom updated successfully",
        "studyroom": {
            "id": room_id,
            "name": new_name,
            "layout": new_layout
        }
    }

@router.delete("/{room_id}")
def delete_studyroom(room_id: str, db: sqlite3.Connection = Depends(get_db_dependency)):
    cursor = db.cursor()
    
    # Check if studyroom exists
    cursor.execute("SELECT id, name, layout FROM study_room WHERE id = ?", (room_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Studyroom not found")
    
    layout = json.loads(row["layout"]) if row["layout"] else {}
    # Calculate seats from layout
    
    # Delete from database
    cursor.execute("DELETE FROM study_room WHERE id = ?", (room_id,))
    db.commit()
    
    return {
        "message": "Studyroom deleted successfully",
        "studyroom": {
            "id": row["id"],
            "name": row["name"],
            "layout": layout
        }
    }

