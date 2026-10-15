type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, context: RouteContext) {
  const { path } = await context.params;
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const origin = request.headers.get('origin');
    // Next's internal URL can use localhost while the browser uses 127.0.0.1.
    const browserOrigin = new URL(request.url);
    browserOrigin.host = request.headers.get('host') ?? browserOrigin.host;
    if ((origin && origin !== browserOrigin.origin) || request.headers.get('sec-fetch-site') === 'cross-site') {
      return Response.json({ detail: 'This origin is not allowed.' }, { status: 403 });
    }
  }
  const base = new URL(process.env.BACKEND_URL ?? 'http://127.0.0.1:8000');
  if (base.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(base.hostname)) {
    return Response.json({ detail: 'The local visit service is not configured.' }, { status: 503 });
  }
  const target = new URL('/' + path.map(encodeURIComponent).join('/'), base);
  target.search = new URL(request.url).search;
  const headers = new Headers();
  for (const name of ['content-type', 'cookie', 'origin', 'x-vene-intent', 'x-vene-csrf']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const controller = new AbortController();
  const signal = AbortSignal.any([request.signal, controller.signal]);
  const deadline = setTimeout(() => controller.abort(), 15000);
  try {
    const body = request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text();
    // The loopback API can restart independently. Own a fresh connection rather
    // than reuse a framework fetch connection across that service lifetime.
    const upstream = await new Promise<http.IncomingMessage>((resolve, reject) => {
      const outgoing = http.request(target, {method:request.method, headers:Object.fromEntries(headers), agent:false, signal}, resolve);
      outgoing.once('error', reject);
      outgoing.end(body);
    });
    const responseHeaders = new Headers({ 'Cache-Control': 'no-store' });
    responseHeaders.set('X-Accel-Buffering', 'no');
    responseHeaders.set('X-Content-Type-Options', 'nosniff');
    const contentType = String(upstream.headers['content-type'] ?? 'application/json');
    responseHeaders.set('Content-Type', contentType);
    for (const cookie of upstream.headers['set-cookie'] ?? []) responseHeaders.append('Set-Cookie', cookie);
    if (contentType.startsWith('text/event-stream')) {
      clearTimeout(deadline);
      // Canceling the response destroys its owned incoming stream/socket.
      const stream = Readable.toWeb(upstream) as ReadableStream<Uint8Array>;
      return new Response(stream, {status:upstream.statusCode ?? 502, headers:responseHeaders});
    }
    // Read ordinary JSON before returning so a reset during the body becomes
    // an explicit unavailable response, not a truncated response to the client.
    const chunks:Buffer[]=[];
    for await (const chunk of upstream) chunks.push(Buffer.from(chunk));
    return new Response(new Uint8Array(Buffer.concat(chunks)), {status:upstream.statusCode ?? 502, headers:responseHeaders});
  } catch {
    return Response.json({ detail: 'The visit service is temporarily unavailable.' }, { status: 503 });
  } finally { clearTimeout(deadline); }
}

export const GET = proxy;
export const POST = proxy;
export const dynamic = 'force-dynamic';
import http from 'node:http';
import {Readable} from 'node:stream';

export const runtime = 'nodejs';
