#!/usr/bin/env bash
# Airflow 2 학습 환경 빌드/실행 스크립트
#
#   ./build.sh build        이미지 빌드 (기본)
#   ./build.sh up           빌드 + DB 초기화 + webserver/scheduler 기동
#   ./build.sh down         컨테이너 중지
#   ./build.sh clean        컨테이너 + 볼륨(DB) + 이미지 삭제
#   ./build.sh logs [svc]   로그 보기
#   ./build.sh shell        airflow CLI 가 있는 컨테이너 셸 진입
#   ./build.sh list-dags    DAG 목록 출력 (파싱 오류 확인용)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

AIRFLOW_VERSION="${AIRFLOW_VERSION:-2.10.5}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"
IMAGE_NAME="${AIRFLOW_IMAGE_NAME:-airflow-study:${AIRFLOW_VERSION}}"

log()  { printf '\033[1;34m[build]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

check_docker() {
  command -v docker >/dev/null 2>&1 || die "docker 가 설치되어 있지 않습니다."
  docker info >/dev/null 2>&1      || die "docker 데몬이 실행 중이 아닙니다. Docker Desktop 을 켜 주세요."
  docker compose version >/dev/null 2>&1 || die "docker compose v2 가 필요합니다."
}

# 컨테이너 안에서 airflow 가 실행될 UID
#  - Linux : 호스트 UID 를 써야 bind mount(logs/, dags/) 권한이 맞음
#  - macOS : Docker Desktop 이 마운트 권한을 처리하므로 이미지 기본 사용자(50000) 사용
resolve_uid() {
  if [[ "$(uname -s)" == "Linux" ]]; then id -u; else echo 50000; fi
}

prepare_env() {
  mkdir -p logs plugins
  if [[ ! -f .env ]]; then
    log ".env 생성"
    cat > .env <<ENV
AIRFLOW_UID=$(resolve_uid)
AIRFLOW_VERSION=${AIRFLOW_VERSION}
PYTHON_VERSION=${PYTHON_VERSION}
AIRFLOW_IMAGE_NAME=${IMAGE_NAME}
AIRFLOW_WEB_PORT=8080
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
ENV
  fi
}

cmd_build() {
  log "이미지 빌드: ${IMAGE_NAME} (airflow ${AIRFLOW_VERSION}, python ${PYTHON_VERSION})"
  docker compose build "$@"
  log "빌드 완료"
  docker image ls "${IMAGE_NAME%%:*}"
}

cmd_up() {
  cmd_build
  log "DB 초기화 및 서비스 기동"
  docker compose up -d
  log "기동 완료 → http://localhost:${AIRFLOW_WEB_PORT:-8080}  (id/pw: airflow / airflow)"
  docker compose ps
}

cmd_down()  { docker compose down; }
cmd_clean() {
  docker compose down -v --rmi local --remove-orphans
  log "logs/ 디렉터리는 남겨 두었습니다. 필요하면 직접 삭제하세요."
}
cmd_logs()  { docker compose logs -f "$@"; }
cmd_shell() { docker compose run --rm --no-deps -it airflow-webserver bash; }
cmd_list_dags() {
  docker compose run --rm airflow-webserver airflow dags list
}

main() {
  local cmd="${1:-build}"; shift || true
  check_docker
  prepare_env
  set -a; source .env; set +a
  case "$cmd" in
    build)     cmd_build "$@" ;;
    up)        cmd_up ;;
    down)      cmd_down ;;
    clean)     cmd_clean ;;
    logs)      cmd_logs "$@" ;;
    shell)     cmd_shell ;;
    list-dags) cmd_list_dags ;;
    -h|--help|help) sed -n '2,11p' "$0" ;;
    *) die "알 수 없는 명령: $cmd (help 참고)" ;;
  esac
}
main "$@"
