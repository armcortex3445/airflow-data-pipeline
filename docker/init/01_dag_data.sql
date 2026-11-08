-- DAG 가 적재하는 데이터용 스키마/테이블.
-- postgres 컨테이너의 최초 초기화(빈 볼륨) 시점에 /docker-entrypoint-initdb.d 에서 자동 실행된다.
-- 이미 기동 중인 DB 에 적용하려면: docker compose exec -T postgres psql -U airflow -d airflow < docker/init/01_dag_data.sql
CREATE SCHEMA IF NOT EXISTS dag_data;

CREATE TABLE IF NOT EXISTS dag_data.pageview_counts (
    id            INT         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pagename      VARCHAR(50) NOT NULL,
    pageviewcount INT         NOT NULL,
    datetime      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
