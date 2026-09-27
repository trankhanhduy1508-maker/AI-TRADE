import postgres from "npm:postgres@3.4.9";

const sql=postgres(Deno.env.get("SUPABASE_DB_URL")!,{prepare:false,max:1,connect_timeout:10,idle_timeout:20});
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});

async function wsCall(message:Record<string,unknown>,timeoutMs=15000):Promise<any>{
  return await new Promise((resolve,reject)=>{
    const ws=new WebSocket("wss://ws.derivws.com/websockets/v3?app_id=1089");
    const timer=setTimeout(()=>{try{ws.close();}catch{};reject(new Error("DERIV_WS_TIMEOUT"));},timeoutMs);
    ws.onopen=()=>ws.send(JSON.stringify(message));
    ws.onerror=()=>{clearTimeout(timer);reject(new Error("DERIV_WS_ERROR"));};
    ws.onmessage=(ev)=>{
      clearTimeout(timer);
      try{
        const data=JSON.parse(String(ev.data));
        ws.close();
        resolve(data);
      }catch(error){
        ws.close();
        reject(error);
      }
    };
  });
}

Deno.serve(async(req)=>{
  try{
    const response=await wsCall({residence_list:1});
    if(response?.error){
      return json({ok:false,status:"DERIV_ERROR",code:response.error.code,message:response.error.message,brokerOrders:false,liveMoneyLocked:true},502);
    }
    const list=Array.isArray(response?.residence_list)?response.residence_list:[];
    const vn=list.find((x:any)=>String(x?.value??"").toLowerCase()==="vn")??null;
    return json({
      ok:true,
      status:"PUBLIC_PROBE_OK",
      appId:1089,
      vietnam:vn?{
        value:vn.value??null,
        text:vn.text??null,
        disabled:vn.disabled??false,
        phone_idd:vn.phone_idd??null
      }:null,
      accountCreated:false,
      brokerOrders:false,
      liveMoneyLocked:true
    });
  }catch(error){
    return json({ok:false,status:"ERROR",message:error instanceof Error?error.message:String(error),accountCreated:false,brokerOrders:false,liveMoneyLocked:true},500);
  }
});