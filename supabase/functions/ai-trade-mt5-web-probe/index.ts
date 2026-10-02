import postgres from "npm:postgres@3.4.9";
import WebSocket from "npm:ws@8.18.0";
import {createCipheriv,createDecipheriv,randomBytes,createHash} from "node:crypto";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8"}});

const WS_URI="wss://web.metatrader.app/terminal";
const INITIAL_KEY=Buffer.from("02de02a1a65cc794684fcbea1ecb0fd74ae657e43662c11eee885d2fd64f4964","hex");

async function authorized(req:Request){
  const rows=await sql`select secret from ai_trade.cron_auth where id=1`;
  const expected=String(rows[0]?.secret??"");
  return Boolean(expected)&&(req.headers.get("x-ai-trade-cron")??"")===expected;
}
function algo(key:Buffer){
  if(key.length===16)return "aes-128-cbc";
  if(key.length===24)return "aes-192-cbc";
  if(key.length===32)return "aes-256-cbc";
  throw new Error("INVALID_AES_KEY_LENGTH_"+key.length);
}
function encrypt(data:Buffer,key:Buffer){
  const c=createCipheriv(algo(key),key,Buffer.alloc(16));
  return Buffer.concat([c.update(data),c.final()]);
}
function decrypt(data:Buffer,key:Buffer){
  const d=createDecipheriv(algo(key),key,Buffer.alloc(16));
  return Buffer.concat([d.update(data),d.final()]);
}
function buildCommand(cmd:number,payload=Buffer.alloc(0)){
  const head=Buffer.alloc(4);
  randomBytes(2).copy(head,0);
  head.writeUInt16LE(cmd,2);
  return Buffer.concat([head,payload]);
}
function packOuter(body:Buffer){
  const head=Buffer.alloc(8);
  head.writeUInt32LE(body.length,0);
  head.writeUInt32LE(1,4);
  return Buffer.concat([head,body]);
}
function unpackOuter(frame:Buffer){
  if(frame.length<8)throw new Error("OUTER_TOO_SHORT");
  const len=frame.readUInt32LE(0),version=frame.readUInt32LE(4);
  const body=frame.subarray(8);
  if(len!==body.length)throw new Error("OUTER_LENGTH_MISMATCH");
  if(version!==1)throw new Error("OUTER_VERSION_"+version);
  return body;
}
function parseFrame(data:Buffer){
  if(data.length<5)throw new Error("INNER_TOO_SHORT");
  return {cmd:data.readUInt16LE(2),code:data.readUInt8(4),body:data.subarray(5)};
}
function fixedUtf16(value:string,size:number){
  const src=Buffer.from(value,"utf16le"),out=Buffer.alloc(size);
  src.copy(out,0,0,Math.min(src.length,size));
  return out;
}
function u32(v:number){const b=Buffer.alloc(4);b.writeUInt32LE(v>>>0);return b;}
function u64(v=0){const b=Buffer.alloc(8);b.writeBigUInt64LE(BigInt(v));return b;}
function buildCid(){
  const uniq=randomBytes(3).readUIntBE(0,3).toString();
  return createHash("sha1").update(["linux","1","en-US","0x0",uniq].join(";")).digest().subarray(0,16);
}
function buildInitPayload(cid:Buffer){
  return Buffer.concat([
    u32(0),
    fixedUtf16("",64),
    fixedUtf16("",128),
    cid,
    fixedUtf16("",64),
    fixedUtf16("",64),
    u64(0),
    fixedUtf16("",128),
    u32(0),
    fixedUtf16("",256),
    u64(0),
  ]);
}
async function runProbe(){
  const ws=new WebSocket(WS_URI,{headers:{Origin:"https://web.metatrader.app"}});
  ws.binaryType="arraybuffer";
  const queue:Buffer[]=[];
  const waiters:Array<(b:Buffer)=>void>=[];
  let wsError:Error|null=null;

  ws.on("message",(data:any)=>{
    const b=Buffer.isBuffer(data)?data:Buffer.from(data);
    const waiter=waiters.shift();
    if(waiter)waiter(b);else queue.push(b);
  });
  ws.on("error",(e:any)=>{wsError=e instanceof Error?e:new Error(String(e));});

  await new Promise<void>((resolve,reject)=>{
    const t=setTimeout(()=>reject(new Error("WS_OPEN_TIMEOUT")),15000);
    ws.once("open",()=>{clearTimeout(t);resolve();});
    ws.once("error",(e:any)=>{clearTimeout(t);reject(e);});
  });

  const nextRaw=()=>new Promise<Buffer>((resolve,reject)=>{
    if(queue.length)return resolve(queue.shift()!);
    if(wsError)return reject(wsError);
    const t=setTimeout(()=>reject(new Error("WS_RECV_TIMEOUT")),15000);
    waiters.push((b)=>{clearTimeout(t);resolve(b);});
  });

  let key=INITIAL_KEY;
  const send=async(cmd:number,payload:Buffer)=>{
    const encrypted=encrypt(buildCommand(cmd,payload),key);
    ws.send(packOuter(encrypted));
    for(let i=0;i<6;i++){
      const raw=await nextRaw();
      const frame=parseFrame(decrypt(unpackOuter(raw),key));
      if(frame.cmd===cmd)return frame;
    }
    throw new Error("EXPECTED_CMD_NOT_RECEIVED_"+cmd);
  };

  try{
    const bootstrap=await send(0,Buffer.alloc(64));
    if(bootstrap.code!==0)throw new Error("BOOTSTRAP_CODE_"+bootstrap.code);
    if(bootstrap.body.length<82)throw new Error("BOOTSTRAP_BODY_SHORT_"+bootstrap.body.length);
    const build=bootstrap.body.readUInt16LE(0);
    const newKey=bootstrap.body.subarray(66);
    if(![16,24,32].includes(newKey.length))throw new Error("BOOTSTRAP_KEY_LENGTH_"+newKey.length);
    key=Buffer.from(newKey);

    const cid=buildCid();
    const initPayload=buildInitPayload(cid);
    if(initPayload.length!==744)throw new Error("INIT_PAYLOAD_LENGTH_"+initPayload.length);
    const init=await send(29,initPayload);

    return {
      ok:init.code===0,
      status:init.code===0?"MT5_WEB_INIT_PASS":"MT5_WEB_INIT_REJECTED",
      websocket:"CONNECTED",
      bootstrapCode:bootstrap.code,
      serverBuild:build,
      negotiatedKeyBytes:key.length,
      initCode:init.code,
      initBodyBytes:init.body.length,
      brokerOrders:false,
      liveMoneyLocked:true,
      identitySent:false,
      externalAccountCreated:false
    };
  }finally{
    try{ws.close();}catch{}
  }
}

Deno.serve(async(req)=>{
  try{
    if(!(await authorized(req)))return json({ok:false,status:"UNAUTHORIZED"},401);
    const result=await runProbe();
    await sql`insert into ai_trade.events(event_type,result,details)
      values('mt5_web_protocol_probe',${String(result.status)},${JSON.stringify(result)}::jsonb)`;
    return json(result);
  }catch(error){
    const message=error instanceof Error?error.message:String(error);
    const result={ok:false,status:"MT5_WEB_PROBE_ERROR",message,brokerOrders:false,liveMoneyLocked:true,identitySent:false,externalAccountCreated:false};
    await sql`insert into ai_trade.events(event_type,result,details)
      values('mt5_web_protocol_probe','ERROR',${JSON.stringify(result)}::jsonb)`;
    return json(result,500);
  }
});