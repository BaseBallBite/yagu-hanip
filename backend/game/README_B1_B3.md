# B1 v2 · B3 v2 데이터 구축

2026 KBO 정규시즌 720경기 데이터 처리 코드입니다.

## 1. B1 v2 — 경기 데이터 정규화 및 보정

경기별 원본 중계 데이터를 정규화하고, 검증된 수동 보정 사항을 반영하여 최종 데이터를 구축합니다.

- 최종 산출물: `B1_corrected_v2.zip`
- 정규화 코드: `b1/normalize_b1.py`
- 최종 패키지 생성: `b1/build_b1_v2_package.py`
- 수동 보정 파일: `b1/b1_manual_corrections_v1.json`
- 선택 규칙: `b1/selection_rules.json`
- 검토 기록: `b1/b1_review_decisions.json`
- 검토 과정: `b1/README_REVIEW.md`

최종 B1 v2는 정규화, 검토, 수동 보정 및 패키지 생성 과정을 거친 결과입니다. 일부 입력 파일과 중간 처리 결과의 이름에 `v1`이 포함되어 있어도 최종 산출물은 B1 corrected v2입니다.

**검증**

```powershell
py -X utf8 -m unittest discover -s backend/game/b1 -p "test_*.py" -v
```

결과: 70개 테스트 통과.

## 2. B3 v2 — 투구 데이터 구축

B1 corrected v2와 팀원의 B2 state v2를 결합하여 투구별 기록, 경기 상태, 좌표 및 궤적 정보를 구축합니다.

- 입력: `B1_corrected_v2.zip`, `b2_state_v2_all.zip`
- 구축 코드: `b3/build_b3_v2.py`
- 최종 산출물: `B3_final_data_v2.zip`
- 검증 보고서: `b3/B3_v2_build_report.json`

**최종 구축 결과**

| 항목 | 결과 |
|---|---:|
| 처리 경기 | 720경기 |
| 투구 관련 기록 | 221,661행 |
| 실제 투구 기록 | 221,530행 |
| B2 상태 연결 | 221,661행 |
| 좌표·궤적 사용 가능으로 분류 | 218,232행 |

B3 v2는 전체 데이터 구축 및 구조·수치 검증을 완료했습니다. 3D 궤적의 실제 물리적 정확성은 별도 검증이 필요합니다.

**실행 형식**

```powershell
py backend/game/b3/build_b3_v2.py --b1 <B1_ZIP_경로> --b2 <B2_ZIP_경로> --out <출력_ZIP_경로> --report <출력_보고서_경로>
```

## 3. 데이터 공유 및 실행 환경

- Python 3.10 이상
- B1·B3 구축 코드의 Python 표준 라이브러리 사용
- 원본 720경기 데이터 및 중간 처리 결과는 GitHub에 포함하지 않음
- 최종 B1·B3 데이터 ZIP은 팀 노션에서 별도로 공유
- B1 재구축에는 원본 데이터, 정규화 중간 결과, 검증된 오버레이 및 설정 파일이 필요함

기존 산출물과 이름이 같은 파일을 다시 만들 때는 덮어쓰지 않도록 새로운 출력 경로를 지정해야 합니다.