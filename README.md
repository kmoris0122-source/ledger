# 생활 장부

지출·예산·일정·투자·할 일을 한 화면에서 보는 개인 가계부 앱이에요.
아이폰·갤럭시 홈 화면에 앱처럼 설치해서 쓰고, 기록은 Supabase(무료 클라우드 DB)에 저장돼요.

- 화면: GitHub Pages (무료 웹 호스팅)
- 저장: Supabase (로그인한 본인 데이터만 읽고 쓰기, 여러 기기 실시간 동기화)
- 시세: 국내 주식·ETF 종목코드를 넣으면 장중 1분마다 현재가 반영

## 똑같이 만들기 (30분, 무료)

준비물: GitHub 계정, Supabase 계정 (둘 다 무료). 코딩은 필요 없어요.

### 1. 코드 복사
1. 이 저장소 오른쪽 위 **Fork**를 눌러 내 계정으로 복사해요.
   (또는 zip을 받아 새 저장소에 파일을 모두 올려도 돼요.)

### 2. Supabase 프로젝트 만들기
1. supabase.com 가입 → **New project** (지역은 Seoul 권장, DB 비밀번호는 아무거나 길게).
2. 왼쪽 **SQL Editor** → **New query**에 `supabase/1_setup.sql` 내용을 붙여 넣고 **Run**.
3. 같은 방법으로 `supabase/2_live_prices.sql`도 실행해요 (주식 실시간 시세용, 안 쓰면 생략 가능).
4. **Authentication → Sign In / Providers**에서 **Allow new users to sign up**을 꺼요. (모르는 사람이 가입하지 못하게)
5. **Authentication → Users → Add user → Create new user**로 내 계정을 만들어요. 이메일·비밀번호 입력, **Auto Confirm User** 체크.
6. **Project Settings → API Keys**에서 두 값을 복사해 둬요.
   - Project URL (예: `https://abcdefgh.supabase.co`)
   - Publishable key (`sb_publishable_...`로 시작) — 공개돼도 되는 키예요. `secret` 키는 절대 넣지 마세요.

### 3. 앱에 내 서버 연결
1. GitHub에서 내 저장소의 `index.html`을 열고 연필(수정) 버튼을 눌러요.
2. `const SUPA_URL=` 과 `const SUPA_KEY=` 두 줄(파일 아래쪽, "따라 만들 때는" 주석 바로 밑)을 6번에서 복사한 값으로 바꾸고 **Commit changes**.

### 4. 웹에 올리기
1. 저장소 **Settings → Pages** → Source: **Deploy from a branch**, Branch: **main / (root)** → Save.
2. 1~2분 뒤 `https://<내 GitHub 아이디>.github.io/<저장소 이름>/` 주소가 생겨요.

### 5. 폰에 설치
- **아이폰**: 사파리로 주소 열기 → 로그인 → 공유 버튼 → **홈 화면에 추가**
- **갤럭시**: 삼성 인터넷 메뉴 → **현재 페이지 추가 → 홈 화면** / 크롬 ⋮ → **앱 설치**
  - 아이콘을 길게 누르면 **지출 기록** 바로가기가 나와요.

### 6. 처음 설정
1. 요약 탭 **변동비 예산 → 예산 정하기**: 한 달 생활비 목표, 결제수단 이름(예: 체크카드).
   회사 인센 카드처럼 매달 충전되는 카드가 있으면 한도를 넣고, 없으면 0 (관련 화면이 숨겨져요).
2. **수입·고정** 탭에 월급과 고정비(월세·통신비·구독)를 넣어요.
3. 필요하면 **투자** 탭에 계좌를 추가해요. 국내 주식·ETF는 6자리 종목코드를 넣으면 시세가 자동 반영돼요.

### 친구도 같이 쓰기
내 Supabase에서 2-5번처럼 친구 계정을 하나 더 만들고 앱 주소를 알려주면 돼요.
데이터는 계정마다 분리돼 앱에서는 서로 안 보여요. 단, 서버 관리자는 관리 화면에서 모든 기록을 볼 수 있으니 친구에게 미리 알려주세요.

## 파일 구성
| 파일 | 역할 |
|---|---|
| `index.html` | 앱 전체 (화면·계산·저장) |
| `manifest.webmanifest`, `icon-*.png`, `sw.js` | 홈 화면 설치·아이콘·빠른 실행 |
| `supabase.min.js` | Supabase 연결 라이브러리 (supabase-js 2.45.4) |
| `supabase/1_setup.sql` | 저장 테이블·보안 규칙·실시간 동기화·빠른 기록 함수 |
| `supabase/2_live_prices.sql` | 네이버 증권 시세를 서버에서 받아오는 함수 |
| `tools/db.py`, `tools/snapshot.py` | 대화형 도우미용 데이터 도구 (앱 사용에는 필요 없음) |

## 무료 한도 (2026년 11월 기준)
Supabase 무료 플랜: DB 500MB, 월 전송량 약 5GB, 일주일 동안 접속이 없으면 일시정지(대시보드에서 다시 켜면 데이터 그대로).
혼자 쓰면 수십 년, 친구 10명 정도까지는 넉넉해요.
