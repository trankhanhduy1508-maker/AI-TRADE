import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

function html(body:string,status=200){
  return new Response(`<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI-TRADE MT5 DEMO</title>
<style>
body{font-family:system-ui,sans-serif;max-width:560px;margin:48px auto;padding:0 18px;background:#111;color:#eee}
form{display:grid;gap:14px}input{font:inherit;padding:12px;border-radius:8px;border:1px solid #555;background:#1b1b1b;color:#fff}
button{font:inherit;padding:12px;border:0;border-radius:8px;font-weight:700;cursor:pointer}
small{color:#aaa}.ok{padding:16px;border:1px solid #555;border-radius:10px}
</style></head><body>${body}</body></html>`,{
    status,headers:{"content-type":"text/html; charset=utf-8","cache-control":"no-store"}
  });
}

async function validToken(token:string){
  const rows=await sql`
    select id
    from ai_trade.mt5_demo_onboarding_tokens
    where token_hash=digest(${token},'sha256')
      and used_at is null
      and expires_at>now()
    limit 1
  `;
  return rows[0]?.id?Number(rows[0].id):null;
}

Deno.serve(async(req)=>{
  const url=new URL(req.url);
  if(req.method==="GET"){
    const token=url.searchParams.get("t")??"";
    if(!token||!(await validToken(token))){
      return html("<h2>Liên kết không hợp lệ hoặc đã hết hạn.</h2>",403);
    }
    const esc=token.replaceAll("&","&amp;").replaceAll('"',"&quot;").replaceAll("<","&lt;");
    return html(`
      <h1>Kết nối MT5 DEMO</h1>
      <p>Chỉ dùng <strong>tài khoản DEMO</strong>. Không nhập tài khoản live/funded.</p>
      <form method="post">
        <input type="hidden" name="token" value="${esc}">
        <label>MT5 login<input name="login" inputmode="numeric" required autocomplete="off"></label>
        <label>Trading password<input name="password" type="password" required autocomplete="new-password"></label>
        <label>Server<input name="server" value="MetaQuotes-Demo" required autocomplete="off"></label>
        <button type="submit">Lưu mã hóa</button>
      </form>
      <p><small>Password được mã hóa ngay trong Supabase và không hiển thị lại. Trang này không đặt lệnh.</small></p>
    `);
  }

  if(req.method!=="POST")return html("<h2>Method not allowed</h2>",405);

  const form=await req.formData();
  const token=String(form.get("token")??"");
  const tokenId=await validToken(token);
  if(!tokenId)return html("<h2>Liên kết không hợp lệ hoặc đã hết hạn.</h2>",403);

  const loginText=String(form.get("login")??"").trim();
  const password=String(form.get("password")??"");
  const server=String(form.get("server")??"").trim();

  if(!/^\d{4,20}$/.test(loginText)||!password||password.length>320){
    return html("<h2>Dữ liệu tài khoản không hợp lệ.</h2>",400);
  }

  if(!/demo/i.test(server)){
    return html("<h2>Bị chặn: server phải là DEMO.</h2>",400);
  }

  const login=BigInt(loginText);

  await sql.begin(async tx=>{
    await tx`
      insert into ai_trade.mt5_demo_accounts(
        provider,server,login,password_cipher,server_build,
        account_mode,verified,metadata
      ) values(
        'USER_MT5_DEMO',${server},${login},
        pgp_sym_encrypt(${password},(select key_text from ai_trade.mt5_demo_secret where id=1)),
        null,'DEMO',false,
        '{"source":"ONE_TIME_SECURE_FORM","brokerOrders":false,"liveMoney":false}'::jsonb
      )
      on conflict(login) do update set
        server=excluded.server,
        password_cipher=excluded.password_cipher,
        account_mode='DEMO',
        verified=false,
        metadata=excluded.metadata
    `;
    await tx`
      update ai_trade.mt5_demo_onboarding_tokens
      set used_at=now()
      where id=${tokenId} and used_at is null
    `;
  });

  return html(`
    <div class="ok">
      <h2>Đã lưu MT5 DEMO an toàn</h2>
      <p>Credential đã được mã hóa. Password không được trả về trình duyệt.</p>
      <p>Trạng thái hiện tại: <strong>chờ read-only validation</strong>. Chưa có broker order.</p>
    </div>
  `);
});