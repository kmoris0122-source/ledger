# 생활 장부 — 작업 안내

이 저장소는 공개 저장소예요. 금액·계획 같은 개인 정보는 여기에 적지 말고, 장부 데이터(Supabase)나 대화에만 두세요.

## 대화 역할 나누기
- **앱 개선 대화**: 화면·기능·코드 수정, 배포(`git push origin main` → GitHub Pages). 장부 데이터는 테스트 목적 외에는 건드리지 않아요.
- **가계부 대화**: 지출·수입·할 일 기록, 예산·현황 질문, 월 결산. 코드는 수정하지 않아요. 앱 수정이 필요하면 "앱 개선 대화에서 요청해 주세요"라고 안내해요.

## 데이터 읽고 쓰기
`tools/db.py`로만 접근해요 (Supabase REST, 비밀 키는 네트워크 프록시가 `apikey` 헤더에 넣어줌 — 키 값을 찾거나 출력하지 않기).
**이 DB에는 친구 계정 데이터도 있어요.** 사용자는 항상 본인 계정 기준으로 물어봐요. `db.py`는 모든 조회·수정에 본인 owner 조건을 붙이니, curl로 직접 부를 때도 반드시 `owner=eq.<OWNER>`를 넣으세요.

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

## 캡처 사진으로 기록하기 (가계부 대화)
사용자가 카드 앱·문자·영수증 캡처를 올리면:
1. 사진에서 날짜·시간, 사용처, 금액, 결제수단(인센/신한), 승인·취소 여부를 읽어요. 취소 건은 원래 승인 건과 짝지어 빼요.
2. 분류는 위 10개 중에서 사용처를 보고 정하고, 그 날짜에 일정(plans)이 있으면 관련 지출에 연결해요. 밤 9시~새벽 4시 배달앱은 `unplanned` 후보로 표시해요.
3. **쓰기 전에** 같은 날짜·금액의 기존 지출을 조회해 겹치는 건 "이미 있음"으로 빼고, 나머지를 표(날짜·사용처·금액·결제수단·분류)로 보여준 뒤 확인을 받아요. 사용자가 "그대로 넣어"처럼 미리 허락했으면 바로 기록해요.
4. 기록 후 추가 건수와 이번 달 남은 변동비·인센 잔액을 한 줄로 알려줘요. 글씨가 잘려 확실하지 않은 값은 추측하지 말고 물어봐요.

## 대화 옆 요약 페이지
"장부 갱신해줘" → `python3 tools/snapshot.py <폴더>`로 CSV를 만들고, 요약 아티팩트에 바뀐 파일만 새로 올려 데이터셋 `source.url`을 바꾼 뒤 예전 파일은 지워요.
