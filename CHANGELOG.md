# Changelog

## Unreleased

### Fixed
- `Verify Key Login` 검증이 접속 호스트와 매칭되는 `~/.ssh/config` 블록의 `IdentityFile`까지 함께 시도해, 서버에 미등록인 키도 성공으로 표시되던 거짓 양성 수정. 검증 ssh 명령에 `-F os.devnull`을 추가해 사용자 config를 무시하고 `-i`로 지정한 키만 격리 검증한다.

## 0.3.1 - 2026-06-01

### Added
- 창 타이틀바에 실제 버전 표시 (예: `Auto SSH Auther v0.3.1`) — dev 실행과 PyInstaller 빌드 양쪽에서 패키지 메타데이터로 해석
- `Verify Key Login` 버튼 추가 — 등록과 별개로 선택한 키로 암호 없이 접속되는지 즉시 검증

### Changed
- `app_assets.py`가 버전을 하드코딩(`v1`) 대신 `importlib.metadata`로 해석
- 프로젝트 버전을 `0.3.1`로 갱신

### Packaging
- `auto_ssh_auther.spec`가 `copy_metadata`로 dist-info를 빌드 결과물에 포함해 빌드 본에서도 버전이 해석되도록 함

### Fixed
- 등록 단위 테스트가 실제 네트워크 접속을 시도하던 문제를 모킹으로 수정

### Verified
- `uv run python -m unittest discover -s tests -v`

## 0.3.0 - 2026-06-01

### Added
- 키 등록 직후 시스템 `ssh`(BatchMode)로 키 전용 로그인이 실제로 되는지 자동 검증하고 결과를 결과창에 표시
- 같은 서버(HostName)를 가리키지만 `IdentityFile`이 없는 다른 Host 별칭을 감지해 경고 (별칭으로 접속 시 키가 아니라 암호를 묻는 문제 예방)
- `src/ssh_auther/ssh/verify.py`와 `tests/test_verify.py` 추가
- `local_config.find_alias_collisions`와 관련 단위 테스트 추가

### Changed
- 프로젝트 버전을 `0.3.0`으로 갱신

### Verified
- `uv run python -m unittest discover -s tests -v`

## 0.2.1 - 2026-06-01

### Changed
- 프로젝트 버전을 `0.2.1`로 갱신
- `_forAI` 문서 세트를 현재 구조 기준으로 정리하고 버전 표기를 `0.2.1`로 통일
- 중복 계획 문서 `_forAI/myplan.md`를 `plan.md` 기준으로 통합하고 제거

### Verified
- `uv run python -m unittest discover -s tests -v`

## 0.2.0 - 2026-05-06

### Added
- 원격 공개키 등록 성공 또는 이미 등록된 키일 때 로컬 `~/.ssh/config`를 자동 추가/갱신
- 로컬 SSH config 반영 대상에 `Host`, `HostName`, `Port`, `User`, `IdentityFile`, `IdentitiesOnly`, `PreferredAuthentications` 적용
- 로컬 SSH config 신규 추가, 기존 Host 갱신, 변경 없음 상태에 대한 단위 테스트 추가
- 원격 등록 성공 메시지에 `로컬 SSH config: added/updated/unchanged` 결과를 함께 표시

### Changed
- 프로젝트 버전을 `0.2.0`으로 갱신
- `pyproject.toml` 설명문을 실제 앱 용도에 맞게 수정
- `README.md`에 현재 빌드/릴리즈 흐름과 GitHub Release 태그 규칙을 반영
- 프로젝트 구조 설명을 `src/ssh_auther` 레이아웃에 맞게 수정

### Packaging
- `build.py`가 PyInstaller 빌드 후 `release/` 아래에 릴리즈용 zip을 생성하도록 변경
- `.gitignore`에 `release/`를 추가해 패키징 산출물을 버전 관리에서 제외
- `pyproject.toml`의 의존성 선언 위치와 build-system 구성을 정리해 `uv` 환경과 빌드가 정상 동작하도록 수정

### Verified
- `uv run python -m unittest discover -s tests -v`

## 0.1.0

### Added
- `PySide6` 기반 GUI 앱 초기 구현
- 로컬 `~/.ssh/*.pub` 공개키 탐색 및 목록 표시
- `ssh-keygen` 기반 키 생성 기능
- 로컬 공개키/비밀키 삭제 기능
- 비밀번호 기반 SSH 연결 테스트 기능
- 원격 `authorized_keys` 공개키 등록 기능
- PyInstaller 기반 빌드 설정
- 앱/창/실행 파일 아이콘 적용
- `unittest` 기반 기본 회귀 테스트

### Changed
- 미등록 호스트는 경고 후 `known_hosts`에 자동 등록하도록 변경
- 중복 키 판별 시 코멘트가 달라도 같은 키로 처리
- `authorized_keys` append 시 마지막 줄 개행이 없어도 파일이 깨지지 않도록 보정
- README와 구현 계획 문서를 현재 상태에 맞게 정리

### Packaging
- `auto_ssh_auther.spec` 추가
- `build.py` 추가
- `pyproject.toml`에 `build` 그룹으로 `pyinstaller`, `pillow` 추가
- 아이콘 리소스가 빌드 결과물에 자동 포함되도록 설정

### Verified
- `python -m unittest discover -s tests -v`
- `python -m compileall auto_ssh_auther main.py tests build.py`
- 오프스크린 GUI 초기화 스모크
- macOS PyInstaller 빌드 성공
