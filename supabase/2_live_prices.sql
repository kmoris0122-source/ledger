-- 생활 장부: 장중 실시간 시세 (앱이 열려 있을 때 1분마다 호출)
-- 네이버 증권 시세를 Supabase 서버가 대신 받아와서 투자 기록의 현재가를 갱신
create extension if not exists http with schema extensions;

create or replace function public.refresh_prices() returns jsonb
language plpgsql security definer set search_path = public, extensions as $$
declare
  me uuid := auth.uid();
  kst timestamp := now() at time zone 'Asia/Seoul';
  last timestamptz; r record; resp extensions.http_response; j jsonb; p bigint; n int := 0;
begin
  if me is null then raise exception 'login required'; end if;
  -- 너무 자주 부르면 30초 안에는 건너뜀
  select updated_at into last from docs where owner = me and collection = 'settings' and id = 'prices';
  if last is not null and now() - last < interval '30 seconds' then
    return jsonb_build_object('skipped', true);
  end if;
  insert into docs(owner, collection, id, data)
    values (me, 'settings', 'prices', jsonb_build_object('at', to_char(kst, 'YYYY-MM-DD HH24:MI')))
    on conflict (owner, collection, id) do update set data = excluded.data;
  perform extensions.http_set_curlopt('CURLOPT_TIMEOUT_MS', '4000');
  for r in select id, data from docs
           where owner = me and collection = 'invest' and coalesce((data->>'qty')::numeric, 0) > 0 and data ? 'code'
  loop
    begin
      resp := extensions.http_get('https://m.stock.naver.com/api/stock/' || (r.data->>'code') || '/basic');
      if resp.status = 200 then
        j := resp.content::jsonb;
        p := replace(j->>'closePrice', ',', '')::bigint;
        if p > 0 then
          update docs set data = data || jsonb_build_object(
              'price', p, 'value', round((data->>'qty')::numeric * p),
              'chg', (j->>'fluctuationsRatio')::numeric,
              'liveAt', to_char(kst, 'YYYY-MM-DD HH24:MI'))
            where owner = me and collection = 'invest' and id = r.id;
          n := n + 1;
        end if;
      end if;
    exception when others then null; -- 한 종목 실패해도 나머지는 계속
    end;
  end loop;
  return jsonb_build_object('updated', n, 'at', to_char(kst, 'HH24:MI'));
end $$;
revoke all on function public.refresh_prices() from public, anon;
grant execute on function public.refresh_prices() to authenticated;

select '완료 ✅ 실시간 시세 함수 준비됨' as 결과;
