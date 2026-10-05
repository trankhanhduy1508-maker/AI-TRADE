do $$
declare j bigint;
begin
  select jobid into j
  from cron.job
  where jobname='ai-trade-forward-shadow-daily'
  limit 1;

  if j is not null then
    perform cron.unschedule(j);
  end if;
end $$;

select cron.schedule(
  'ai-trade-forward-shadow-daily',
  '15 3 * * *',
  $cron$
  select net.http_post(
    url := 'https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-forward-shadow',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'x-ai-trade-cron',(select secret from ai_trade.cron_auth where id=1)
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 120000
  ) as request_id;
  $cron$
);
