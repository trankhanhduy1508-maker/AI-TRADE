import postgres from "npm:postgres@3.4.9";
import WebSocket from "npm:ws@8.18.3";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{
  prepare:false,max:1,connect_timeout:10,idle_timeout:20
});

const WS_URI="wss://web.metatrader.app/terminal";
const INITIAL_KEY_HEX="02de02a1a65cc794684fcbea1ecb0fd74ae657e43662c11eee885d2fd64f4964";

const CMD_BOOTSTRAP=0;
const CMD_VERIFY_CODE=27;
const CMD_INIT=29;
const CMD_OPEN_DEMO=30;

const enc=new TextEncoder();

function json(body:unknown,status=200){
  return new Response(JSON.stringify(body),{
    status,headers:{"content-type":"application/json; charset=utf-8"}
  });
}

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function concat(...parts:Uint8Array[]){
  const len=parts.reduce((n,p)=>n+p.length,0);
  const out=new Uint8Array(len);
  let o=0;
  for(const p of parts){out.set(p,o);o+=p.length;}
  return out;
}

function u16le(v:number){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,v,true);return b;}
function i16le(v:number){const b=new Uint8Array(2);new DataView(b.buffer).setInt16(0,v,true);return b;}
function u32le(v:number){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,v>>>0,true);return b;}
function u64le(v:number|bigint){
  const b=new Uint8Array(8);
  new DataView(b.buffer).setBigUint64(0,BigInt(v),true);
  return b;
}
function f64le(v:number){const b=new Uint8Array(8);new DataView(b.buffer).setFloat64(0,v,true);return b;}

function hexToBytes(hex:string){
  const out=new Uint8Array(hex.length/2);
  for(let i=0;i<out.length;i++)out[i]=parseInt(hex.slice(i*2,i*2+2),16);
  return out;
}

function fixedUtf16(value:string,size:number){
  const out=new Uint8Array(size);
  const s=value.slice(0,Math.floor(size/2));
  for(let i=0;i<s.length;i++){
    const code=s.charCodeAt(i);
    out[i*2]=code&255;
    out[i*2+1]=(code>>>8)&255;
  }
  return out;
}

function readUtf16(data:Uint8Array){
  let s="";
  for(let i=0;i+1<data.length;i+=2){
    const c=data[i]|(data[i+1]<<8);
    if(c===0)break;
    s+=String.fromCharCode(c);
  }
  return s;
}

function randomBytes(n:number){
  const b=new Uint8Array(n);
  crypto.getRandomValues(b);
  return b;
}

async function importAes(key:Uint8Array){
  return crypto.subtle.importKey("raw",key,{name:"AES-CBC"},false,["encrypt","decrypt"]);
}

async function aesEncrypt(key:Uint8Array,data:Uint8Array){
  const k=await importAes(key);
  return new Uint8Array(await crypto.subtle.encrypt(
    {name:"AES-CBC",iv:new Uint8Array(16)},k,data
  ));
}

async function aesDecrypt(key:Uint8Array,data:Uint8Array){
  const k=await importAes(key);
  return new Uint8Array(await crypto.subtle.decrypt(
    {name:"AES-CBC",iv:new Uint8Array(16)},k,data
  ));
}

function commandInner(cmd:number,payload:Uint8Array){
  return concat(randomBytes(2),u16le(cmd),payload);
}

function outerFrame(encrypted:Uint8Array){
  return concat(u32le(encrypted.length),u32le(1),encrypted);
}

function initPayload(cid:Uint8Array){
  return concat(
    u32le(0),
    fixedUtf16("",64),
    fixedUtf16("",128),
    cid,
    fixedUtf16("",64),
    fixedUtf16("",64),
    u64le(0),
    fixedUtf16("",128),
    u32le(0),
    fixedUtf16("",256),
    u64le(0)
  );
}

type Opening={
  firstName:string;
  secondName:string;
  email:string;
  emailCode:number;
};

function openingBase(r:Opening){
  const full=[r.firstName,r.secondName].filter(Boolean).join(" ");
  return concat(
    fixedUtf16(full,256),
    fixedUtf16("",128),
    fixedUtf16("",64),
    fixedUtf16("VN",64),
    fixedUtf16("",64),
    fixedUtf16("",64),
    fixedUtf16("",32),
    fixedUtf16("",256),
    fixedUtf16("",64),
    fixedUtf16(r.email,128),
    f64le(100000),
    u32le(100),
    u32le(0),
    u32le(1),
    fixedUtf16("web.metatrader.app",128),
    fixedUtf16("mt5-demo-bootstrap",64),
    fixedUtf16("ai-trade-cloud",64),
    u32le(r.emailCode),
    u32le(0),
    fixedUtf16(r.firstName,128),
    fixedUtf16(r.secondName,128),
    u32le(1)
  );
}

class Mt5Socket{
  ws:WebSocket;
  key:Uint8Array;

  constructor(){
    this.key=hexToBytes(INITIAL_KEY_HEX);
    this.ws=new WebSocket(WS_URI,{
      headers:{Origin:"https://web.metatrader.app"}
    });
  }

  async open(){
    await new Promise<void>((resolve,reject)=>{
      const timer=setTimeout(()=>reject(new Error("WS_OPEN_TIMEOUT")),15000);
      this.ws.once("open",()=>{clearTimeout(timer);resolve();});
      this.ws.once("error",(e)=>{clearTimeout(timer);reject(e);});
    });
  }

  async command(cmd:number,payload=new Uint8Array()){
    const encrypted=await aesEncrypt(this.key,commandInner(cmd,payload));
    const frame=outerFrame(encrypted);

    const response=new Promise<{cmd:number;code:number;body:Uint8Array}>((resolve,reject)=>{
      const timer=setTimeout(()=>{
        cleanup(); reject(new Error("CMD_"+cmd+"_TIMEOUT"));
      },30000);

      const onError=(e:unknown)=>{cleanup();reject(e);};
      const onMessage=async(data:WebSocket.RawData)=>{
        try{
          const raw=data instanceof Uint8Array?new Uint8Array(data):new Uint8Array(data as ArrayBuffer);
          if(raw.length<8)return;
          const dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);
          const bodyLen=dv.getUint32(0,true);
          if(bodyLen!==raw.length-8)return;
          const decrypted=await aesDecrypt(this.key,raw.slice(8));
          if(decrypted.length<5)return;
          const rc=new DataView(decrypted.buffer,decrypted.byteOffset,decrypted.byteLength);
          const responseCmd=rc.getUint16(2,true);
          if(responseCmd!==cmd)return;
          cleanup();
          resolve({cmd:responseCmd,code:decrypted[4],body:decrypted.slice(5)});
        }catch(e){cleanup();reject(e);}
      };
      const cleanup=()=>{
        clearTimeout(timer);
        this.ws.off("message",onMessage);
        this.ws.off("error",onError);
      };
      this.ws.on("message",onMessage);
      this.ws.on("error",onError);
    });

    this.ws.send(frame);
    return response;
  }

  close(){try{this.ws.close();}catch{}}
}

async function storeDemo(
  login:bigint,
  password:string,
  investorPassword:string,
  serverBuild:number,
  metadata:Record<string,unknown>
){
  await sql`
    insert into ai_trade.mt5_demo_accounts(
      provider,server,login,password_cipher,investor_password_cipher,
      server_build,account_mode,verified,metadata
    )
    values(
      'METAQUOTES','MetaQuotes-Demo',${login},
      pgp_sym_encrypt(${password},(select key_text from ai_trade.mt5_demo_secret where id=1)),
      case when ${investorPassword}='' then null
        else pgp_sym_encrypt(${investorPassword},(select key_text from ai_trade.mt5_demo_secret where id=1))
      end,
      ${serverBuild},'DEMO',false,${JSON.stringify(metadata)}::jsonb
    )
    on conflict(login) do update set
      password_cipher=excluded.password_cipher,
      investor_password_cipher=excluded.investor_password_cipher,
      server_build=excluded.server_build,
      metadata=excluded.metadata
  `;
}

Deno.serve(async(req)=>{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);

  const body=await req.json().catch(()=>({})) as {
    email?:string;
    emailCode?:number;
    allowCreate?:boolean;
  };

  const opening:Opening={
    firstName:"Duy",
    secondName:"Tran",
    email:String(body.email??"").trim(),
    emailCode:Number(body.emailCode??0)||0
  };

  const socket=new Mt5Socket();
  try{
    await socket.open();

    const bootstrap=await socket.command(CMD_BOOTSTRAP,new Uint8Array(64));
    if(bootstrap.code!==0||bootstrap.body.length<82){
      return json({ok:false,status:"BOOTSTRAP_FAILED",code:bootstrap.code,bodyLength:bootstrap.body.length});
    }

    const bdv=new DataView(
      bootstrap.body.buffer,bootstrap.body.byteOffset,bootstrap.body.byteLength
    );
    const serverBuild=bdv.getUint16(0,true);
    const sessionKey=bootstrap.body.slice(66);
    if(![16,24,32].includes(sessionKey.length)){
      return json({ok:false,status:"SESSION_KEY_LENGTH_UNEXPECTED",serverBuild,keyLength:sessionKey.length});
    }
    socket.key=sessionKey;

    const cid=randomBytes(16);
    const init=await socket.command(CMD_INIT,initPayload(cid));
    if(init.code!==0){
      return json({ok:false,status:"INIT_FAILED",serverBuild,code:init.code});
    }

    const base=openingBase(opening);
    const verifyPayload=concat(i16le(serverBuild),cid,base);
    const verify=await socket.command(CMD_VERIFY_CODE,verifyPayload);
    if(verify.code!==0){
      return json({ok:false,status:"VERIFY_PROBE_FAILED",serverBuild,code:verify.code});
    }

    const emailRequired=Boolean(verify.body[0]??0);
    const phoneRequired=Boolean(verify.body[1]??0);

    if(phoneRequired){
      return json({
        ok:true,status:"BLOCKED_PHONE_VERIFICATION",
        serverBuild,emailRequired,phoneRequired,
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    if(emailRequired&&!opening.email){
      return json({
        ok:true,status:"EMAIL_REQUIRED",
        serverBuild,emailRequired:true,phoneRequired:false,
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    if(emailRequired&&!opening.emailCode){
      return json({
        ok:true,status:"EMAIL_CODE_REQUIRED",
        serverBuild,emailRequired:true,phoneRequired:false,
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    if(body.allowCreate!==true){
      return json({
        ok:true,status:"READY_TO_CREATE_DEMO",
        serverBuild,emailRequired,phoneRequired,
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    if(emailRequired&&opening.emailCode){
      const submitted=await socket.command(40,base);
      const emailOk=Boolean(submitted.body[0]??0);
      const phoneOk=Boolean(submitted.body[1]??0);
      if(submitted.code!==0||!emailOk||phoneOk){
        return json({
          ok:false,status:"EMAIL_VERIFICATION_REJECTED",
          serverBuild,code:submitted.code,emailOk,phoneOk,
          accountCreated:false,brokerOrders:false,liveMoneyLocked:true
        });
      }
    }

    const created=await socket.command(CMD_OPEN_DEMO,base);
    if(created.code!==0||created.body.length<72){
      return json({
        ok:false,status:"DEMO_CREATE_FAILED",
        serverBuild,code:created.code,bodyLength:created.body.length,
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    const cdv=new DataView(created.body.buffer,created.body.byteOffset,created.body.byteLength);
    const resultCode=cdv.getUint32(0,true);
    const login=cdv.getBigInt64(4,true);
    const password=readUtf16(created.body.slice(12,44));
    const investorPassword=readUtf16(created.body.slice(44,76));

    if(resultCode!==0||login<=0n||!password){
      return json({
        ok:false,status:"DEMO_CREATE_RESULT_FAILED",
        serverBuild,resultCode,loginPresent:login>0n,passwordPresent:Boolean(password),
        accountCreated:false,brokerOrders:false,liveMoneyLocked:true
      });
    }

    await storeDemo(login,password,investorPassword,serverBuild,{
      source:"METAQUOTES_WEBTERMINAL_CMD30",
      emailVerificationUsed:emailRequired,
      createdVia:"SUPABASE_EDGE",
      liveMoney:false
    });

    return json({
      ok:true,status:"DEMO_CREATED",
      server:"MetaQuotes-Demo",
      serverBuild,
      login:login.toString(),
      credentialStoredEncrypted:true,
      passwordExposed:false,
      accountMode:"DEMO",
      accountCreated:true,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch(error){
    return json({
      ok:false,status:"ERROR",
      error:error instanceof Error?error.message:String(error),
      accountCreated:false,brokerOrders:false,liveMoneyLocked:true
    },500);
  }finally{
    socket.close();
  }
});
