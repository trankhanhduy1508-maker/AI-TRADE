export class DashboardStore{
  constructor(){this.state={overview:null,trades:[],journal:[],arena:null,candles:[],symbolSpecs:{},selectedSymbol:"EURUSD",selectedTimeframe:"1h",chartOpened:false};this.listeners=new Set()}
  get(){return this.state}
  set(patch){this.state={...this.state,...patch};for(const fn of this.listeners)fn(this.state)}
  subscribe(fn){this.listeners.add(fn);return()=>this.listeners.delete(fn)}
}
