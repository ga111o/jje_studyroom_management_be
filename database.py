import sqlite3
from pathlib import Path
import threading

local_storage = threading.local()

SCHEMA = f"""
-- Study Room 테이블
CREATE TABLE IF NOT EXISTS study_room (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- "일맥관 2층", ...
    layout TEXT  -- JSON(dict) 형식으로 저장 # [["1", "2", "3", "aisle", "4", "5", "6"], ["1", "2", "3", "aisle", "4", "5", "6"], ...]
);

-- Study Session 테이블
CREATE TABLE IF NOT EXISTS study_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- "1학년 1차야자", "3학년 2차야자", ...
    start_time TEXT NOT NULL, -- 야자 시작 시간
    end_time TEXT NOT NULL, -- 야자 종료 시간
    one_grade BOOLEAN NOT NULL, -- 1학년 신청 가능 여부
    two_grade BOOLEAN NOT NULL, -- 2학년 신청 가능 여부
    three_grade BOOLEAN NOT NULL, -- 3학년 신청 가능 여부
    minutes_before INTEGER NOT NULL, -- 신청 가능 시간, 야자 시작 n분 전부터
    minutes_after INTEGER NOT NULL, -- 신청 가능 시간, 야자 시작 n분 후까지
    room_id INTEGER NOT NULL,
    FOREIGN KEY (room_id) REFERENCES study_room(id)
);

-- Issue Types 테이블
CREATE TABLE IF NOT EXISTS issue_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL
);

-- Registration 테이블
CREATE TABLE IF NOT EXISTS registration (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grade INTEGER NOT NULL,
    class INTEGER NOT NULL,
    number INTEGER NOT NULL,
    student_id TEXT NOT NULL, -- 학생 ID (grade-class-number)
    session_id INTEGER NOT NULL, -- 신청한 야자 id
    seat_id_row TEXT NOT NULL, -- 야자 자리 id 열
    seat_id_col TEXT NOT NULL, -- 야자 자리 id 행
    date TEXT NOT NULL, -- 야자 날짜 (YYYY-MM-DD)
    registered_at TEXT NOT NULL, -- 신청 시간
    cancelled BOOLEAN DEFAULT 0, -- 취소 여부
    cancelled_at TEXT, -- 취소 시간
    cancellation_reason TEXT, -- 취소 사유
    issue_type TEXT, -- 특이사항
    note TEXT, -- 비고
    FOREIGN KEY (session_id) REFERENCES study_session(id)
);
"""

def init_database():
    db_path = Path("database.db")
    
    db_exists = db_path.exists()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript(SCHEMA)
    
    conn.commit()
    conn.close()
    
    print(f"Database {'initialized' if not db_exists else 'verified'} at {db_path.absolute()}") 


def get_db():
    if not hasattr(local_storage, 'connection'):
        db_path = Path("database.db")
        local_storage.connection = sqlite3.connect(db_path)
        local_storage.connection.row_factory = sqlite3.Row
    
    return local_storage.connection

def get_db_dependency():
    db_path = Path("database.db")
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()

def close_db():
    if hasattr(local_storage, 'connection'):
        local_storage.connection.close()
        del local_storage.connection

