import{CONFIG}from"./config.js";
export class DashboardApi{
  constructor(token){this.token=token}
  async getOverview(){
    const u=new URL(CONFIG.apiBase);u.searchParams.set("format","json");u.searchParams.set("t",this.token);
    const r=await fetch(u,{cache:"no-store"});if(!r.ok)throw new Error("Overview API HTTP "+r.status);return r.json();
  }
  async getFeature(feature,params={}){
    const u=new URL(CONFIG.apiBase);u.searchParams.set("format",feature);u.searchParams.set("t",this.token);
    Object.entries(params).forEach(([k,v])=>u.searchParams.set(k,String(v)));
    const r=await fetch(u,{cache:"no-store"});if(!r.ok)throw new Error(`${feature} API HTTP ${r.status}`);return r.json();
  }
}
