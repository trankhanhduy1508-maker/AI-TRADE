import WebSocket from "npm:ws@8.18.3";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});

const WS_URI="wss://web.metatrader.app/terminal";
const INITIAL_KEY_OBFUSCATED="13ef13b2b76dd8:5795gdcfb2fdc1ge85bf768f54773d22fff996e3ge75g5:75";
const CMD_BOOTSTRAP=0;
const CMD_INIT=29;

const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}

function decodeInitialKey():Buffer{
  let decoded="";
  for(const ch of INITIAL_KEY_OBFUSCATED){
    const code=ch.charCodeAt(0);
    if(code===28) decoded+="&";
    else if(code===23) decoded+="!";
    else decoded+=String.fromCharCode(code-1);
  }
  return Buffer.from(decoded,"hex");
}

function algorithmForKey(key:Buffer){
  if(key.length===16) return "aes-128-cbc";
  if(key.length===24) return "aes-192-cbc";
  if(key.length===32) return "aes-256-cbc";
  throw new Error("INVALID_AES_KEY_LENGTH_"+key.length);
}

function encrypt(data:Buffer,key:Buffer){
  const cipher=createCipheriv(algorithmForKey(key),key,Buffer.alloc(16));
  return Buffer.concat([cipher.update(data),cipher.final()]);
}

function decrypt(data:Buffer,key:Buffer){
  const decipher=createDecipheriv(algorithmForKey(key),key,Buffer.alloc(16));
  return Buffer.concat([decipher.update(data),decipher.final()]);
}

function u16(v:number){const b=Buffer.alloc(2);b.writeUInt16LE(v);return b;}
function u32(v:number){const b=Buffer.alloc(4);b.writeUInt32LE(v>>>0);return b;}
function u64(v:number){const b=Buffer.alloc(8);b.writeBigUInt64LE(BigInt(Math.max(0,Math.trunc(v))));return b;}
function fixedUtf16(value:string,size:number){
  const raw=Buffer.from(value,"utf16le");
  const out=Buffer.alloc(size);
  raw.copy(out,0,0,Math.min(raw.length,size));
  return out;
}
function fixedBytes(value:Buffer,size:number){
  const out=Buffer.alloc(size);value.copy(out,0,0,Math.min(value.length,size));return out;
}
function buildCommand(cmd:number,payload=Buffer.alloc(0)){
  return Buffer.concat([randomBytes(2),u16(cmd),payload]);
}
function packOuter(body:Buffer){
  return Buffer.concat([u32(body.length),u32(1),body]);
}
function parseOuter(frame:Buffer){
  if(frame.length<8) throw new Error("OUTER_TOO_SHORT");
  const len=frame.readUInt32LE(0),version=frame.readUInt32LE(4);
  const body=frame.subarray(8);
  if(len!==body.length) throw new Error("OUTER_LENGTH_MISMATCH");
  return {version,body};
}
function parseResponse(data:Buffer){
  if(data.length<5) throw new Error("RESPONSE_TOO_SHORT");
  return {command:data.readUInt16LE(2),code:data.readUInt8(4),body:data.subarray(5)};
}
function buildInitPayload(cid:Buffer){
  return Buffer.concat([
    u32(0),
    fixedUtf16("",64),
    fixedUtf16("",128),
    fixedBytes(cid,16),
    fixedUtf16("",64),
    fixedUtf16("",64),
    u64(0),
    fixedUtf16("",128),
    u32(0),
    fixedUtf16("",256),
    u64(0),
  ]);
}

function waitOpen(ws:WebSocket,timeoutMs=12000){
  return new Promise<void>((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error("WS_OPEN_TIMEOUT")),timeoutMs);
    ws.once("open",()=>{clearTimeout(timer);resolve();});
    ws.once("error",(e)=>{clearTimeout(timer);reject(e);});
  });
}

function waitBinary(ws:WebSocket,timeoutMs=12000){
  return new Promise<Buffer>((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error("WS_RESPONSE_TIMEOUT")),timeoutMs);
    const onMessage=(data:WebSocket.RawData,isBinary:boolean)=>{
      if(!isBinary) return;
      clearTimeout(timer);
      ws.off("error",onError);
      resolve(Buffer.isBuffer(data)?data:Buffer.from(data as ArrayBuffer));
    };
    const onError=(e:Error)=>{clearTimeout(timer);ws.off("message",onMessage);reject(e);};
    ws.once("message",onMessage);
    ws.once("error",onError);
  });
}

async function sendAndReceive(ws:WebSocket,cmd:number,payload:Buffer,key:Buffer){
  const inner=buildCommand(cmd,payload);
  ws.send(packOuter(encrypt(inner,key)));
  const raw=await waitBinary(ws);
  const outer=parseOuter(raw);
  const frame=parseResponse(decrypt(outer.body,key));
  return {outerVersion:outer.version,...frame};
}

Deno.serve(async(req)=>{
  if(!(await authorized(req))) return json({ok:false,status:"UNAUTHORIZED"},401);
  let ws:WebSocket|null=null;
  try{
    const initialKey=decodeInitialKey();
    const cid=randomBytes(16);
    ws=new WebSocket(WS_URI,{
      headers:{Origin:"https://web.metatrader.app"},
      perMessageDeflate:false,
      handshakeTimeout:12000,
    });
    await waitOpen(ws);

    const bootstrap=await sendAndReceive(ws,CMD_BOOTSTRAP,Buffer.alloc(64),initialKey);
    if(bootstrap.command!==CMD_BOOTSTRAP||bootstrap.code!==0){
      throw new Error("BOOTSTRAP_REJECTED_"+bootstrap.command+"_"+bootstrap.code);
    }
    if(bootstrap.body.length<82){
      throw new Error("BOOTSTRAP_BODY_TOO_SHORT_"+bootstrap.body.length);
    }
    const serverBuild=bootstrap.body.readUInt16LE(0);
    const token=bootstrap.body.subarray(2,66);
    const sessionKey=bootstrap.body.subarray(66);
    if(![16,24,32].includes(sessionKey.length)){
      throw new Error("UNEXPECTED_SESSION_KEY_LENGTH_"+sessionKey.length);
    }

    const init=await sendAndReceive(ws,CMD_INIT,buildInitPayload(cid),sessionKey);
    if(init.command!==CMD_INIT||init.code!==0){
      throw new Error("INIT_REJECTED_"+init.command+"_"+init.code);
    }

    ws.close();
    return json({
      ok:true,
      status:"MT5_PROTOCOL_READY",
      endpoint:"web.metatrader.app",
      serverBuild,
      tokenLength:token.length,
      sessionKeyLength:sessionKey.length,
      bootstrapCode:bootstrap.code,
      initCode:init.code,
      demoCreated:false,
      emailSent:false,
      brokerOrders:false,
      liveMoneyLocked:true,
    });
  }catch(error){
    try{ws?.close();}catch(_){}
    return json({
      ok:false,
      status:"MT5_PROTOCOL_PROBE_FAILED",
      error:error instanceof Error?error.message:String(error),
      demoCreated:false,
      emailSent:false,
      brokerOrders:false,
      liveMoneyLocked:true,
    },500);
  }
});
