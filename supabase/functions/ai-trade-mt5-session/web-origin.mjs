const ORIGINS=new Set(['https://cws-autotrade-lab.trankhanhduy1508.chatgpt.site']);
export function corsHeaders(origin){
 if(!ORIGINS.has(origin))return null;
 return {'access-control-allow-origin':origin,'vary':'Origin',
  'access-control-allow-methods':'GET, POST, OPTIONS',
  'access-control-allow-headers':'authorization, content-type, x-cws-client, x-cws-client-version',
  'access-control-max-age':'600'};
}
