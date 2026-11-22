# airflow_data_pipeline

Airflow 2 학습용 저장소이다. Airflow 는 Docker 컨테이너(`apache/airflow:2.10.5-python3.12`)에서만 실행하며,
로컬 Python 환경은 편집기 지원(자동완성, 정적 분석) 용도로만 사용한다.

### 참조
- [BOOK EXAM REPO](https://github.com/K9Ns/data-pipelines-with-apache-airflow)

## 실행

프로젝트 루트가 컨테이너의 `/opt/airflow/dags` 로 마운트되므로 `ch2/`, `ch4/` 등 챕터별 DAG 가 그대로 인식된다.

```bash
./build.sh up         # 컨테이너 기동 (postgres + webserver + scheduler)
./build.sh down       # 컨테이너 중지
./build.sh list-dags  # 등록된 DAG 목록
./build.sh shell      # 컨테이너 셸 접속
```

웹 UI 는 http://localhost:8080 이며, 계정과 비밀번호는 `.env` 에 정의되어 있다(기본값 airflow / airflow).
