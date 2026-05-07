# _forAI Guide

## 한 줄 요약

`auto_ssh_auther`는 로컬 `~/.ssh` 공개키를 선택해 원격 서버의 `authorized_keys`에 등록하고, 성공 시 로컬 `~/.ssh/config`까지 자동 반영하는 PySide6 기반 GUI 데스크톱 앱이다.

## 문서 읽기 순서

1. `readme.md`
2. `inventory.md`
3. `plan.md`
4. `memo.md`
5. `dev_log.md`

## 각 문서 역할

- `inventory.md`: 현재 저장소 구조, 엔트리포인트, 테스트 범위를 정리
- `plan.md`: 당장 손볼 목표와 중단기 작업 항목을 정리
- `memo.md`: 열린 질문, 설계 판단 기준, 잊기 쉬운 구현 메모를 정리
- `dev_log.md`: `_forAI` 문서 생성 및 갱신 이력을 기록

## 저장소 정보

- 이름: `auto_ssh_auther`
- 경로: `D:\works\auto_ssh_auther`
- 현재 버전: `0.2.0`
- 실행 방식: `uv run python main.py`
- 빌드 방식: `uv sync --group build` 후 `uv run python build.py`

## 참고

- 실제 사용자용 설명은 [README.md](D:/works/auto_ssh_auther/README.md)에 있다.
- `_forAI` 문서는 코드 수정 전에 구조와 의도를 빠르게 파악하기 위한 내부 작업 문서다.
