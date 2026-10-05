/** Native PNG icon renderer used by CWS AI Trade PWA. Reproducible source; no binary image provider or CDN dependency. */
function put32(target:Uint8Array,at:number,n:number) {
 target[at]=(n>>>24)&255;target[at+1]=(n>>>16)&255;target[at+2]=(n>>>8)&255;target[at+3]=n&255;
}
function crc32(bytes:Uint8Array) {
 let crc=0xffffffff;
 for(const b of bytes){
  crc ^= b;
  for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);
 }
 return (crc^0xffffffff)>>>0;
}
function chunk(label:string,data:Uint8Array){
 const bytes=new Uint8Array(12+data.length),name=new TextEncoder().encode(label);
 put32(bytes,0,data.length);bytes.set(name,4);bytes.set(data,8);
 const crcInput=new Uint8Array(4+data.length);crcInput.set(name,0);crcInput.set(data,4);
 put32(bytes,8+data.length,crc32(crcInput));
 return bytes;
}
function nearSegment(x:number,y:number,ax:number,ay:number,bx:number,by:number){
 const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)));
 return Math.hypot(x-ax-t*dx,y-ay-t*dy);
}
export async function generatePngIcon(size:number):Promise<Uint8Array> {
 if(size!==192&&size!==512)throw new Error("Unsupported icon size");
 const scan=new Uint8Array(size*(1+size*4));
 const corners=0.17;
 for(let y=0;y<size;y++){
  const start=y*(1+size*4);
  scan[start]=0; // PNG scanline filter: None
  for(let x=0;x<size;x++){
   const u=(x+0.5)/size,v=(y+0.5)/size,off=start+1+x*4;
   // Dark brand background.
   let r=8,g=19,b=32;
   const dx=Math.max(Math.abs(u-0.5)-(0.5-corners),0);
   const dy=Math.max(Math.abs(v-0.5)-(0.5-corners),0);
   const within=Math.hypot(dx,dy)<=corners-0.03;
   if(within){r=16;g=45;b=66;}
   const border=Math.hypot(dx,dy)>=corners-0.048&&within;
   if(border){r=38;g=105;b=148;}
   // Cyan CWS diamond.
   const diamond=Math.abs(u-0.34)+Math.abs(v-0.28);
   if(diamond<0.135){r=45;g=155;b=242;}
   if(u>0.34&&diamond<0.135){r=24;g=111;b=215;}
   // Green ascending trade trend.
   const points=[[0.19,0.68],[0.37,0.52],[0.49,0.58],[0.73,0.32],[0.80,0.37]];
   for(let i=0;i<points.length-1;i++){
    if(nearSegment(u,v,points[i][0],points[i][1],points[i+1][0],points[i+1][1])<0.019){r=41;g=217;b=163;break;}
   }
   scan[off]=r;scan[off+1]=g;scan[off+2]=b;scan[off+3]=255;
  }
 }
 const compressed=new Uint8Array(await new Response(new Blob([scan]).stream().pipeThrough(new CompressionStream("deflate"))).arrayBuffer());
 const header=new Uint8Array(13);
 put32(header,0,size);put32(header,4,size);header[8]=8;header[9]=6;header[10]=0;header[11]=0;header[12]=0;
 const signature=new Uint8Array([137,80,78,71,13,10,26,10]);
 const chunks=[chunk("IHDR",header),chunk("IDAT",compressed),chunk("IEND",new Uint8Array())];
 const length=signature.length+chunks.reduce((n,p)=>n+p.length,0);
 const result=new Uint8Array(length);result.set(signature);
 let offset=signature.length;
 for(const part of chunks){result.set(part,offset);offset+=part.length;}
 return result;
}
