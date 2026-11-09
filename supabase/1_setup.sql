-- 생활 장부 DB 설정 (한 번만 실행)
-- 1) 문서 저장 테이블: 앱의 컬렉션(expenses, fixed, plans …)을 그대로 담음
create table if not exists public.docs (
  owner uuid not null default auth.uid() references auth.users(id) on delete cascade,
  collection text not null,
  id text not null,
  data jsonb not null default '{}'::jsonb,
  version int not null default 1,
  updated_at timestamptz not null default now(),
  primary key (owner, collection, id)
);
create index if not exists docs_owner_col on public.docs(owner, collection);

-- 2) 수정할 때마다 version +1, 수정 시각 갱신
create or replace function public.docs_touch() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' then new.version := old.version + 1; end if;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists docs_touch on public.docs;
create trigger docs_touch before insert or update on public.docs
  for each row execute function public.docs_touch();

-- 3) 보안 규칙: 로그인한 본인 데이터만 읽고 쓰기
alter table public.docs enable row level security;
drop policy if exists "own docs" on public.docs;
create policy "own docs" on public.docs for all to authenticated
  using (owner = auth.uid()) with check (owner = auth.uid());

-- 4) 실시간 동기화(앱 화면 자동 갱신)
do $$ begin
  alter publication supabase_realtime add table public.docs;
exception when duplicate_object then null; end $$;
alter table public.docs replica identity full;

-- 5) 잠금화면 '빠른 기록' 전용 열쇠 (기록 추가만 가능, 읽기 불가)
create table if not exists public.ingest_keys (
  key_hash text primary key,
  owner uuid not null references auth.users(id) on delete cascade
);
alter table public.ingest_keys enable row level security; -- 정책 없음 = 앱/외부에서 접근 불가

create or replace function public.quick_add(
  k text, amount numeric, method text default '인센',
  category text default '기타', memo text default '')
returns text language plpgsql security definer set search_path = public, extensions as $$
declare o uuid; now_kst timestamp := (now() at time zone 'Asia/Seoul'); new_id text;
begin
  select owner into o from public.ingest_keys
   where key_hash = encode(extensions.digest(k, 'sha256'), 'hex');
  if o is null then raise exception 'invalid key'; end if;
  if amount is null or amount <= 0 or amount > 10000000 then raise exception 'bad amount'; end if;
  new_id := 'quick-' || to_char(now_kst, 'YYYYMMDD-HH24MISS') || '-' || amount::bigint;
  insert into public.docs(owner, collection, id, data) values (o, 'expenses', new_id, jsonb_build_object(
    'date', to_char(now_kst, 'YYYY-MM-DD'), 'month', to_char(now_kst, 'YYYY-MM'),
    'time', to_char(now_kst, 'HH24:MI'), 'amount', amount::bigint,
    'method', case when method in ('인센','신한') then method else '인센' end,
    'category', coalesce(nullif(category, ''), '기타'), 'memo', coalesce(memo, ''),
    'plan', '', 'reimb', 0, 'reimbDone', false, 'source', 'quick',
    'createdAt', (extract(epoch from now()) * 1000)::bigint))
  on conflict do nothing;
  return new_id;
end $$;
revoke all on function public.quick_add(text, numeric, text, text, text) from public;
grant execute on function public.quick_add(text, numeric, text, text, text) to anon, authenticated;

-- 6) 열쇠 등록 (본인 계정에 연결)
insert into public.ingest_keys(key_hash, owner)
select '66017a6c3e25b73cf0f59a28132901593aeaf960053226e34a65bac419902724', id
  from auth.users order by created_at limit 1
on conflict (key_hash) do nothing;

select '완료 ✅ 사용자 ' || count(*) || '명, 열쇠 ' || (select count(*) from public.ingest_keys) || '개' as 결과 from auth.users;
