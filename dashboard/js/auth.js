import{CONFIG}from"./config.js";

const AUTH_KEY="cws-ai-trade-google-token";
const APPDEPLOY_USER_KEY="cws-ai-trade-appdeploy-user";

export async function getGoogleUser(){
  const external=localStorage.getItem(APPDEPLOY_USER_KEY);
  if(external){
    try{
      const u=JSON.parse(external);
      if(u?.email)return{email:u.email,user_metadata:{full_name:u.name||"",name:u.name||"",avatar_url:u.picture||""},provider:"appdeploy-google"};
    }catch{}
  }

  const hash=new URLSearchParams(location.hash.replace(/^#/,""));
  const fromHash=hash.get("access_token");
  if(fromHash){
    localStorage.setItem(AUTH_KEY,fromHash);
    history.replaceState(null,"",location.pathname+location.search);
  }
  const token=fromHash||localStorage.getItem(AUTH_KEY);
  if(!token)return null;
  try{
    const r=await fetch(CONFIG.supabaseUrl+"/auth/v1/user",{
      headers:{apikey:CONFIG.supabasePublishableKey,Authorization:"Bearer "+token},
      cache:"no-store"
    });
    if(!r.ok)return null;
    return await r.json();
  }catch{return null}
}

export function signInWithGoogle(){
  if(location.hostname.endsWith(".v2.appdeploy.ai")){
    location.href=location.origin;
    return;
  }
  const clean=location.href.split("#")[0];
  const u=new URL(CONFIG.supabaseUrl+"/auth/v1/authorize");
  u.searchParams.set("provider","google");
  u.searchParams.set("redirect_to",clean);
  location.href=u.toString();
}

export function signOutGoogle(){
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(APPDEPLOY_USER_KEY);
  if(location.hostname.endsWith(".v2.appdeploy.ai"))location.href=location.origin;
  else location.reload();
}
