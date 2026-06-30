"""
scoring.py

[역할]
- 주차장 난이도 및 혼잡도 계산

[기능]
1. 요금 기반 점수 계산
2. 주차면수 기반 점수 계산
3. 역세권 기반 점수 계산
4. 최종 난이도 점수 계산
5. 난이도 등급(A~D) 산출
6. 평일/주말 혼잡도 패턴 제공
"""


# 설정값
SUBWAY_RADIUS_M = 500


# 혼잡도 패턴

WEEKDAY_PATTERN = {
     0:"여유",  1:"여유",  2:"여유",  3:"여유",
     4:"여유",  5:"여유",  6:"여유",  7:"보통",
     8:"혼잡",  9:"혼잡", 10:"보통", 11:"보통",
    12:"보통", 13:"보통", 14:"보통", 15:"보통",
    16:"보통", 17:"혼잡", 18:"혼잡", 19:"혼잡",
    20:"보통", 21:"보통", 22:"여유", 23:"여유",
} #평일

WEEKEND_PATTERN = {
     0:"여유",  1:"여유",  2:"여유",  3:"여유",
     4:"여유",  5:"여유",  6:"여유",  7:"여유",
     8:"여유",  9:"여유", 10:"보통", 11:"보통",
    12:"혼잡", 13:"혼잡", 14:"혼잡", 15:"혼잡",
    16:"보통", 17:"보통", 18:"보통", 19:"여유",
    20:"여유", 21:"여유", 22:"여유", 23:"여유",
} #주말


# 요금 점수
def calc_fee_score(fee):
    """
    기본요금 점수 (0~40점)
    """

    if fee <= 0: #무료 또는 요금정보x
        return 0
    
    elif fee <= 500: #0 ~ 500원 : 0~10점
        return round(fee / 500 * 10)
    
    elif fee <= 1000: #500~1000원 : 10~25점
        return round(10 + (fee - 500) / 500 * 15)
    
    elif fee <= 2000: #1001~2000원 : 25~35점
        return round(25 + (fee - 1000) / 1000 * 10)
    
    else: #2000원 초과 :최대 점수(40점)
        return 40


# 주차면수 점수
def calc_capacity_score(capacity):
    """
    주차면수 점수 (0~30점)
    면수가 적을수록 높은 점수
    """

    if capacity <= 0: # 면수 정보가 없는 경우 중간 점수
        return 15
    
    elif capacity <= 30: # 30면 이하 : 매우 혼잡할 가능성
        return 30
    
    elif capacity <= 100: # 31 ~ 100면 : 면수가 증가할수록 점수 감소
        return round(30 - (capacity - 30) / 70 * 15)
    
    elif capacity <= 500: # 101 ~ 500면 : 점진적으로 감소
        return round(15 - (capacity - 100) / 400 * 10)
    
    else: # 500면 초과 : 매우 넓은 주차장
        return 5



# 역세권 점수
def calc_subway_score(distance):
    """
    역세권 점수 (0~30점)
    """

    if distance is None or distance == "": # 거리 정보가 없으면 매우 먼 거리로 처리
        distance = 9999 
      

    if distance <= SUBWAY_RADIUS_M: # 500m 이내 : 역세권
        return 30
    elif distance <= 1000: # 501 ~ 1000m : 거리가 멀어질수록 점수 감소
        return round(
            30 * (1 - (distance - SUBWAY_RADIUS_M) / 500)
        )
    else:  # 1000m 초과 : 역세권 영향 없음
        return 0


# ----------------------------------------
# 등급 계산
# ----------------------------------------

def calc_grade(total_score):
    """
    난이도 등급 반환
    """
    # 총점이 높을수록 난이도가 높음
    if total_score >= 80:
        return "D"
    elif total_score >= 55:
        return "C"
    elif total_score >= 30:
        return "B"
    else:
        return "A"


# ----------------------------------------
# 최종 점수 계산
# ----------------------------------------

def calc_score(fee, parking_space, distance):
    """
    최종 난이도 점수 계산
    """

    # 항목별 점수 계산
    fee_score = calc_fee_score(fee)
    capacity_score = calc_capacity_score(parking_space)
    subway_score = calc_subway_score(distance)

    # 총점 계산
    total_score = (
        fee_score +
        capacity_score +
        subway_score
    )

    # 계산 결과 반환
    return {
        "요금점수": fee_score,
        "면수점수": capacity_score,
        "역세권점수": subway_score,
        "난이도점수": total_score,
        "난이도등급": calc_grade(total_score)
    }