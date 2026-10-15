'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { request, redeemInvite } from '@/lib/api/client';

export function AccessGate({ ended = false }: { ended?: boolean }) {
  const [development, setDevelopment] = useState(false);
  useEffect(() => { request<{enabled: boolean}>('/dev/fixture').then(x => setDevelopment(x.enabled)).catch(() => {}); }, []);
  return <main className="access-page"><div className="access-card"><span className="brand-mark">v<span /></span><div className="eyebrow">BRING VENE</div><h1>{ended ? 'This visit is no longer open.' : 'Your visit, by invitation.'}</h1><p>{ended ? 'Your session has ended or access was withdrawn. The visit information has been cleared from this window.' : 'Open the invitation Maria shared with you. It gives you access to the parts of this visit she chose to share.'}</p>{development && <Link className="primary-button" href="/dev">Open the fictional preview</Link>}<small>An invitation gives access. It does not approve an action or a clinical decision.</small></div></main>;
}

export function FixtureLauncher() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [cases,setCases]=useState<{id:string;name:string;preferred:string;family:string;description:string}[]>([]);
  const [selected,setSelected]=useState('maria'),[tools,setTools]=useState(false);
  useEffect(()=>{request<typeof cases>('/dev/cases').then(setCases).catch(()=>{});},[]);
  useEffect(() => { request<{enabled:boolean}>('/dev/fixture').then(x => setEnabled(x.enabled)).catch(() => setEnabled(false)); }, []);
  async function launch(persona: 'patient' | 'clinician' | 'family') {
    setBusy(true); setError('');
    try {
      sessionStorage.setItem('vene-demo-tools',String(tools));
      const invite = await request<{token: string}>('/dev/invitations', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ persona,case:selected }) });
      await redeemInvite(invite.token); window.location.replace('/prepare');
    } catch (e) { setError((e as Error).message); setBusy(false); }
  }
  return <main className="access-page"><div className="access-card"><div className="eyebrow">LOCAL · FICTIONAL VISIT</div><h1>See care from each side.</h1><p>Each person has a separate invitation and only sees what the patient permits. Use separate browser profiles to see them together.</p><label className="demo-case-label">Fictional encounter<select aria-label="Fictional encounter" value={selected} onChange={e=>setSelected(e.target.value)}>{cases.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><p className="muted">{cases.find(c=>c.id===selected)?.description}</p><label className="demo-tools-choice"><input type="checkbox" checked={tools} onChange={e=>setTools(e.target.checked)}/>Show fictional scenario controls (developer)</label>{enabled === null ? <p>Checking preview access…</p> : enabled ? <div className="persona-list">{([['patient','Maria','Choose questions and what to share.'],['clinician','Dr. Chen','See the context approved for you.'],['family','Elena','Suggest a question and see shared updates.']] as const).map(([role, name, detail]) => <button disabled={busy} key={role} onClick={() => launch(role)}><strong>Continue as {role==='patient'?(cases.find(c=>c.id===selected)?.preferred??name):role==='family'?(cases.find(c=>c.id===selected)?.family.split(' ')[0]??name):name}</strong><span>{detail}</span></button>)}</div> : <p>This preview launcher is unavailable.</p>}{error && <p role="alert">{error}</p>}<small>Fictional data only. This launcher is enabled explicitly by the local development server.</small></div></main>;
}

export function JoinInvitation() {
  const [error, setError] = useState('');
  const consumed = useRef(false);
  useEffect(() => {
    if (consumed.current) return;
    consumed.current = true;
    const token = new URLSearchParams(window.location.hash.slice(1)).get('invite');
    window.history.replaceState(null, '', '/join');
    if (!token) { setError('This invitation is missing. Open the complete link Maria shared.'); return; }
    redeemInvite(token).then(() => window.location.replace('/prepare')).catch(() => setError('This invitation has expired, was already used, or was withdrawn. Ask for a new invitation.'));
  }, []);
  return <main className="access-page"><div className="access-card"><div className="eyebrow">BRING VENE</div><h1>{error ? 'A new invitation is needed.' : 'Opening your visit…'}</h1>{error && <p role="alert">{error}</p>}</div></main>;
}
