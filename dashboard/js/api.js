import{CONFIG}from"./config.js";
export class DashboardApi{
  constructor(token){this.token=token;this.timings={}}
  async _fetch(name,u,options={}){
    const start=performance.now();
    const r=await fetch(u,{cache:"no-store",...options});
    this.timings[name]=Math.round(performance.now()-start);
    if(!r.ok)throw new Error(name+" API HTTP "+r.status);
    return r.json();
  }
  getTimings(){return{...this.timings}}
  async getOverview(){
    const u=new URL(CONFIG.apiBase);u.searchParams.set("format","json");u.searchParams.set("t",this.token);
    return this._fetch("overview",u);
  }
  async getFeature(feature,params={}){
    const u=new URL(CONFIG.apiBase);u.searchParams.set("format",feature);u.searchParams.set("t",this.token);
    Object.entries(params).forEach(([k,v])=>u.searchParams.set(k,String(v)));
    return this._fetch(feature,u);
  }
  async founderAction(tokenId,action){
    const u=new URL(CONFIG.apiBase);u.searchParams.set("format","admin-testers");u.searchParams.set("t",this.token);
    return this._fetch("admin-action",u,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({tokenId,action})});
  }
}
