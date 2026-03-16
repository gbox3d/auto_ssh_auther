# auto_ssh_auther

로컬 `~/.ssh` 공개키를 원격 서버의 `authorized_keys`에 자동으로 등록해주는 GUI 데스크톱 앱.

## 기능

| 기능 | 설명 |
|------|------|
| 공개키 목록 표시 | `~/.ssh/*.pub` 파일을 자동 탐색, 키 타입·코멘트와 함께 표시 |
| 키 생성 | 다이얼로그에서 이름·타입·코멘트 입력 후 `ssh-keygen`으로 키 쌍 생성 |
| 키 삭제 | 선택한 키의 공개키·비밀키 쌍을 확인 후 삭제 |
| 연결 테스트 | 비밀번호 기반 SSH 접속 테스트, 원격 호스트명 반환 |
| 공개키 등록 | 원격 `authorized_keys`에 선택한 키 추가 (중복 방지) |
| 자동 디렉터리 생성 | 원격 `~/.ssh` 없으면 생성, 권한 `700`/`600` 자동 적용 |
| 호스트 키 검증 | `known_hosts` 기반 검증, 미등록 서버는 경고 후 자동 등록 |
| 비밀번호 미저장 | 서버 정보는 세션 중에만 사용, 디스크 저장 없음 |

## 요구사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv)

## 설치 및 실행

```bash
uv sync
uv run python main.py
```

## 빌드

PyInstaller 기반 빌드 파일은 [`auto_ssh_auther.spec`](/Volumes/data/work/gb_works/auto_ssh_auther/auto_ssh_auther.spec) 와 [`build.py`](/Volumes/data/work/gb_works/auto_ssh_auther/build.py) 로 준비되어 있다.

```bash
uv sync --group build
uv run python build.py
```

- 결과물은 `dist/` 아래에 생성된다.
- 아이콘 파일은 spec에서 자동 포함되므로, `dist`로 별도 복사할 필요가 없다.
- 런타임 창 아이콘과 실행 파일 아이콘 모두 같은 리소스를 사용한다.
- Windows, macOS, Linux에서 같은 spec를 사용할 수 있지만, 실행 파일은 각 운영체제에서 직접 빌드해야 한다.

## 사용 방법

### 공개키 등록
1. 앱 실행 시 `~/.ssh/*.pub` 목록 자동 표시
2. 등록할 공개키 선택
3. 서버 접속 정보(Host, Port, Username, Password) 입력
4. **Test Connection** 으로 접속 확인 (선택사항)
5. 미등록 서버라면 경고 메시지와 함께 호스트 키를 `known_hosts`에 자동 등록
6. **Register Key** 클릭
7. 결과 창에서 `[성공]` / `[안내] 이미 등록됨` / `[실패]` 확인

### 키 생성
1. **Generate Key** 클릭
2. 파일명, 키 타입(ed25519 / rsa / ecdsa), 코멘트 입력
3. 확인 시 `~/.ssh/` 아래에 키 쌍 생성, 목록 자동 갱신

### 키 삭제
1. 목록에서 삭제할 키 선택
2. **Delete Key** 클릭 후 확인
3. 공개키(`.pub`)와 비밀키가 함께 삭제, 목록 자동 갱신

## 프로젝트 구조

```
auto_ssh_auther/
├── auto_ssh_auther.spec   # PyInstaller 빌드 정의
├── auto_ssh_auther/
│   ├── app_assets.py      # 아이콘/리소스 경로 및 앱 아이덴티티
│   ├── keys/
│   │   └── local_keys.py  # ~/.ssh/*.pub 탐색·파싱·생성·삭제
│   ├── services/
│   │   └── register.py    # 키 등록 흐름 제어 (중복 검사 포함)
│   ├── ssh/
│   │   └── remote.py      # paramiko 기반 SSH 접속, 원격 파일 조작
│   └── ui/
│       └── main_window.py # PySide6 GUI (GenerateKeyDialog 포함)
├── build.py               # PyInstaller 빌드 실행 스크립트
main.py                   # 진입점
```

## 의존성

| 패키지 | 용도 |
|--------|------|
| PySide6 | GUI |
| paramiko | SSH 통신 |

## 테스트

```bash
uv run python -m unittest discover -s tests -v
```

## v1 미포함 사항 (향후 검토)
- 서버 목록 저장
- 다중 서버 동시 등록
- SSH 키 기반 관리자 로그인
- 원격 키 제거 기능
