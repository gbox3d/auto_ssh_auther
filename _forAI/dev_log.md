# Dev Log

## Entries

- 2026-06-01: 검증/별칭 경고 기능을 담아 버전을 `0.3.0`으로 올리고 커밋·푸시한 뒤 GitHub Release `v0.3.0`을 발행했다.
- 2026-06-01: 키 등록 후 실제 키 로그인 가능 여부를 시스템 `ssh`(BatchMode)로 자동 검증하는 기능을 추가했다(`ssh/verify.py`). 같은 서버를 가리키지만 `IdentityFile`이 없는 Host 별칭을 감지·경고하는 `find_alias_collisions`도 추가했다. 실제 사례(`gb-dgx-01` 별칭에 키 설정이 없어 계속 암호를 묻던 문제)를 진단·수정하면서 나온 기능이다.
- 2026-06-01: 버전을 `0.2.1`로 올리고 `_forAI` 문서 세트를 정리했다. 중복/레거시 계획 문서 `myplan.md`를 `plan.md`로 통합하고 제거했다.
- 2026-06-01: 모든 `_forAI` 문서와 `CHANGELOG.md`의 버전 표기를 `0.2.1`로 통일하고, 태그 규칙을 `v0.2.1`(언더스코어 없음)로 정리했다.
- 2026-06-01: `build.py`로 릴리즈 zip을 생성하고 `main`에 커밋·푸시한 뒤 GitHub Release `v0.2.1`을 발행했다.
- 2026-05-06: 원격 등록 성공/이미 등록됨 이후 로컬 `~/.ssh/config` 자동 반영 기능을 추가하고 버전을 `0.2.0`으로 올렸다.
- 2026-05-06: `ssh/local_config.py`와 `tests/test_local_config.py`를 추가해 Host 추가/갱신/unchanged 동작을 문서화된 테스트로 고정했다.
- 2026-05-06: `README.md`, `CHANGELOG.md`, `_forAI` 문서를 현재 경로 `D:\works\auto_ssh_auther`와 로컬 SSH config 자동 반영 흐름 기준으로 정리했다.
- 2026-03-27: 버전 관리 메모를 `major.minor.patch` 기준으로 정리하고 `_forAI/memo.md`에 예시를 보강했다.
- 2026-03-27: `build.py`를 수정해 릴리즈 zip을 자동 생성하고, 출력 위치를 `release/` 폴더로 분리했다.
- 2026-03-27: `README.md`와 `CHANGELOG.md`에 현재 빌드/릴리즈 절차와 태그 규칙을 반영했다.
- 2026-03-27: `_forAI/readme.md`를 프로젝트 요약과 읽기 가이드가 포함된 한국어 문서로 정리했다.
- 2026-03-27: `inventory.md`, `plan.md`, `memo.md`, `dev_log.md`를 새로 추가하고 현재 코드 구조 기준으로 내용을 채웠다.
- 2026-03-27: 현재 테스트 범위와 기능 리스크를 문서화했다.
