# :red_car: 서울시 스마트 공영주차장 정보 시스템

## :pushpin: 프로젝트 소개

공공데이터 API와  지도 리뷰를 활용하여
서울시 사영,공영 주차장 정보를 제공하는 웹 서비스입니다.

---

## :tools: 사용 기술

- Python
- Requests
- Pandas
- Selenium
- MySQL
- SQLAlchemy
- Streamlit

---

## :open_file_folder: 프로젝트 구조

parking_project/
├── api/ # 공공데이터 API 수집
│ └── parking_api.py
│
├── crawler/ # Selenium 크롤링
│ └── review.py
│
├── preprocessing/ # 데이터 전처리
│ ├── api_preprocess.py
│ ├── review_preprocess.py
│ └── merge.py
│
├── database/ # DB 연결
│ ├── connection.py
│ └── select_data.py
│
├── streamlit/ # 대시보드
│ ├── app.py # 메인 실행 파일
│ └── pages/
│ ├── map_view.py
│ ├── congestion.py
│ └── analysis.py
│
├── utils/ # 공통 함수
│ ├── scoring.py # 혼잡도 점수 계산
│ └── helpers.py
│
├── data/
│ ├── raw/ # API / 크롤링 원본 데이터
│ └── processed/ # 전처리 완료 데이터
│
├── logs/ # 실행 로그
├── tests/ # 테스트 코드 (선택)
├── notebooks/ # 분석 실험 (선택)
│
├── .env # API KEY / DB 정보 (절대 Git 업로드 금지)
├── .gitignore
├── requirements.txt
├── README.md
└── config.py

---

## :rocket: 실행 방법

### 1. 저장소 다운로드

```bash
git clone <repository_url>
cd parking_project
```

### 2. 가상환경 생성

```bash
python -m venv parking_venv
```

### 3. 가상환경 실행

Windows

```bash
.parking_venv\Scripts\activate
```

Mac/Linux

```bash
source .venv/bin/activate
```

### 4. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 5. .env 설정

```
SERVICE_KEY1= 서울시 공공데이터에서 가져온키
SERVICE_KEY2= 카카오맵 api
SERVICE_KEY3= 카카오리뷰 크롤링

DB_HOST=localhost
DB_PORT=3306
DB_NAME=parking_db
DB_USER=root
DB_PASSWORD=1234
```

### 6. 실행 순서

① 공공데이터 API 수집

↓

② API 전처리

↓

③ MySQL 저장

↓

④ Streamlit 기본 화면

↓

⑤ Selenium 리뷰 크롤링

↓

⑥ 리뷰 전처리

↓

⑦ MySQL 저장 및 JOIN

↓

⑧ Streamlit 통합 조회

---

### 실행

```bash
streamlit run streamlit/app.py
```