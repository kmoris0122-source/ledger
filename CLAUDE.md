# 생활 장부 — 작업 안내

이 저장소는 공개 저장소예요. 금액·계획 같은 개인 정보는 여기에 적지 말고, 장부 데이터(Supabase)나 대화에만 두세요.

## 대화 역할 나누기
- **앱 개선 대화**: 화면·기능·코드 수정, 배포(`git push origin main` → GitHub Pages). 장부 데이터는 테스트 목적 외에는 건드리지 않아요.
- **가계부 대화**: 지출·수입·할 일 기록, 예산·현황 질문, 월 결산. 코드는 수정하지 않아요. 앱 수정이 필요하면 "앱 개선 대화에서 요청해 주세요"라고 안내해요.

## 데이터 읽고 쓰기
`tools/db.py`로만 접근해요 (Supabase REST, 비밀 키는 네트워크 프록시가 `apikey` 헤더에 넣어줌 — 키 값을 찾거나 출력하지 않기).

```
python3 tools/db.py list <collection> [YYYY-MM]
python3 tools/db.py get <collection> <id>
python3 tools/db.py create <collection> <id> '<json>'   # 이미 있으면 "exists"
python3 tools/db.py update <collection> <id> '<json>' [version]   # 필드 병합
python3 tools/db.py delete <collection> <id>
```

컬렉션: `expenses`, `income`(월별), `fixed`, `invest`, `debts`, `plans`(월별 일정 예산), `todos`, `dcLog`, `investSnap`, `settings`(`main`: varBudget, incenMonthly, m1Name, m2Name).

## 기록 규칙
- 지출 문서: `{date:"YYYY-MM-DD", month:"YYYY-MM", amount, method:"인센"|"신한", category, memo, plan:"", reimb:0, reimbDone:false, unplanned:false, selfcare:false, createdAt:<ms>}`. id는 짧은 무작위 문자열.
- 분류: 식비, 카페·간식, 교통, 약속·모임, 쇼핑, 생활용품, 의료·건강, 자기계발, 경조사, 기타.
- 정산 받을 돈은 `reimb`에 적고, 받으면 `reimbDone:true`. 예산·분석은 내 몫(amount − reimb), 인센 잔액은 결제 총액 기준.
- 일정 관련 지출은 `plan`에 그 달 plans 문서 id.
- `unplanned`: 계획 없던 충동 소비. `selfcare`: 나를 위한 소비(지난달 아낀 돈에서 씀, 예산 속도에서 제외).
- 신한 결제는 `link:"신한"`인 invest 통장(baseAmount − baseAt 이후 신한 결제)에서 자동 차감돼요. 통장 잔액을 고칠 땐 `baseAmount`와 `baseAt`(현재 ms)을 함께 바꿔요.
- 삭제한 `sms-*` 지출은 `smsSkip/<id>`를 남겨 다시 들어오지 않게 해요.

## 대화 옆 요약 페이지
"장부 갱신해줘" → `python3 tools/snapshot.py <폴더>`로 CSV를 만들고, 요약 아티팩트에 바뀐 파일만 새로 올려 데이터셋 `source.url`을 바꾼 뒤 예전 파일은 지워요.
