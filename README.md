# airflow_data_pipeline

Airflow 2 학습용 저장소이다. Airflow 는 Docker 컨테이너(`apache/airflow:2.10.5-python3.12`)에서만 실행하며,
로컬 Python 환경은 편집기 지원(자동완성, 정적 분석) 용도로만 사용한다.

## 실행

프로젝트 루트가 컨테이너의 `/opt/airflow/dags` 로 마운트되므로 `ch2/`, `ch4/` 등 챕터별 DAG 가 그대로 인식된다.

```bash
./build.sh up         # 컨테이너 기동 (postgres + webserver + scheduler)
./build.sh down       # 컨테이너 중지
./build.sh list-dags  # 등록된 DAG 목록
./build.sh shell      # 컨테이너 셸 접속
```

웹 UI 는 http://localhost:8080 이며, 계정과 비밀번호는 `.env` 에 정의되어 있다(기본값 airflow / airflow).

## 로컬 개발 환경 설정

### 결론

VS Code 에서 `Import "airflow.operators.bash" could not be resolved` 경고가 나타나는 원인은
VS Code 가 사용하는 로컬 Python 인터프리터에 Airflow 가 설치되어 있지 않기 때문이다.
해결 방법은 컨테이너와 같은 Python 3.12 가상환경을 만들어 동일 버전의 Airflow 를 설치하고,
VS Code 인터프리터를 그 가상환경으로 지정하는 것이다. 이 경고는 정적 분석 경고이므로 DAG 실행에는 영향이 없다.

### 원인

- Airflow 는 Docker 이미지 안에만 설치되어 있고, 로컬 Mac 에는 설치되어 있지 않다.
- 프로젝트에 가상환경이 없으므로 VS Code 는 시스템 기본 Python(Homebrew, 3.14)을 인터프리터로 사용한다.
- 해당 인터프리터에 `airflow` 모듈이 없으므로 Pylance 가 import 를 해석하지 못한다.

Airflow 2.10.x 는 Python 3.8 ~ 3.12 만 지원한다. Python 3.13 이상에는 설치되지 않으므로
가상환경은 반드시 컨테이너와 동일한 Python 3.12 로 만들어야 한다.

### 설정 절차

#### 1. Python 3.12 설치

Homebrew 설치를 권장한다. 미리 빌드된 바이너리를 받으므로 컴파일러나 SDK 상태의 영향을 받지 않는다.

```bash
brew install python@3.12
```

pyenv 를 사용하는 경우 `CC` 를 절대 경로로 지정해야 한다.

```bash
CC=/usr/bin/clang pyenv install 3.12
```

`CC` 없이 `pyenv install 3.12` 를 실행하면 `C compiler cannot create executables` 오류로 실패한다.
Command Line Tools 26.6 에 함께 설치된 `MacOSX27.0.sdk` 가 현재 링커와 호환되지 않는 상태에서,
pyenv 빌드 스크립트가 `SDKROOT` 환경변수를 무시한 채(`xcrun --sdk macosx`) 가장 높은 버전인
그 SDK 를 `-isysroot` 로 주입하기 때문이다. `CC` 가 `clang` 이라는 문자열이 아니면 빌드 스크립트가
SDK 주입을 건너뛰므로 정상 SDK(`MacOSX26.5.sdk`)로 빌드된다.

#### 2. 가상환경 생성

프로젝트 루트에서 실행한다. `.venv/` 는 `.gitignore` 에 포함되어 있다.

Homebrew 로 설치한 경우:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv
```

pyenv 로 설치한 경우:

```bash
"$(pyenv root)/versions/$(pyenv latest 3.12)/bin/python" -m venv .venv
```

#### 3. Airflow 설치

Airflow 는 반드시 공식 constraints 파일과 함께 설치한다. 의존성이 많아서 constraints 없이 설치하면 버전 충돌이 발생한다.
버전은 `.env` 의 `AIRFLOW_VERSION` / `PYTHON_VERSION` 과 맞춘다(기본값 2.10.5 / 3.12).

```bash
.venv/bin/pip install --upgrade pip
```

```bash
.venv/bin/pip install "apache-airflow==2.10.5" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
```

실습 챕터용 추가 패키지는 `docker/requirements.txt` 와 동일하게 설치한다.

```bash
.venv/bin/pip install -r docker/requirements.txt \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"
```

다음 명령으로 `2.10.5` 가 출력되면 설치가 완료된 것이다.

```bash
.venv/bin/python -c "import airflow; print(airflow.__version__)"
```

#### 4. VS Code 인터프리터 지정

`.vscode/settings.json` 을 다음 내용으로 생성한다.

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic"
}
```

명령 팔레트(Cmd+Shift+P)에서 **Python: Select Interpreter** 를 실행해 `.venv` 를 선택하면 경고가 사라진다.
경고가 남아 있으면 **Developer: Reload Window** 로 창을 다시 불러온다.

### 참고

- 로컬 가상환경은 편집기 지원용이다. DAG 실행과 테스트는 Docker 컨테이너에서 수행한다.
- `.env` 나 `docker/requirements.txt` 의 버전을 변경하면 로컬 가상환경도 같은 버전으로 다시 설치해야 한다.
- `python.analysis.extraPaths` 로 경로를 추가하는 방법은 효과가 없다. Airflow 가 로컬에 설치되어 있지 않기 때문이다.
