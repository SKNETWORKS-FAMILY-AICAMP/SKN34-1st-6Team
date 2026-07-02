import pandas as pd
import os


# 최종 조건 불일치 행 삭제
# 열마다 문자와 숫자 통일
# 한글 열 이름 영어로 변경 

# ==========================================
# 1. 데이터 불러오기
# ==========================================
file_path   = "data/crawled/google_review_after_kakao.csv"
output_path = "data/processed/parking_review_crawled.csv"

os.makedirs("data/processed", exist_ok=True)

print(f"📁 [{file_path}] 파일을 불러오는 중...")
try:
    df = pd.read_csv(file_path, encoding='utf-8-sig')
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding='cp949')

target_col = '카카오맵_별점'
bg_col = '카카오맵_후기_URL'

initial_count = len(df)
print(f"📊 원본 데이터 건수: {initial_count}건")

# ==========================================
# 2. 전처리 작업 수행
# ==========================================
if target_col in df.columns:
    # (1) '평가 없음' 또는 '평가없음'을 '0'으로 변경
    df[target_col] = df[target_col].replace(['평가 없음', '평가없음'], '0')
    
    # (2) '조건 불일치'가 포함된 불량 행 완전 삭제
    df = df[~df[target_col].astype(str).str.contains('조건 불일치|조건불일치', na=False)]
    
    # (3) 살아남은 정상 데이터 중, BG열(후기 URL)이 비어있으면 '평가없음' 채우기
    if bg_col in df.columns:
        df[bg_col] = df[bg_col].replace(r'^\s*$', '평가없음', regex=True)
        df[bg_col] = df[bg_col].fillna('평가없음')
    
    # (4) 행이 삭제되면서 이빨이 빠진 인덱스를 초기화
    df = df.reset_index(drop=True)
    
    # (5) 향후 분석을 위해 별점과 리뷰수를 텍스트에서 진짜 숫자로 변환
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
    
    if '카카오맵_리뷰수' in df.columns:
        df['카카오맵_리뷰수'] = pd.to_numeric(df['카카오맵_리뷰수'], errors='coerce').fillna(0)

# ==========================================
# 🌟 3. 열 이름(컬럼명) 변경 로직 추가
# ==========================================
rename_dict = {
    '카카오맵_매칭된_주차장명': 'pk_rlname',
    '카카오맵_유사도':          'pk_sim',
    '카카오맵_별점':            'pk_rate',
    '카카오맵_리뷰수':          'pk_review',
    '카카오맵_URL':             'pk_url',
    '카카오맵_후기_URL':        'pk_reviewurl',
}

df = df.rename(columns=rename_dict)

# ==========================================
# 4. 결과 저장 및 안내
# ==========================================
final_count   = len(df)
deleted_count = initial_count - final_count

df.to_csv(output_path, index=False, encoding='utf-8-sig')

print("-" * 50)
print(f"🧹 전처리 완료!")
print(f"   ❌ 삭제된 조건 불일치 데이터: {deleted_count}건")
print(f"   ✅ 살아남은 유효 데이터: {final_count}건")
print(f"   🔗 리뷰 URL 결측치 '평가없음' 처리 완료")
print(f"   🏷️ 영어(영문) 컬럼명으로 완벽하게 변경 완료")
print(f"💾 깔끔하게 정제된 데이터가 [{output_path}] 파일로 저장되었습니다.")