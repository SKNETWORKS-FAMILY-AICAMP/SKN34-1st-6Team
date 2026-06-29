"""
connection.py

[역할]
- MySQL(DB) 연결 설정

[기능]
1. DB 연결 생성
2. cursor 관리
3. 재사용 가능한 connection 객체 제공
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="parking_project"
    )