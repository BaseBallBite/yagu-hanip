# 이벤트 유형

tools/event_types.txt의 유형 이름 60개에 대한 설명. 2026 정규시즌 720경기 문자중계(B1 정규화, B3)에서 전 행이 하나의 유형으로 분류되는 것을 확인함.

## 원칙

- 한 행은 유형 하나만 가짐. 세부 구분은 이름에 합치지 않고 속성(attr)으로 분리함
- 처음 보는 문구는 유형을 새로 만들기 전에 원문을 남기고 이 문서에 추가함
- 행마다 아웃·득점을 더하지 않음. 유형은 후보 분류이고 상태는 B2 기준임
- 주자 이동은 타석(plate_appearance_id)에 묶어 두고, 같은 원인으로 연속된 주자 행은 한 원인 사건으로 봄. 한 타석 안에서 원인이 다르면 따로 셈

## 타석 결과

| 유형 | 원본 문구 | 속성 |
|---|---|---|
| STRIKEOUT | 삼진 아웃, 쓰리번트 아웃 | 헛스윙/루킹(마지막 투구로 계산), 쓰리번트 |
| DROPPED_THIRD_STRIKE | 스트라이크 낫 아웃, 낫아웃 | 아웃(태그/1루 송구), 출루(폭투·포일·실책·다른주자수비) |
| WALK / INTENTIONAL_WALK / HIT_BY_PITCH | 볼넷 / 자동 고의4구 / 몸에 맞는 볼 | |
| SINGLE | 1루타, 내야안타, 번트안타 | detail: 일반/내야안타/번트안타 |
| DOUBLE / TRIPLE / HOME_RUN | 2루타 / 3루타 / 홈런 | 홈런은 그라운드 여부 |
| GROUNDOUT / FLYOUT / LINEOUT | 땅볼 아웃 / 플라이 아웃 / 라인드라이브 아웃 | FLYOUT은 파울플라이 여부 |
| INFIELD_FLY | 인필드플라이 아웃 | |
| SAC_BUNT / SAC_FLY | 희생번트 / 희생플라이 | 번트는 아웃/출루(실책·야수선택) |
| BUNT_OUT | 희생이 아닌 번트 아웃 | |
| DOUBLE_PLAY / TRIPLE_PLAY | 병살타 / 삼중살 | |
| FIELDERS_CHOICE | 야수선택으로 출루, 땅볼로 출루 | 주자 아웃 동반/주자 실책 동반 |
| ERROR | 실책으로 출루 | detail: 타자출루, 주자진루, 파울플라이포구 |
| BATTED_BALL_HIT_RUNNER | 타구맞음 아웃 | |

## 주자 이동

| 유형 | 원본 문구 |
|---|---|
| ADVANCE / SCORE | N루까지 진루 / 홈인 (타자 결과에 딸린 일반 진루와 득점) |
| FORCE_OUT / TAG_OUT | 포스아웃 / 태그아웃 |
| STOLEN_BASE / CAUGHT_STEALING | 도루로 진루, 이중도루 / 도루실패아웃 |
| DOUBLE_STEAL_ADVANCE | 이중도루 실패시 진루 (아웃 아님) |
| UNCONTESTED_ADVANCE | 무관심도루 |
| PICKOFF | 견제사아웃 |
| WILD_PITCH / PASSED_BALL / BALK | 폭투로, 포일로, 보크로 진루·홈인 |
| ADVANCE_ON_THROW / ADVANCE_ON_PLAY | 주자의 재치로 / 다른주자수비하는 사이 진루 |
| OUT_ON_ADVANCE | 폭투·포일 사이 진루실패아웃 |
| OBSTRUCTION | 주루방해 진루 |

ERROR의 주자진루 속성은 "실책으로 N루까지 진루"(견제 송구 실책 포함)임.

## 교체

PITCHING_CHANGE(투수 교체), PINCH_HITTER(대타), PINCH_RUNNER(대주자), DEFENSIVE_SUB(수비 교체), POSITION_CHANGE(수비위치 변경)

## 상황 메모

| 유형 | 내용 |
|---|---|
| VIDEO_REVIEW | 비디오 판독. 대상(체크스윙, 도루, 태그 등)과 결과(유지/번복) 속성 |
| CHECK_SWING_CALL | 체크스윙 심판 판정 |
| INTERFERENCE | 수비방해, 3피트 수비방해, 코치 접촉. detail로 구분 |
| MOUND_VISIT | 코칭스태프, 포수 마운드 방문 |
| PITCH_CLOCK_VIOLATION | 피치클락 투수위반 볼, 타자위반 스트라이크 |
| EJECTION / WARNING | 퇴장 / 경고 |
| GAME_STOPPAGE / GAME_CALLED | 우천·폭염·정비 등 중단 / 콜드게임 |
| ABS_STATUS | ABS 장애, 심판 자체 판정, 복구 |
| UMPIRE_CHANGE / RULING_NOTE / INTENTIONAL_DROP / ADMIN_NOTE | 심판 교체 / 굴절 등 판정 메모 / 고의낙구 / 판독 불가 안내 |
| PITCHER_STEP_OFF | 투수판 이탈. 데이터에는 두고 해설 대상에서 뺌 (투수판 이탈 경고는 WARNING, 피치클락 장면은 맥락으로 유지) |

## 파생 유형

TAG_UP은 원본 문구가 없음. 플라이 아웃 타석에 주자 진루·득점이 있거나 희생플라이일 때 계산으로 채움.
병살타 문구가 없는데 한 타석에 아웃이 2개 이상인 경우도 DOUBLE_PLAY 계열로 계산함.

## 구조 행

SEPARATOR, GAME_RESULT_NOTICE는 경기 종료 정보와 구분선이라 해설 대상이 아님.

투구, 타자 소개, 이닝 시작은 이벤트 유형이 아니라 행 종류로 구분함. 원본의 모든 행은 이 세 가지 행 종류와 위 유형 중 하나로 설명됨.

| 행 종류 | 내용 |
|---|---|
| 투구 | 결과 코드 B(볼), T(루킹 스트라이크), S(헛스윙), F(파울), H(타격), W(번트파울), V(번트헛스윙). 피치클락 위반(PITCH_CLOCK_VIOLATION)과 파울플라이 포구 실책(ERROR, detail 파울플라이포구)은 투구 행에 같이 있음. 수작업 복원 투구 3건은 추적·구속 없음 |
| 타자 소개 | N번타자 이름 |
| 이닝 시작 | N회초/말 팀 공격 |

## 주의

- 폭투·보크·도루 건수는 주자 행 기준이라 사건 수보다 큼
- B1 handoff 기준으로 모든 행이 can_use_as_verified_fact=false임. 수작업 복원 행과 flagged_source_record는 검증 사실로 쓰지 않음
