from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uuid
from datetime import datetime
from database import get_db_dependency

router = APIRouter()

class IssueTypeBase(BaseModel):
    description: str

class IssueTypeCreate(IssueTypeBase):
    pass

class IssueType(IssueTypeBase):
    id: str
    
    class Config:
        orm_mode = True

# 이슈 타입 생성
@router.post("/", response_model=IssueType, status_code=status.HTTP_201_CREATED)
async def create_issue_type(issue_type: IssueTypeCreate, db: sqlite3.Connection = Depends(get_db_dependency)):
    """이슈 타입 생성"""
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO issue_types (description) VALUES (?)",
        (issue_type.description,)
    )
    db.commit()
    
    # Get the auto-generated ID and convert to string
    issue_id = str(cursor.lastrowid)
    
    return {"id": issue_id, "description": issue_type.description}

# 이슈 타입 전체 목록 조회
@router.get("/", response_model=List[IssueType])
async def get_issue_types(db: sqlite3.Connection = Depends(get_db_dependency)):
    """이슈 타입 목록 조회"""
    cursor = db.cursor()
    cursor.execute("SELECT id, description FROM issue_types")
    issue_types = cursor.fetchall()
    
    return [{"id": str(row["id"]), "description": row["description"]} for row in issue_types]

# 특정 이슈 수정
@router.put("/{issue_id}", response_model=IssueType)
async def update_specific_issue_type(
    issue_id: str, issue_type: IssueTypeCreate, db: sqlite3.Connection = Depends(get_db_dependency)
):
    """이슈 타입 수정"""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM issue_types WHERE id = ?", (issue_id,))
    existing_issue = cursor.fetchone()
    
    if not existing_issue:
        raise HTTPException(status_code=404, detail="Issue type not found")
    
    cursor.execute(
        "UPDATE issue_types SET description = ? WHERE id = ?",
        (issue_type.description, issue_id)
    )
    db.commit()
    
    return {"id": issue_id, "description": issue_type.description}

# 특정 이슈 타입 삭제
@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specific_issue_type(issue_id: str, db: sqlite3.Connection = Depends(get_db_dependency)):
    """이슈 타입 삭제"""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM issue_types WHERE id = ?", (issue_id,))
    existing_issue = cursor.fetchone()
    
    if not existing_issue:
        raise HTTPException(status_code=404, detail="Issue type not found")
    
    cursor.execute("DELETE FROM issue_types WHERE id = ?", (issue_id,))
    db.commit()
    
    return None

# 특정 등록에 이슈 할당
class IssueAssignment(BaseModel):
    issue_description: str

@router.post("/assign/{registration_id}", status_code=status.HTTP_200_OK)
async def assign_issue_to_registration(
    registration_id: str, 
    issue_data: IssueAssignment, 
    db: sqlite3.Connection = Depends(get_db_dependency)
):
    """특정 야자 신청자에게 이슈 할당"""
    cursor = db.cursor()
    
    # 등록 정보 확인
    cursor.execute("SELECT id FROM registration WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # 이슈 설명 업데이트
    cursor.execute(
        "UPDATE registration SET issue_type = ? WHERE id = ?",
        (issue_data.issue_description, registration_id)
    )
    db.commit()
    
    return {"message": "Issue assigned successfully", "registration_id": registration_id}

# 특정 등록에 메모 작성
class MemoAssignment(BaseModel):
    memo: str

@router.post("/memo/{registration_id}", status_code=status.HTTP_200_OK)
async def add_memo_to_registration(
    registration_id: str, 
    memo_data: MemoAssignment, 
    db: sqlite3.Connection = Depends(get_db_dependency)
):
    """특정 야자 신청자에게 메모 작성"""
    cursor = db.cursor()
    
    # 등록 정보 확인
    cursor.execute("SELECT id FROM registration WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    # 메모 업데이트
    cursor.execute(
        "UPDATE registration SET note = ? WHERE id = ?",
        (memo_data.memo, registration_id)
    )
    db.commit()
    
    return {"message": "Memo added successfully", "registration_id": registration_id}

# 특정 학생의 이슈 타입과 메모 조회
class IssueAndNoteResponse(BaseModel):
    registration_id: str
    issue_type: Optional[str] = None
    note: Optional[str] = None

@router.get("/student/{registration_id}", response_model=IssueAndNoteResponse)
async def get_student_issue_and_note(
    registration_id: str, 
    db: sqlite3.Connection = Depends(get_db_dependency)
):
    """특정 학생의 이슈 타입과 메모 조회"""
    cursor = db.cursor()
    
    # 등록 정보 확인
    cursor.execute("SELECT id, issue_type, note FROM registration WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return {
        "registration_id": registration_id,
        "issue_type": registration["issue_type"],
        "note": registration["note"]
    }

