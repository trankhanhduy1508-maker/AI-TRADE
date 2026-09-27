import{CONFIG}from"./config.js";

const AUTH_KEY="cws-ai-trade-google-token";

export async function getGoogleUser(){
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
    if(!r.ok){localStorage.removeItem(AUTH_KEY);return null}
    return await r.json();
  }catch{return null}
}

export function signInWithGoogle(){
  const clean=location.href.split("#")[0];
  const u=new URL(CONFIG.supabaseUrl+"/auth/v1/authorize");
  u.searchParams.set("provider","google");
  u.searchParams.set("redirect_to",clean);
  location.href=u.toString();
}

export function signOutGoogle(){
  localStorage.removeItem(AUTH_KEY);
  location.reload();
}
