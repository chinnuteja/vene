import {proxyRequest} from '@/lib/api/proxy';
type Context={params:Promise<{run:string;role:string;path:string[]}>};
async function proxy(request:Request,context:Context){
  const {run,role,path}=await context.params;
  if(!/^[a-f0-9-]{36}$/.test(run)||!['patient','clinician','family'].includes(role)||path[0]==='dev')
    return Response.json({detail:'Not found.'},{status:404});
  return proxyRequest(request,path,{name:'vene_demo_'+run.replaceAll('-','')+'_'+role,path:'/api/demo/'+run+'/'+role});
}
export const GET=proxy;
export const POST=proxy;
export const dynamic='force-dynamic';
export const runtime='nodejs';
