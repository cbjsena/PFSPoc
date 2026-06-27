# 테스트 시나리오 ID 명명 규칙 (PFSPoc 적용)

---

## 1. 목적

이 문서는 PFSPoc 프로젝트에 적용할 테스트 시나리오 ID 명명 규칙을 정의한다. 프로젝트의 실제 Django 앱 구조(config/settings.py의 INSTALLED_APPS)를 반영하여 APP 코드와 기본 규칙을 고정한다.

---

## 2. 전체 형식

{APP}_{MENU}_{TYPE}_{NNN}

- APP: Django 앱 식별자 (2~3자)
- MENU: 기능/모듈 식별자 (2~4자)
- TYPE: 테스트 계층 (DIS, SVC, MDL, CMD, API 등)
- NNN: 3자리 일련번호 (각 APP+MENU+TYPE 범위 내에서 순차 부여)

예: IN_PF_DIS_001

---

## 3. 본 프로젝트(APP 코드표)

PFSPoc의 settings.py 기준 INSTALLED_APPS에 맞춰 APP 코드를 아래와 같이 권장한다.

| APP 코드 | Django 앱 폴더 | 설명 |
|---------:|----------------|------|
| IN      | input          | 데이터 입력/시나리오 관리 (UI/CSV 등)
| AP      | api            | API 엔드포인트 (AJAX/REST)
| CM      | common         | 공통 유틸리티/컨텍스트 프로세서/인프라
| SIM     | simulation     | 시뮬레이션 실행 로직(엔진 연동 등)
| RST     | result         | 시뮬레이션/분석 결과 저장·조회

(추가 앱 발생 시 APP 코드 표에 항목을 추가)

---

## 4. MENU(모듈) 예시

MENU 코드는 각 앱 내 주요 화면/기능 단위를 나타낸다. 2~4자 권장.

- IN (input)
  - SCE: Scenario
  - DASH: Dashboard
  - MST: Master 데이터
  - PF: Proforma/스케줄 관련 UI
  - CSV: CSV Import/Export

- AP (api)
  - PF: Proforma 관련 API
  - DST: Distance API
  - VSL: Vessel API

- SIM (simulation)
  - RUN: Simulation Run
  - TSK: Background Task / Worker

- CM (common)
  - AUTH: 인증/권한
  - DOC: DB/테이블 설명/도큐먼트

- RST (result)
  - RPT: 리포트/분석
  - EXP: 결과 Export

(프로젝트 실제 파일/뷰명을 참고하여 MENU 표를 보완)

---

## 5. TYPE 키워드 (권장)

| TYPE | 의미 |
|------|------|
| DIS  | Display / 화면 CRUD 테스트 (목록, 상세, 입력, 삭제) |
| SVC  | Service / 비즈니스 로직 단위 테스트 |
| MDL  | Model / DB 제약·관계·마이그레이션 관련 테스트 |
| CMD  | Management Command (관리 커맨드) |
| API  | API 엔드포인트(비동기, AJAX) |

---

## 6. 일련번호(NNN) 규칙

- 각 조합(APP+MENU+TYPE) 내에서 001부터 순차 부여
- 보수적 충돌 방지: 다른 APP 또는 다른 MENU면 중복 허용
- 대규모 분기 필요 시 접두사에 버전 표기 허용: `IN_PF_DIS_v2_001` (권장하지 않음; 대신 문서화)

---

## 7. 예시 매핑 (현재 프로젝트에 맞춘 예)

| 설명 | ID 예 |
|------|------|
| Scenario 목록 조회 (화면) | IN_SCE_DIS_001 |
| Scenario 생성 서비스 (비즈니스) | IN_SCE_SVC_001 |
| Proforma 목록 API | AP_PF_API_001 |
| Simulation 실행 Command | SIM_RUN_CMD_001 |
| Result 리포트 다운로드 | RST_RPT_DIS_001 |

---

## 8. 운영 및 관리 지침

1. ID 생성자는 PR 템플릿 또는 테스트 시나리오 작성 시 신규 ID를 문서(또는 중앙 시트)에 등록할 것.
2. 기존 ID 변경은 금지(심각한 추적성 문제 발생). 변경이 불가피하면 이전 ID와의 매핑을 문서화할 것.
3. APP 또는 MENU 추가 시 이 문서를 업데이트하여 코드표를 명확히 유지할 것.
4. 자동화 도구(예: 테스트 케이스 관리 시트)가 도입되면 APP+MENU+TYPE 컬럼을 필수로 하여 자동 검증 가능하게 설계.

---

## 9. 요약

형식: `{APP}_{MENU}_{TYPE}_{NNN}` — PFSPoc의 실제 앱(input, api, common, simulation, result)에 맞춘 APP 코드 표를 사용한다. TYPE은 DIS/SVC/MDL/CMD/API를 기본으로 하며, NNN은 각 조합 내에서 3자리 순번으로 관리한다.

문서에 기재된 APP/MENU 표는 프로젝트 실제 코드(views, management commands, API 엔드포인트)를 반영하여 필요 시 갱신한다.
