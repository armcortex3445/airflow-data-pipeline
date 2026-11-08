# Airflow 2 학습용 커스텀 이미지
# 빌드:  ./build.sh build   (또는 docker compose build)
ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.12
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# 시스템 패키지 설치는 root 권한 필요
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        wget \
        unzip \
        vim-tiny \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip 설치는 반드시 airflow 유저로 (공식 이미지 권장 사항)
USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /opt/airflow
