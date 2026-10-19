import {proxyRequest} from '@/lib/api/proxy';
type Context={params:Promise<{path:string[]}>};
async function proxy(request:Request,context:Context){return proxyRequest(request,(await context.params).path);}
export const GET=proxy;
export const POST=proxy;
export const dynamic='force-dynamic';
export const runtime='nodejs';
