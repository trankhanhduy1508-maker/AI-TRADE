import{CONFIG}from"./config.js";
const GOOGLE_AUTH_KEY="cws-ai-trade-google-token";
export class DashboardApi{
  constructor(token){this.token=token;this.timings={}}
  async _fetch(name,u,options={}){
    const start=performance.now();
    const googleToken=localStorage.getItem(GOOGLE_AUTH_KEY)||"";
    const headers={...(options.headers||{})};
    if(googleToken)headers.Authorization="Bearer "+googleToken;
    const r=await fetch(u,{cache:"no-store",...options,headers});
    this.timings[name]=Math.round(performance.now()-start);
    if(!r.ok)throw new Error(name+" API HTTP "+r.status);
    return r.json();
  }
  getTimings(){return{...this.timings}}
  _url(feature=null){
    const u=new URL(CONFIG.apiBase);
    if(feature)u.searchParams.set("format",feature);
    if(this.token)u.searchParams.set("t",this.token);
    return u;
  }
  async getOverview(){
    return this._fetch("overview",this._url("json"));
  }
  async getFeature(feature,params={}){
    const u=this._url(feature);
    Object.entries(params).forEach(([k,v])=>u.searchParams.set(k,String(v)));
    return this._fetch(feature,u);
  }
  async founderAction(tokenId,action){
    const u=this._url("admin-testers");
    return this._fetch("admin-action",u,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({tokenId,action})});
  }
}
