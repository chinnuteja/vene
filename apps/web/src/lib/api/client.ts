import type { components } from '../../../../../packages/contracts/schema';
export type Encounter = Omit<components['schemas']['EncounterView'], 'suggestions'> & { suggestions: NonNullable<components['schemas']['EncounterView']['suggestions']> };
export type Evidence = components['schemas']['Evidence'];
export type Command = components['schemas']['CommandEnvelope'];
export type Identity = components['schemas']['Identity'];
export type Member = components['schemas']['MemberView'];
let csrf = '';
export class AccessError extends Error {}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.method && init.method !== 'GET') {
    headers.set('x-vene-intent', 'mutation');
    if (csrf) headers.set('x-vene-csrf', csrf);
  }
  let response: Response;
  try { response = await fetch('/api' + path, { ...init, headers, cache: 'no-store' }); }
  catch { throw new Error("We couldn't connect to your visit. Please try again in a moment."); }
  if (!response.ok) {
    if (response.status === 401) { csrf = ''; throw new AccessError('Your session has ended or access has been withdrawn.'); }
    if (response.status === 409) {
      const body = await response.json().catch(() => null);
      const guidance = new Set([
        'Share a next step and its sources with everyone present before requesting a closeout.',
        'Share the question or step and its sources with everyone present first.',
        'Everyone present must agree to this speaking mode.',
        'Ask after the reservation is confirmed, and share this step and its sources with this person first.',
        'These steps changed. Review them again.',
      ]);
      throw new Error(guidance.has(body?.detail) ? body.detail : 'Your visit changed in another window. Refresh and try again.');
    }
    if (response.status === 403) throw new Error('You do not have permission to make this change.');
    throw new Error(init?.method&&init.method!=='GET'?"We couldn't confirm the result. Refresh your visit before trying again.":"We couldn't reach your visit. Please try again in a moment.");
  }
  return response.json() as Promise<T>;
}
export async function loadVisit(signal: AbortSignal) {
  const viewer = await request<Identity>('/auth/me', { signal });
  csrf = viewer.csrf_token;
  const list = await request<components['schemas']['EncounterSummary'][]>('/encounters', { signal });
  if (!list.length) throw new Error('No visit is available yet.');
  const [visit, health] = await Promise.all([
    request<Encounter>('/encounters/' + list[0].id, { signal }),
    request<components['schemas']['Health']>('/health/ready', { signal }),
  ]);
  return { visit, viewer, ready: health.status === 'ready' };
}
export async function redeemInvite(token: string) {
  const viewer = await request<Identity>('/auth/redeem', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) });
  csrf = viewer.csrf_token;
  return viewer;
}
export async function logoutSession() {
  const viewer = await request<Identity>('/auth/me');
  csrf = viewer.csrf_token;
  await request('/auth/logout', { method: 'POST' });
  csrf = '';
}
export async function sendCommand(visit: Encounter, command: Command['command']) {
  const result = await request<components['schemas']['CommandResult']>('/encounters/' + visit.id + '/commands',
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command_id: crypto.randomUUID(), expected_version: visit.version, evidence_refs: [], command }) });
  return result.encounter as Encounter;
}
export async function choosePriority(visit: Encounter, priorityId: string, selected: boolean) {
  return sendCommand(visit, { type: 'priority.selection_changed', priority_id: priorityId, selected });
}

