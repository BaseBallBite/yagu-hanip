# 사전 빌드

루트 cards/ 의 카드 yaml(규칙 51, 용어 147)을 합쳐서 data/dict 에 dict.json, dict.csv 를 만듦.

## 쓰는 법
```
python3 data/dict/build_dict.py cards data/dict
```
- 필요한 것: python3, pyyaml
- 저장소 루트에서 실행함. 첫 번째 인자는 카드 폴더, 두 번째 인자는 결과물을 둘 폴더임
- cards/rule/ 에 규칙 카드, cards/term/ 에 용어 카드를 둠. 폴더와 카드의 kind 가 다르면 오류로 알려 줌
- _template.yaml 처럼 밑줄로 시작하는 파일은 건너뜀

## 규칙
- 카드는 cards/ 의 yaml 에서만 고침(새 카드는 kind 에 맞는 rule/ 또는 term/ 폴더에 둠)
- dict.json, dict.csv 는 결과물이라 직접 고치지 않음. 직접 고치면 다음 빌드 때 사라짐
- 카드를 고친 뒤에는 빌드를 다시 돌리고, yaml 과 결과물을 같이 커밋함

## 검사
빌드할 때 아래를 확인하고 문제가 있으면 출력함
- 필수 칸(id, kind, title, category, one_liner, easy, review_status)이 비었는지
- id 가 파일 이름과 같은지
- one_liner 가 60자를 넘는지
- source 가 없는지
- related 에 없는 카드가 있는지

## 결과물
- dict.json: cards(카드 전체), alias_index(밑줄용 별칭, 긴 것부터), event_index(경기 이벤트별 카드)
- dict.csv: 카드 내용을 열로 푼 것. UTF-8 BOM 이라 엑셀에서 바로 열림. 검수 상태 열은 없고 dict.json 에만 있음

## 데이터 설명
카드 하나가 한 개념(용어 또는 규칙)이고, 사전 화면, 용어 밑줄, AI 해설 근거가 같은 카드를 씀. 카드 id 가 모든 곳의 연결 키임.

현재 198장
- 구분: 규칙 51, 용어 147
- 규칙 카테고리: 특수 상황 16, 주루 규칙 10, 기본 규칙 9, 수비 규칙 9, 타격 규칙 7
- 용어 카테고리: 기록·통계 55, 투구·구종 26, 경기 운영 21, 타격 20, 수비 15, 주루 10
- 검수 상태: 198장 모두 draft(규칙집 대조 전 또는 사람 검수 전)

카드 칸
- id: rule.영어이름 또는 term.영어이름. 파일 이름과 같음
- kind, title, category: 구분, 화면에 보이는 이름, 분류
- one_liner: 60자 이내 한 줄 설명. 용어 팝업에 그대로 뜸
- easy: 2~4문장 쉬운 설명. 사전 상세 페이지와 AI 해설의 근거
- example: 가상 예시 1개. 실제 선수 이름은 안 씀
- when: 규칙이 적용되는 조건(39장에만 있음)
- source: 출처. 규칙 카드는 규칙 번호가 들어감
- quote: 규칙집 원문 인용, 40자 이내(6장에만 있음)
- related: 관련 카드 id
- event_types: 이 카드가 설명하는 경기 이벤트(48장에 있음)
- image, image_static: 그림 파일 경로(data/dict 기준 상대 경로). 구종 카드와 체크스윙, 스트라이크 존에만 있음(16장)
- aliases: 해설 문장에서 밑줄을 칠 단어들(193장에 있음)
- review_status, reviewer: 검수 상태와 검수자

dict.json 구성
- cards: id 를 키로 한 카드 전체
- alias_index: 공백 뺀 표기에서 카드 id 로 가는 표. 밑줄 칠 때 긴 표기부터 맞추도록 길이순으로 정렬됨(630개)
- event_index: 경기 이벤트에서 카드 id 목록으로 가는 표(30종)

출처 분포(출처 항목 수 기준)
- 공식야구규칙 2026 159, KBO 리그 규정 2026 35, 2026 KBO 연감 가이드북 4, KBO 홈페이지 3, MLB.com 용어집 14
- 팀 작성 67(일반 야구 용어 40, KBO 기록실 항목 23, 세이버메트릭스 일반 정의 2, 중계 관용 표현 2). 팀이 직접 쓴 카드라 사람 검수가 필요함

주의
- event_types 이름은 초안이라 백엔드에서 확정하는 값과 맞춰야 event_index 가 동작함
- 카드 검사: python3 tools/validate_cards.py cards --strict
- 그림은 tools/diagrams/ 의 스크립트로 만듦
- 카드 설명은 쉬운 말투(~예요)로 쓰여 있음
