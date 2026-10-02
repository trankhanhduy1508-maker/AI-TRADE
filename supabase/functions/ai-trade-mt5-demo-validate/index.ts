import postgres from "npm:postgres@3.4.9";
import WebSocket from "npm:ws@8.18.3";
import { verifiedDemoSnapshot } from "./readback.mjs";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const WS_URI="wss://web.metatrader.app/terminal";
const INITIAL_KEY_HEX="02de02a1a65cc794684fcbea1ecb0fd74ae657e43662c11eee885d2fd64f4964";

const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json","cache-control":"no-store","x-content-type-options":"nosniff"}});
async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
function concat(...parts:Uint8Array[]){
  const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let o=0;
  for(const p of parts){out.set(p,o);o+=p.length;}return out;
}
function u16le(v:number){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,v,true);return b;}
function u32le(v:number){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,v>>>0,true);return b;}
function u64le(v:number|bigint){const b=new Uint8Array(8);new DataView(b.buffer).setBigUint64(0,BigInt(v),true);return b;}
function fixedUtf16(value:string,size:number){const out=new Uint8Array(size);for(let i=0;i<Math.min(value.length,size/2);i++){const c=value.charCodeAt(i);out[i*2]=c&255;out[i*2+1]=(c>>>8)&255;}return out;}
function readUtf16(data:Uint8Array){let s="";for(let i=0;i+1<data.length;i+=2){const c=data[i]|(data[i+1]<<8);if(c===0)break;s+=String.fromCharCode(c);}return s;}
function hexToBytes(hex:string){const out=new Uint8Array(hex.length/2);for(let i=0;i<out.length;i++)out[i]=parseInt(hex.slice(i*2,i*2+2),16);return out;}
function randomBytes(n:number){const b=new Uint8Array(n);crypto.getRandomValues(b);return b;}
async function crypt(key:Uint8Array,data:Uint8Array,mode:"encrypt"|"decrypt"){
  const k=await crypto.subtle.importKey("raw",key,{name:"AES-CBC"},false,[mode]);
  const iv=new Uint8Array(16);
  const out=mode==="encrypt"
    ? await crypto.subtle.encrypt({name:"AES-CBC",iv},k,data)
    : await crypto.subtle.decrypt({name:"AES-CBC",iv},k,data);
  return new Uint8Array(out);
}
function inner(cmd:number,payload:Uint8Array){return concat(randomBytes(2),u16le(cmd),payload);}
function outer(body:Uint8Array){return concat(u32le(body.length),u32le(1),body);}
function initPayload(cid:Uint8Array){
  return concat(
    u32le(0),fixedUtf16("",64),fixedUtf16("",128),cid,
    fixedUtf16("",64),fixedUtf16("",64),u64le(0),
    fixedUtf16("",128),u32le(0),fixedUtf16("",256),u64le(0)
  );
}
async function buildClientId(){
  const uniq=new Uint8Array(3);
  crypto.getRandomValues(uniq);
  const uniqText=String((uniq[0]<<16)|(uniq[1]<<8)|uniq[2]);
  const source=new TextEncoder().encode(
    ["deno","1","en-US","0x0",uniqText].join(";")
  );
  const digest=new Uint8Array(await crypto.subtle.digest("SHA-1",source));
  return digest.slice(0,16);
}
function loginPayload(login:bigint,password:string,cid:Uint8Array){
  const webUrl="web.metatrader.app";
  return concat(
    u32le(0),
    fixedUtf16(password.slice(0,32),64),
    fixedUtf16("",128),
    cid,
    fixedUtf16("",64),
    fixedUtf16("",64),
    u64le(0),
    fixedUtf16("",128),
    u32le(webUrl.length),
    fixedUtf16(webUrl,256),
    u64le(login),
    new Uint8Array(160),
    u64le(0)
  );
}

async function renderPymt5Fallback(login:bigint,password:string){
  const secrets=await sql`
    select decrypted_secret as secret
    from vault.decrypted_secrets
    where name='cws_mt5_render_verify_token'
    limit 1
  `;
  const token=String(secrets[0]?.secret??"");
  if(!token)return null;
  try{
    const response=await fetch("https://cws-mt5-verify-free.onrender.com/mt5-verify",{
      method:"POST",
      headers:{
        "content-type":"application/json",
        "authorization":"Bearer "+token
      },
      body:JSON.stringify({
        server:"MetaQuotes-Demo",
        login:Number(login),
        password
      }),
      cache:"no-store",
      signal:AbortSignal.timeout(120000)
    });
    const data=await response.json().catch(()=>null);
    if(!response.ok||!data||data.verified!==true
        ||data.status!=="DEMO_VERIFIED"
        ||data.server!=="MetaQuotes-Demo"
        ||String(data.login)!==String(login)
        ||data.brokerOrders!==false
        ||data.liveMoneyLocked!==true
        ||typeof data.balance!=="number"
        ||!Number.isFinite(data.balance)
        ||typeof data.currency!=="string"){
      return null;
    }
    return data;
  }catch{
    return null;
  }
}
class Client{
  ws:WebSocket;
  key=hexToBytes(INITIAL_KEY_HEX);
  constructor(){this.ws=new WebSocket(WS_URI,{headers:{Origin:"https://web.metatrader.app"}});}
  async open(){await new Promise<void>((resolve,reject)=>{const t=setTimeout(()=>reject(new Error("WS_OPEN_TIMEOUT")),15000);this.ws.once("open",()=>{clearTimeout(t);resolve();});this.ws.once("error",(e)=>{clearTimeout(t);reject(e);});});}
  async command(cmd:number,payload=new Uint8Array()){
    const encrypted=await crypt(this.key,inner(cmd,payload),"encrypt");
    const response=new Promise<{code:number;body:Uint8Array}>((resolve,reject)=>{
      const t=setTimeout(()=>{cleanup();reject(new Error("CMD_"+cmd+"_TIMEOUT"));},30000);
      const onErr=(e:unknown)=>{cleanup();reject(e);};
      const onMsg=async(data:WebSocket.RawData)=>{
        try{
          const raw=new Uint8Array(data as any);if(raw.length<8)return;
          const dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);
          if(dv.getUint32(0,true)!==raw.length-8)return;
          const dec=await crypt(this.key,raw.slice(8),"decrypt");if(dec.length<5)return;
          const id=new DataView(dec.buffer,dec.byteOffset,dec.byteLength).getUint16(2,true);
          if(id!==cmd)return;cleanup();resolve({code:dec[4],body:dec.slice(5)});
        }catch(e){cleanup();reject(e);}
      };
      const cleanup=()=>{clearTimeout(t);this.ws.off("message",onMsg);this.ws.off("error",onErr);};
      this.ws.on("message",onMsg);this.ws.on("error",onErr);
    });
    this.ws.send(outer(encrypted));return response;
  }
  close(){try{this.ws.close();}catch{}}
}
function parseAccount(body:Uint8Array){
  if(body.length<739)throw new Error("ACCOUNT_BODY_TOO_SHORT");
  const dv=new DataView(body.buffer,body.byteOffset,body.byteLength);
  let o=0;
  const accountType=dv.getUint8(o);o+=1;
  const rights=dv.getInt32(o,true);o+=4;
  const permissionsFlags=dv.getInt32(o,true);o+=4;
  const balance=dv.getFloat64(o,true);o+=8;
  const credit=dv.getFloat64(o,true);o+=8;
  const currency=readUtf16(body.slice(o,o+64));o+=64;
  const currencyDigits=dv.getUint32(o,true);o+=4;
  const leverage=dv.getUint32(o,true);o+=4;
  const accountName=readUtf16(body.slice(o,o+256));o+=256;
  const serverBuild=dv.getUint16(o,true);o+=2;
  const serverName=readUtf16(body.slice(o,o+128));o+=128;
  const company=readUtf16(body.slice(o,o+256));o+=256;
  return {
    accountType,rights,permissionsFlags,balance,credit,currency,currencyDigits,
    leverage,accountName,serverBuild,serverName,company,
    isDemo:accountType===1,
    tradeAllowed:(rights&4)===0,
    readOnly:(rights&512)!==0
  };
}

Deno.serve(async(req)=>{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const size=Number(req.headers.get("content-length")??0);
  if(!Number.isFinite(size)||size>1024)return json({ok:false,
    status:"INVALID_DEMO_REQUEST",verified:false},413);
  const raw=await req.text();
  if(raw.length>1024)return json({ok:false,
    status:"INVALID_DEMO_REQUEST",verified:false},413);
  let body:{login?:unknown;readback?:unknown;verifyPassword?:unknown};
  try{body=JSON.parse(raw)}catch{return json({ok:false,
    status:"INVALID_DEMO_REQUEST",verified:false},400);}
  if(!body||typeof body!=="object"||Array.isArray(body))
    return json({ok:false,status:"INVALID_DEMO_REQUEST",verified:false},400);
  const requested=typeof body.login==="string"?body.login.trim():"";
  const fullReadback=body.readback==="investor_snapshot";
  const direct=body.readback==="founder_verify";
  const fallbackSelftest=body.readback==="render_fallback_selftest";
  if((body.readback!==undefined&&!fullReadback&&!direct&&!fallbackSelftest)
      ||(direct&&(!requested||typeof body.verifyPassword!=="string"
        ||body.verifyPassword.length<4||body.verifyPassword.length>32
        ||/[\u0000-\u001F\u007F]/.test(body.verifyPassword)))
      ||(!direct&&body.verifyPassword!==undefined)){
    return json({ok:false,status:"INVALID_DEMO_REQUEST",verified:false,
      brokerOrders:false,liveMoneyLocked:true},400);
  }
  if(requested&&!/^[1-9][0-9]{4,14}$/.test(requested)){
    return json({ok:false,status:"INVALID_DEMO_LOGIN",verified:false,
      brokerOrders:false,liveMoneyLocked:true},400);
  }

  const rows=direct
    ? await sql`
      select a.account_login as login,a.server
      from ai_trade.mt5_demo_accounts a
      where a.account_login=${BigInt(requested)}
        and a.account_type='DEMO' and a.server='MetaQuotes-Demo'
        and a.is_active=true
      limit 1
    `
    : requested
    ? await sql`
      select a.account_login as login,a.server,
             v.decrypted_secret as password,
             vi.decrypted_secret as investor_password
      from ai_trade.mt5_demo_accounts a
      join vault.decrypted_secrets v on v.id=a.password_secret_id
      left join vault.decrypted_secrets vi on vi.id=a.investor_password_secret_id
      where a.account_login=${BigInt(requested)}
        and a.account_type='DEMO'
        and a.server='MetaQuotes-Demo'
        and a.is_active=true
      limit 1
    `
    : await sql`
      select a.account_login as login,a.server,
             v.decrypted_secret as password,
             vi.decrypted_secret as investor_password
      from ai_trade.mt5_demo_accounts a
      join vault.decrypted_secrets v on v.id=a.password_secret_id
      left join vault.decrypted_secrets vi on vi.id=a.investor_password_secret_id
      where a.account_type='DEMO'
        and a.server='MetaQuotes-Demo'
        and a.is_active=true
      order by a.last_verified_at desc nulls last,a.created_at desc
      limit 1
    `;

  if(!rows[0])return json({ok:true,status:"NO_METAQUOTES_DEMO_CREDENTIAL",verified:false,brokerOrders:false,liveMoneyLocked:true});

  const row=rows[0];
  const login=BigInt(row.login);
  const password=String((direct
    ? body.verifyPassword
    : fullReadback
    ? row.investor_password
    : row.password)??"");
  if(!password)return json({ok:false,status:fullReadback
    ?"MISSING_INVESTOR_ONLY_CREDENTIAL":direct
    ?"INVALID_DEMO_REQUEST":"MISSING_DECRYPTED_PASSWORD",
    verified:false,brokerOrders:false,liveMoneyLocked:true},503);

  if(fallbackSelftest){
    const fallback=await renderPymt5Fallback(login,password);
    if(!fallback){
      return json({
        ok:false,status:"RENDER_FALLBACK_E2E_FAIL",verified:false,
        brokerOrders:false,liveMoneyLocked:true
      },503);
    }
    return json({
      ok:true,status:"RENDER_FALLBACK_E2E_PASS",verified:true,
      server:"MetaQuotes-Demo",mode:"DEMO",
      source:"RENDER_PYMT5_FALLBACK",
      brokerOrders:false,liveMoneyLocked:true
    });
  }

  const c=new Client();
  try{
    await c.open();
    const boot=await c.command(0,new Uint8Array(64));
    if(boot.code!==0||boot.body.length<82)return json({ok:false,status:"BOOTSTRAP_FAILED",code:boot.code,verified:false});
    const bdv=new DataView(boot.body.buffer,boot.body.byteOffset,boot.body.byteLength);
    const bootstrapBuild=bdv.getUint16(0,true);
    const sessionKey=boot.body.slice(66);
    if(![16,24,32].includes(sessionKey.length))return json({ok:false,status:"BAD_SESSION_KEY",verified:false,keyLength:sessionKey.length});
    c.key=sessionKey;

    const cid=await buildClientId();
    // Pinned pymt5 live evidence uses bootstrap -> login directly.
    // cmd=29 is not part of the successful MetaQuotes-Demo login path.
    const loginResult=await c.command(28,loginPayload(login,password,cid));
    if(loginResult.code!==0){
      if(direct){
        const fallback=await renderPymt5Fallback(login,password);
        if(fallback){
          await sql`
            update ai_trade.mt5_demo_accounts
            set last_verified_at=now(),is_active=true
            where account_login=${login}
          `;
          return json({
            ok:true,
            status:"DEMO_VERIFIED",
            verified:true,
            login:login.toString(),
            accountType:Number(fallback.accountType??1),
            server:"MetaQuotes-Demo",
            mode:"DEMO",
            readbackSource:"RENDER_PYMT5_FALLBACK",
            balance:Number(fallback.balance),
            equity:Number(fallback.equity??fallback.balance),
            currency:String(fallback.currency??"USD"),
            tradeAllowed:fallback.tradeAllowed===true,
            readOnly:fallback.readOnly===true,
            passwordExposed:false,
            brokerOrders:false,
            liveMoneyLocked:true,
            supabaseLoginCode:loginResult.code
          });
        }
      }
      return json({ok:true,status:"LOGIN_REJECTED",login:login.toString(),
        loginCode:loginResult.code,verified:false,brokerOrders:false,liveMoneyLocked:true});
    }

    const acctResult=await c.command(3,new Uint8Array());
    if(acctResult.code!==0)return json({ok:false,status:"ACCOUNT_READ_FAILED",code:acctResult.code,verified:false});

    const account=parseAccount(acctResult.body);
    const verified=account.isDemo&&account.serverName==="MetaQuotes-Demo";
    if(fullReadback){
      // Investor-only: fresh cmd=3 -> cmd=4 -> cmd=3, same broker session.
      // An empty position list is valid only if the broker returned count=0.
      if(!verified) return json({ok:false,status:"BROKER_NOT_DEMO",
        verified:false,brokerOrders:false,liveMoneyLocked:true},403);
      const positionsResult=await c.command(4,new Uint8Array());
      if(positionsResult.code!==0)throw new Error("BROKER_POSITIONS_FAILED");
      const secondResult=await c.command(3,new Uint8Array());
      if(secondResult.code!==0)throw new Error("BROKER_ACCOUNT_RECHECK_FAILED");
      const fresh=verifiedDemoSnapshot(
        acctResult.body,positionsResult.body,secondResult.body);
      if(fresh.server!==row.server)throw new Error("BROKER_SERVER_CHANGED");
      await sql`
        update ai_trade.mt5_demo_accounts
        set last_verified_at=now()
        where account_login=${login}
          and account_type='DEMO' and server='MetaQuotes-Demo' and is_active=true
      `;
      return json({ok:true,status:"DEMO_VERIFIED",verified:true,
        login:login.toString(),accountType:1,server:fresh.server,
        mode:fresh.mode,readbackSource:"MT5_INVESTOR_BROKER",
        readOnly:true,credentialScope:"INVESTOR_READ_ONLY",
        balance:fresh.balance,equity:fresh.equity,currency:fresh.currency,
        positions:fresh.positions,asOf:new Date().toISOString(),
        brokerOrders:false,liveMoneyLocked:true});
    }
    if(verified){
      await sql`
        update ai_trade.mt5_demo_accounts
        set last_verified_at=now(),is_active=true
        where account_login=${login}
      `;
    }

    return json({
      ok:true,
      status:verified?"DEMO_VERIFIED":"ACCOUNT_NOT_ACCEPTED_AS_DEMO",
      login:login.toString(),
      verified,
      accountType:account.accountType,
      server:account.serverName,
      company:account.company,
      currency:account.currency,
      balance:account.balance,
      leverage:account.leverage,
      tradeAllowed:account.tradeAllowed,
      readOnly:account.readOnly,
      bootstrapBuild,
      accountServerBuild:account.serverBuild,
      passwordExposed:false,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch{
    // Never echo SDK/SQL/WebSocket exceptions: they can contain broker secrets.
    return json({ok:false,status:"BROKER_VERIFIER_FAILED",verified:false,
      brokerOrders:false,liveMoneyLocked:true},503);
  }finally{c.close();}
});