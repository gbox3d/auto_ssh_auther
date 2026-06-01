# Memo

## 버전 관리

- 버전 형식은 `major.minor.patch`를 사용한다.
- 첫 번째 숫자는 `major`다. 큰 구조 변경이나 호환성에 영향이 있는 변경 때 올린다.
- 두 번째 숫자는 `minor`다. 기능 추가나 의미 있는 개선이 있을 때 올린다.
- 세 번째 숫자는 `patch`다. 버그 수정이나 작은 변경이 있을 때 올린다.
- 시작 버전은 `0.1.0`이다.
- 현재 버전은 `0.3.1`이다.
- 예: `0.1.0 -> 0.2.0` 은 `minor` 증가다.
- 예: `0.2.0 -> 0.2.1` 은 `patch` 증가다.
- 예: `0.2.1 -> 0.3.0` 은 `minor` 증가다.
- 예: `0.3.0 -> 0.3.1` 은 `patch` 증가다.
- 타이틀바 버전은 `app_assets.py`가 설치된 패키지 메타데이터(`importlib.metadata.version`)에서 읽는다. 그래서 버전을 올린 뒤에는 빌드 전에 반드시 `uv sync`로 dist-info를 갱신해야 타이틀과 zip 이름이 일치한다.
- 버전별 변경 사항은 `CHANGELOG.md`와 `_forAI/dev_log.md`에 기록한다.

## 릴리스/태그 규칙

- GitHub Release 태그는 `v` 접두사 + 버전명을 쓴다. 예: `v0.2.1`.
- 과거 `v_0.1.0`은 언더스코어를 포함한 구형 태그이므로, 이후 태그는 언더스코어 없이 `v0.2.1` 형식으로 통일한다.
- 릴리스 제목은 `auto_ssh_auther v0.2.1` 형식을 쓴다.
- 릴리스 asset은 `release/auto_ssh_auther_<os>_<arch>_<version>.zip`을 업로드한다.

## 열린 질문

- `Host` 값을 서버 주소와 동일하게 두는 현재 정책을 유지할지, 별칭 입력 필드를 추가할지? (현재는 별칭 입력 대신 `find_alias_collisions`로 충돌을 감지·경고하는 방식으로 1차 대응함)
- 미등록 호스트를 자동 등록하는 현재 정책을 계속 기본값으로 둘지, 사용자 확인 단계를 더 분리할지?
- 서버 목록 저장 기능을 넣을 경우 민감정보를 어디까지 저장할지? (해결: `history.py`로 host/port/user만 앱 설정폴더 JSON에 저장하고 비밀번호는 절대 저장하지 않는 방식으로 1차 도입함)
- Windows 환경에서 `ssh-keygen`이 없거나 경로가 잡히지 않은 경우를 별도로 안내할지?
- 빌드 결과물 배포 시 운영체제별 서명 또는 추가 패키징 절차가 필요한지?

## 판단 기준

- 비밀번호는 세션 중에만 사용하고 디스크에 남기지 않는다.
- 원격 서버에는 필요한 최소 변경만 한다.
- 로컬 `~/.ssh/config`에는 선택한 공개키와 같은 basename의 비밀키 경로를 `IdentityFile`로 기록한다.
- 사용자가 실패 원인을 빠르게 이해할 수 있도록 오류 메시지는 구체적으로 유지한다.
- UI 로직과 SSH 처리 로직은 최대한 분리해 테스트 가능한 경계를 유지한다.

## 짧은 메모

- 중복 키 판정은 코멘트가 아니라 `키 타입 + base64 데이터` 기준이다.
- `services/register.py`는 미등록 호스트 감지 시 `trust_unknown_host=True`로 1회 재시도한다.
- `remote.py`는 `known_hosts` 파일이 없으면 생성하고, 필요 시 자동 저장한다.
- `ssh/local_config.py`는 기존 Host 블록을 찾아 필요한 항목만 추가/갱신하고, 이미 원하는 값이면 `unchanged`로 둔다.
- 신규 Host 블록은 `Host *`보다 먼저 읽히도록 기존 Host/Match 섹션 앞에 삽입한다.
- `IdentityFile`은 가능하면 `~/.ssh/...` 형태로 기록한다.
- 메인 UI의 원격 작업은 `QThread` 기반 `WorkerThread`로 분리되어 있다.
- 키 등록 검증은 paramiko가 아니라 시스템 `ssh -o BatchMode=yes -o PreferredAuthentications=publickey -i <키>`로 한다. 실제 ssh 동작과 동일하고 암호화된 키도 처리되기 때문이다.
- 검증은 `-i`로 키를 직접 지정해 서버의 authorized_keys 수락 여부(서버 측)를 본다. 별칭 경로(로컬 측) 문제는 `find_alias_collisions`가 별도로 잡는다 — 두 층은 따로 깨질 수 있다.
