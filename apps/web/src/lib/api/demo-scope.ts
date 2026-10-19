// Each iframe has its own JS realm and a distinct HttpOnly, path-scoped session.
// Role text in a URL only selects a cookie jar. The backend still authenticates the cookie.
export function apiBase(){
  if(typeof window==='undefined')return '/api';
  const match=/^\/demo\/pane\/([a-f0-9-]{36})\/(patient|clinician|family)$/.exec(window.location.pathname);
  return match?'/api/demo/'+match[1]+'/'+match[2]:'/api';
}
