/* First-party only: no chart/CDN scripts in the MT5 credential entry page. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(typeof document!=="undefined"&&typeof window!=="undefined")api.start(document,window);
})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const WEB_ORIGIN="https://trankhanhduy1508-maker.github.io";
const WEB_PREFIX="/AI-TRADE/";
const SUPABASE="https://oziktadfeenydvgobudr.supabase.co";
const API=SUPABASE+"/functions/v1/ai-trade-founder-mt5/";
function trustedLocation(loc){
  return loc?.origin===WEB_ORIGIN&&loc?.pathname?.startsWith(WEB_PREFIX);
}
function authUrl(loc){
  if(!trustedLocation(loc))return null;
  const url=new URL(SUPABASE+"/auth/v1/authorize");
  url.searchParams.set("provider","google");
  url.searchParams.set("redirect_to",loc.origin+loc.pathname);
  return url.toString();
}
function demoPayload(login,server,password){
  const id=String(login??"").trim();
  const s=String(server??"");
  const p=String(password??"");
  if(!/^[1-9][0-9]{4,14}$/.test(id)||s!=="MetaQuotes-Demo"||
     p.length<4||p.length>32)return null;
  return {login:id,server:s,password:p};
}
function visualStatus(account,trading){
  if(trading?.liveMoneyLocked!==true)return "TRẠNG THÁI AN TOÀN KHÔNG XÁC ĐỊNH";
  if(!account)return "Chưa có tài khoản MT5 DEMO được liên kết.";
  const recent=account.recentlyVerified===true;
  return [
    "Tài khoản: "+String(account.login??"—"),
    "Máy chủ: "+String(account.server??"—"),
    "Xác minh gần đây: "+(recent?"CÓ (không phải phiên trade chạy nền)":"KHÔNG / ĐÃ HẾT HẠN"),
    "Xác minh lúc: "+String(account.verifiedAt??"—"),
    "Model được duyệt: "+(trading.modelApproved===true?"CÓ":"CHƯA"),
    "Risk Engine: "+(trading.riskApproved===true?"ĐÃ DUYỆT":"CHƯA DUYỆT"),
    "The5ers gate: "+String(trading.the5ersReadiness??"CHƯA RÕ"),
    "Auto Trade: "+(trading.autoTradeActive===true?"HOẠT ĐỘNG":"LOCKED"),
    "Live-money: LOCKED"
  ].join("\n");
}
function start(doc,win){
  const get=id=>doc.getElementById(id);
  const msg=get("message"),google=get("googleLogin"),logout=get("logout");
  const panel=get("privatePanel"),info=get("accountInfo"),form=get("demoForm");
  const login=get("mt5Login"),server=get("mt5Server"),pass=get("mt5Password");
  let token="",expiresAt=0;
  const tell=v=>{msg.textContent=String(v);};
  const clear=()=>{token="";expiresAt=0;pass.value="";panel.hidden=true;logout.hidden=true;google.hidden=false;};
  function active(){return token!==""&&Date.now()<expiresAt;}
  async function request(path,options={}){
    if(!active())throw Error("Phiên Google hết hạn. Hãy đăng nhập lại.");
    const res=await win.fetch(API+path,{
      ...options,cache:"no-store",credentials:"omit",
      headers:{...(options.headers??{}),Authorization:"Bearer "+token}
    });
    const data=await res.json().catch(()=>null);
    if(!res.ok||!data?.ok)throw Error(String(data?.status??"Yêu cầu không thành công"));
    return data;
  }
  async function refresh(){
    const state=await request("status");
    panel.hidden=false;
    info.textContent=visualStatus(state.account,state.trading);
    if(state.account?.login)login.value=String(state.account.login);
    tell("Google Founder đã xác thực. Tài khoản demo chỉ đọc; quyền đặt lệnh chưa mở.");
  }
  const supported=trustedLocation(win.location);
  if(!supported){
    google.disabled=true;
    tell("BLOCKED: Chỉ cho phép đăng nhập từ Web App HTTPS chính thức sau khi xuất bản và cấu hình OAuth redirect. Không nhập MT5 trên trang xem trước.");
    return;
  }
  const hash=new URLSearchParams(win.location.hash.replace(/^#/,""));
  const candidate=hash.get("access_token")??"";
  // Clear OAuth callback fragment BEFORE doing any network request.
  if(win.location.hash)win.history.replaceState(null,"",win.location.pathname+win.location.search);
  if(candidate&&hash.get("token_type")?.toLowerCase()==="bearer"){
    const expiry=Number(hash.get("expires_in")??0);
    if(expiry>0&&Number.isFinite(expiry)){
      token=candidate;expiresAt=Date.now()+Math.min(expiry,3600)*1000;
      google.hidden=true;logout.hidden=false;
      refresh().catch(e=>{clear();tell("Phiên không hợp lệ: "+e.message);});
    }else tell("Phiên OAuth không hợp lệ. Hãy đăng nhập lại.");
  }else if(hash.get("error")){
    tell("Google OAuth chưa hoàn tất hoặc redirect chưa được cấp quyền.");
  }else tell("Đăng nhập Google Founder để xem và xác minh MT5 DEMO.");
  google.addEventListener("click",()=>{
    const url=authUrl(win.location);
    if(url)win.location.assign(url);
  });
  logout.addEventListener("click",()=>{clear();tell("Đã đóng phiên cục bộ. Không thay đổi quyền MT5 trên máy chủ.");});
  form.addEventListener("submit",async(event)=>{
    event.preventDefault();
    const payload=demoPayload(login.value,server.value,pass.value);
    if(!payload){tell("Dữ liệu không hợp lệ. Chỉ hỗ trợ MetaQuotes-Demo đã liên kết.");pass.value="";return;}
    get("verifyDemo").disabled=true;
    tell("Đang xác minh tài khoản DEMO với máy chủ. Không gửi lệnh.");
    try{
      const data=await request("verify-demo",{
        method:"POST",headers:{"content-type":"application/json"},
        body:JSON.stringify(payload)
      });
      if(data.status!=="DEMO_VERIFIED_READ_ONLY")throw Error("Không xác minh được tài khoản DEMO.");
      await refresh();
    }catch(e){tell("Kết nối chưa được xác minh: "+e.message);}
    finally{pass.value="";get("verifyDemo").disabled=false;}
  });
}
return {trustedLocation,authUrl,demoPayload,visualStatus,start};
});
