Deno.serve(()=>new Response(
  '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font-family:system-ui;max-width:620px;margin:48px auto;padding:0 18px"><h1>MT5 DEMO đã kết nối</h1><p>Luồng nhập credential thủ công đã bị vô hiệu hóa vì AI-TRADE đã có account MetaQuotes-Demo canonical trong Supabase Vault.</p><p>Trang này không nhận login/password và không đặt lệnh.</p></body></html>',
  {status:410,headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store'}}
));