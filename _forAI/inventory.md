# Inventory

## 저장소 정보

- 이름: `auto_ssh_auther`
- 경로: `D:\works\auto_ssh_auther`
- 패키지 이름: `auto-ssh-auther`
- 현재 버전: `0.2.0`
- Python 요구사항: `>=3.11`

## 최상위 구조

- `_forAI/`: AI 작업용 내부 문서
- `src/ssh_auther/`: 실제 애플리케이션 코드
- `tests/`: 단위 테스트
- `main.py`: GUI 실행 진입점
- `build.py`: PyInstaller 빌드 실행 스크립트
- `auto_ssh_auther.spec`: PyInstaller 설정
- `pyproject.toml`: 프로젝트 메타데이터와 의존성 정의
- `README.md`: 사용자용 설명서
- `CHANGELOG.md`: 변경 이력
- `icon_ssh_auther.ico`, `icon_ssh_auther.png`: 앱 아이콘 자산

## 소스 구조

- `src/ssh_auther/app_assets.py`: 앱 이름, 윈도우 제목, 아이콘 로딩, Windows App ID 설정
- `src/ssh_auther/ui/main_window.py`: 메인 윈도우, 키 생성 다이얼로그, 백그라운드 작업 스레드
- `src/ssh_auther/keys/local_keys.py`: 로컬 공개키 탐색, 파싱, 생성, 삭제
- `src/ssh_auther/services/register.py`: 접속 테스트, 중복 검사, 사용자 메시지 변환, 등록 흐름 제어
- `src/ssh_auther/ssh/remote.py`: Paramiko 기반 SSH 연결, `authorized_keys` 읽기/추가, `known_hosts` 처리
- `src/ssh_auther/ssh/local_config.py`: 로컬 `~/.ssh/config` Host 블록 추가/갱신

## 실행 및 빌드 엔트리포인트

- 개발 실행: `uv sync`
- 앱 실행: `uv run python main.py`
- 테스트 실행: `uv run python -m unittest discover -s tests -v`
- 빌드 준비: `uv sync --group build`
- 빌드 실행: `uv run python build.py`

## 의존성

- `PySide6`: GUI
- `paramiko`: SSH 통신 및 호스트 키 처리
- `pyinstaller`: 배포 빌드
- `pillow`: 빌드 그룹 의존성

## 테스트 범위

- `tests/test_remote.py`
  - `authorized_keys` append payload 줄바꿈 처리
  - 빈 키 문자열 거부
- `tests/test_register.py`
  - 중복 키 판정 시 코멘트 무시
  - 주요 네트워크/SSH 오류 메시지 변환
  - 원격 등록 성공 메시지에 로컬 SSH config 반영 결과 포함 확인
- `tests/test_local_config.py`
  - 신규 Host 블록 추가
  - 기존 Host 블록 갱신
  - 변경 없음 상태 유지

## 현재 파악된 공백

- GUI 동작 자체에 대한 자동화 테스트는 없다.
- 실제 SSH 서버를 대상으로 한 통합 테스트는 없다.
- 키 생성/삭제 함수에 대한 직접 테스트는 아직 없다.
- 복잡한 사용자 `~/.ssh/config` 사례는 더 많은 fixture로 보강할 수 있다.
