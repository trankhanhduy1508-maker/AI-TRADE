import postgres from "npm:postgres@3.4.9";
import WebSocket from "npm:ws@8.18.3";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const WS_URI="wss://web.metatrader.app/terminal";
const INITIAL_KEY_HEX="02de02a1a65cc794684fcbea1ecb0fd74ae657e43662c11eee885d2fd64f4964";

const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json"}});
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
          const raw=new Uint8Array(data as any); if(raw.length<8)return;
          const dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);
          if(dv.getUint32(0,true)!==raw.length-8)return;
          const dec=await crypt(this.key,raw.slice(8),"decrypt"); if(dec.length<5)return;
          const id=new DataView(dec.buffer,dec.byteOffset,dec.byteLength).getUint16(2,true);
          if(id!==cmd)return; cleanup(); resolve({code:dec[4],body:dec.slice(5)});
        }catch(e){cleanup();reject(e);}
      };
      const cleanup=()=>{clearTimeout(t);this.ws.off("message",onMsg);this.ws.off("error",onErr);};
      this.ws.on("message",onMsg);this.ws.on("error",onErr);
    });
    this.ws.send(outer(encrypted)); return response;
  }
  close(){try{this.ws.close();}catch{}}
}

Deno.serve(async(req)=>{
  if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
  const c=new Client();
  try{
    await c.open();
    const boot=await c.command(0,new Uint8Array(64));
    if(boot.code!==0||boot.body.length<82)return json({ok:false,status:"BOOTSTRAP_FAILED",code:boot.code,bodyLength:boot.body.length});
    const dv=new DataView(boot.body.buffer,boot.body.byteOffset,boot.body.byteLength);
    const serverBuild=dv.getUint16(0,true);
    const sessionKey=boot.body.slice(66);
    if(![16,24,32].includes(sessionKey.length))return json({ok:false,status:"BAD_SESSION_KEY",serverBuild,keyLength:sessionKey.length});
    c.key=sessionKey;
    const cid=randomBytes(16);
    const init=await c.command(29,initPayload(cid));
    return json({
      ok:init.code===0,
      status:init.code===0?"MT5_PROTOCOL_READY":"MT5_INIT_FAILED",
      server:"MetaQuotes-Demo",
      serverBuild,
      sessionKeyLength:sessionKey.length,
      initCode:init.code,
      accountCreated:false,
      authenticated:false,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch(e){
    return json({ok:false,status:"ERROR",error:e instanceof Error?e.message:String(e),accountCreated:false,brokerOrders:false,liveMoneyLocked:true},500);
  }finally{c.close();}
});