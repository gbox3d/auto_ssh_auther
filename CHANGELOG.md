# Changelog

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
