import http from 'node:http';
import {Readable} from 'node:stream';
export type SessionJar={name:string;path:string};

export async function proxyRequest(request:Request,path:string[],jar?:SessionJar){
  if(request.method!=='GET'&&request.method!=='HEAD'){
    const origin=request.headers.get('origin'),browserOrigin=new URL(request.url);
    browserOrigin.host=request.headers.get('host')??browserOrigin.host;
    if((origin&&origin!==browserOrigin.origin)||request.headers.get('sec-fetch-site')==='cross-site')
      return Response.json({detail:'This origin is not allowed.'},{status:403});
  }
  const base=new URL(process.env.BACKEND_URL??'http://127.0.0.1:8000');
  if(base.protocol!=='http:'||!['127.0.0.1','localhost'].includes(base.hostname))
    return Response.json({detail:'The visit service is not configured.'},{status:503});
  const target=new URL('/'+path.map(encodeURIComponent).join('/'),base);
  target.search=new URL(request.url).search;
  const headers=new Headers();
  for(const name of ['content-type','origin','x-vene-intent','x-vene-csrf']){
    const value=request.headers.get(name);if(value)headers.set(name,value);
  }
  const cookies=request.headers.get('cookie')??'';
  if(jar){
    const selected=cookies.split(';').map(c=>c.trim()).find(c=>c.startsWith(jar.name+'='));
    if(selected)headers.set('cookie','vene_session='+selected.slice(jar.name.length+1));
    // Never fall back to the normal visit cookie or another pane's credentials.
  }else if(cookies)headers.set('cookie',cookies);
  const controller=new AbortController(),signal=AbortSignal.any([request.signal,controller.signal]);
  const deadline=setTimeout(()=>controller.abort(),15000);
  try{
    const body=['GET','HEAD'].includes(request.method)?undefined:await request.text();
    const upstream=await new Promise<http.IncomingMessage>((resolve,reject)=>{
      const outgoing=http.request(target,{method:request.method,headers:Object.fromEntries(headers),agent:false,signal},resolve);
      outgoing.once('error',reject);outgoing.end(body);
    });
    const responseHeaders=new Headers({'Cache-Control':'no-store','X-Accel-Buffering':'no','X-Content-Type-Options':'nosniff'});
    const contentType=String(upstream.headers['content-type']??'application/json');
    responseHeaders.set('Content-Type',contentType);
    for(const cookie of upstream.headers['set-cookie']??[]){
      if(jar&&cookie.startsWith('vene_session='))responseHeaders.append('Set-Cookie',cookie.replace(/^vene_session=/,jar.name+'=').replace(/;\s*Path=\/($|;)/i,'; Path='+jar.path+'$1'));
      else if(!jar)responseHeaders.append('Set-Cookie',cookie);
    }
    if(contentType.startsWith('text/event-stream')){
      clearTimeout(deadline);
      return new Response(Readable.toWeb(upstream) as ReadableStream<Uint8Array>,{status:upstream.statusCode??502,headers:responseHeaders});
    }
    const chunks:Buffer[]=[];for await(const chunk of upstream)chunks.push(Buffer.from(chunk));
    return new Response(new Uint8Array(Buffer.concat(chunks)),{status:upstream.statusCode??502,headers:responseHeaders});
  }catch{return Response.json({detail:'The visit service is temporarily unavailable.'},{status:503});}
  finally{clearTimeout(deadline);}
}
