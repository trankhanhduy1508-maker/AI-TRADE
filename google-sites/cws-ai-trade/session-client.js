(function(factory){const api=factory();if(typeof module==='object')module.exports=api;if(typeof document!=='undefined')api.start(document,window);})(function(){
'use strict';
const ROOT='https://oziktadfeenydvgobudr.supabase.co/functions/v1/ai-trade-mt5-session/mt5/';
function payload(login,password,server){
 const id=String(login).trim();
 if(!/^[1-9][0-9]{4,14}$/.test(id)||!Number.isSafeInteger(Number(id))||server!=='MetaQuotes-Demo'||typeof password!=='string'||password.length<4||password.length>32||/[\u0000-\u001f\u007f]/.test(password))return null;
 return {login:Number(id),password,server,remember:false};
}
function accountText(data){
 const a=data?.account;
 if(!a||a.trade_mode!=='DEMO'||a.server!=='MetaQuotes-Demo'||!['CONNECTED','CONNECTED_READ_ONLY'].includes(data.status))return 'Tài khoản không hợp lệ hoặc chưa được xác minh.';
 return ['MT5 DEMO: '+a.login,'Server: '+a.server,'Quyền broker: '+a.trade_permission,'Balance khi đăng nhập: '+a.balance,'Equity từ snapshot đăng nhập: '+a.equity,'Tự giao dịch: chưa bật — cần Risk Engine và đường đặt lệnh được kiểm chứng.','Đây là xác minh đăng nhập; chưa có bằng chứng khớp lệnh.'].join('\n');
}
function start(doc,win){
 const get=id=>doc.getElementById(id),msg=get('message'),info=get('accountInfo');let session='';
 const tell=text=>msg.textContent=String(text);
 const clear=()=>{session='';get('mt5Password').value='';get('refresh').disabled=true;get('disconnect').disabled=true;};
 async function request(path,{method='GET',body}={}){
  const headers={'content-type':'application/json','x-cws-client':'web','x-cws-client-version':'0.7.0-lab'};
  if(session)headers.authorization='Bearer '+session;
  const r=await win.fetch(ROOT+path,{method,headers,body:body?JSON.stringify(body):undefined,credentials:'omit',cache:'no-store',signal:AbortSignal.timeout(130000)});
  const data=await r.json();if(!r.ok)throw Error(String(data.status??'CONNECTION_FAILED'));return data;
 }
 get('connect').disabled=false;
 get('demoForm').addEventListener('submit',async event=>{
  event.preventDefault();const input=payload(get('mt5Login').value,get('mt5Password').value,get('mt5Server').value);get('mt5Password').value='';
  if(!input){tell('Nhập Login, mật khẩu giao dịch và đúng server MetaQuotes-Demo.');return;}
  if(session){input.password='';tell('Ngắt phiên hiện tại trước khi kết nối tài khoản khác.');return;}
  get('connect').disabled=true;tell('Đang xác minh với MT5. Có thể mất khoảng 2 phút.');
  try{
   const data=await request('session/connect',{method:'POST',body:input});
   if(!['CONNECTED','CONNECTED_READ_ONLY'].includes(data.status)||data.account?.trade_mode!=='DEMO'||data.account?.server!=='MetaQuotes-Demo'||String(data.account?.login)!==String(input.login)||typeof data.session_id!=='string'||data.session_id.length<40||data.session_id.length>128)throw Error('UNVERIFIED_DEMO_RESPONSE');
   session=data.session_id;info.textContent=accountText(data);get('refresh').disabled=false;get('disconnect').disabled=false;tell('Đăng nhập MT5 DEMO đã xác minh. Tự đặt lệnh vẫn chưa bật.');
  }catch(e){clear();info.textContent='Chưa có phiên được xác minh.';tell('Kết nối chưa thành công: '+e.message);}
  finally{input.password='';get('connect').disabled=false;}
 });
 get('refresh').addEventListener('click',async()=>{try{info.textContent=accountText(await request('session/account'));tell('Đã đọc snapshot phiên; chưa phải P/L theo tick.');}catch(e){clear();tell('Phiên không đọc được: '+e.message);}});
 get('disconnect').addEventListener('click',async()=>{try{await request('session/disconnect',{method:'POST'});clear();info.textContent='Đã ngắt phiên.';tell('Đã ngắt kết nối.');}catch(e){tell('Chưa xác nhận ngắt phiên trên máy chủ: '+e.message);}});
 request('brokers').then(data=>{const labels={RUNTIME_DISABLED:'Bot chưa bật',DEMO_SEND_DISABLED:'Đặt lệnh DEMO chưa mở',RISK_NOT_APPROVED:'Giới hạn rủi ro chưa duyệt',PROVIDER_NOT_READY:'Kết nối thực thi lệnh chưa sẵn sàng'};const b=Array.isArray(data.demo_autotrade_blockers)?data.demo_autotrade_blockers:[];get('readiness').textContent='Đường đặt lệnh: '+(b.length?b.map(x=>labels[x]??'Điều kiện phía máy chủ chưa đạt').join(' · '):'Cần kiểm chứng lệnh và vị thế trên broker.');}).catch(()=>get('readiness').textContent='Chưa đọc được điều kiện tự giao dịch.');
 win.addEventListener('pagehide',()=>{session='';get('mt5Password').value='';});
}
return {payload,accountText,start};
});
