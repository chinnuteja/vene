'use client';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, CalendarDays, Check, ChevronRight, CircleHelp, FileText, Heart, Leaf, LoaderCircle, MessageCircle, RefreshCw, ShieldCheck, Sparkles, X } from 'lucide-react';
import { AccessError, choosePriority, loadVisit, logoutSession, request, sendCommand, type Command, type Encounter, type Evidence, type Identity } from '@/lib/api/client';
import { AccessGate } from './access-gate';
import { AudienceChoices, GuestPreparation, PreparationControls, QuestionEditor } from './preparation-controls';
import dynamic from 'next/dynamic';
import {UnderstandingPanel,EvolvingVisitCard,ConversationSourceCorrection} from './understanding-panel';
import {ExecutionPanel} from './execution-panel';
import {ContinuityPanel} from './continuity-panel';
import {InRoomChecks} from './in-room-checks';
import {DraftedAgenda} from './drafted-agenda';
const CallPanel=dynamic(()=>import('./call-panel').then(m=>m.CallPanel),{ssr:false});

type Stage = 'prepare' | 'visit' | 'follow-up';
const stages = [
  { id: 'prepare', label: 'Prepare', href: '/prepare' },
  { id: 'visit', label: 'Your visit', href: '/visit' },
  { id: 'follow-up', label: 'Next steps', href: '/follow-up' },
] as const;
const headings = {
  prepare: { eyebrow: 'BEFORE YOUR VISIT', title: "Let's make room for what matters.", description: 'A little preparation, so your questions come with you.' },
  visit: { eyebrow: 'YOUR VISIT, TOGETHER', title: 'Keep the important things in view.', description: 'Your questions, what you understand, and what still needs an answer.' },
  'follow-up': { eyebrow: 'AFTER THE CONVERSATION', title: 'A clear way forward.', description: 'Keep track of the next step, and what it is waiting on.' },
};
function date(value: string, options: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', ...options }).format(new Date(value));
}

export function VisitWorkspace({ stage }: { stage: Stage }) {
  const [visit, setVisit] = useState<Encounter | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [source, setSource] = useState<Evidence | null>(null);
  const [viewer, setViewer] = useState<Identity | null>(null);
  const [accessNeeded, setAccessNeeded] = useState(false);
  const [ended, setEnded] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const sourceTrigger = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    loadVisit(controller.signal).then(result => {
      setVisit(result.visit); setViewer(result.viewer); setAccessNeeded(false); setReady(result.ready); setError('');
    }).catch(e => { if (!controller.signal.aborted) { setReady(false); if (e instanceof AccessError) { setVisit(null); setViewer(null); setSource(null); setAccessNeeded(true); } else setError(e.message); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [refresh]);
  useEffect(() => {
    if (!visit?.id || !viewer) return;
    const stream = new EventSource('/api/encounters/' + visit.id + '/stream');
    function update(event: MessageEvent) {
      const incoming: Encounter = JSON.parse(event.data);
      setVisit(current => !current || (incoming.version > current.version || (incoming.version === current.version && incoming.consent_epoch > current.consent_epoch)) ? incoming : current);
      setReady(true);
    }
    function clear() { stream.close(); setVisit(null); setSource(null); setViewer(null); setReady(false); setAccessNeeded(true); setEnded(true); }
    stream.addEventListener('snapshot', update as EventListener);
    stream.addEventListener('update', update as EventListener);
    stream.addEventListener('access_revoked', clear);
    stream.addEventListener('unavailable', () => { stream.close(); setVisit(null); setSource(null); setReady(false); setError('Live updates are unavailable. Refresh to reconnect.'); });
    stream.onerror = () => { stream.close(); setVisit(null); setSource(null); setReady(false); request<Identity>('/auth/me').catch(e => { if (e instanceof AccessError) clear(); }).finally(() => setError('The live connection ended. Refresh to reconnect.')); };
    return () => stream.close();
  }, [visit?.id, viewer?.membership_id, refresh]);
  useEffect(() => {
    if (!source) { dialog.current?.close(); return; }
    const current = visit?.evidence.find(e => e.id === source.id);
    if (!current) { dialog.current?.close(); setSource(null); }
    else if (JSON.stringify(current) !== JSON.stringify(source)) setSource(current);
  }, [visit, source]);
  useEffect(() => { if (source && dialog.current && !dialog.current.open) dialog.current.showModal(); }, [source]);
  async function toggle(id: string, selected: boolean) {
    if (!visit || saving) return;
    const previous = visit;
    setSaving(id);
    setVisit({ ...visit, priorities: visit.priorities.map(p => p.id === id ? { ...p, selected } : p) });
    try { setVisit(await choosePriority(previous, id, selected)); setError(''); }
    catch (e) { setVisit(previous); setError((e as Error).message); }
    finally { setSaving(null); }
  }
  async function mutate(command: Command['command']) {
    if (!visit || saving) return false;
    setSaving('controls');
    try { setVisit(await sendCommand(visit, command)); setError(''); return true; }
    catch (e) { if (e instanceof AccessError) { setAccessNeeded(true); setEnded(true); setVisit(null); setSource(null); setViewer(null); } else setError((e as Error).message); return false; }
    finally { setSaving(null); }
  }
  function openSource(item: Evidence, trigger: HTMLElement) { sourceTrigger.current = trigger; setSource(item); }
  function closeSource() { dialog.current?.close(); setSource(null); sourceTrigger.current?.focus(); }
  async function leave() {
    try { await logoutSession(); }
    catch (e) { if (!(e instanceof AccessError)) { setError((e as Error).message); return; } }
    setVisit(null); setViewer(null); setSource(null); setAccessNeeded(true); setEnded(true);
  }
  const selected = visit?.priorities.filter(p => p.selected) ?? [];
  const text = headings[stage];
  const stageIndex = stages.findIndex(s => s.id === stage);
  const patient = viewer?.role === 'patient';
  if (accessNeeded) return <AccessGate ended={ended} />;
  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <aside className="sidebar">
      <Link href="/prepare" className="brand" aria-label="Bring Vene home"><span className="brand-mark">v<span /></span><span>vene<span className="brand-sub">WITH YOU, THROUGH CARE</span></span></Link>
      <div className="sidebar-label">YOUR SPACE</div>
      <nav aria-label="Visit sections" className="side-nav">{stages.map((s, i) => <Link href={s.href} key={s.id} aria-current={stage === s.id ? 'page' : undefined} className={stage === s.id ? 'active' : ''}>
        {i === 0 ? <Leaf size={19} /> : i === 1 ? <MessageCircle size={19} /> : <Check size={19} />}<span>{s.label}</span>{stage === s.id && <ChevronRight size={16} />}
      </Link>)}</nav>
      <div className="sidebar-note"><Heart size={20} /><p>A little less to carry.<br /><strong>One step at a time.</strong></p></div>
      <div className="profile"><div className="avatar">{viewer?.name.split(' ').map(n => n[0]).slice(0,2).join('') ?? 'V'}</div><div><strong>{viewer?.name ?? 'Your visit'}</strong><span>{patient ? 'Your care companion' : viewer?.role === 'family' ? 'Family view' : 'Clinician view'}</span></div></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span className="breadcrumb">Bring Vene <ChevronRight size={14} /> {stages[stageIndex].label}</span><span className="connection" role="status"><i className={ready ? 'online' : ''} />{loading ? 'Connecting' : ready ? 'Visit saved' : 'Connection unavailable'}</span></header>
      <main id="main" className="main">
        <div className="mobile-brand"><span className="brand-mark">v<span /></span><strong>vene</strong><span>Bring Vene</span></div>
        <nav className="steps" aria-label="Visit progress">{stages.map((s, i) => <Link key={s.id} href={s.href} aria-current={stage === s.id ? 'step' : undefined} className={stage === s.id ? 'current' : ''}><span>{i + 1}</span>{s.label}</Link>)}</nav>
        <section className="hero"><div><div className="eyebrow">{text.eyebrow}</div><h1>{text.title}</h1><p>{text.description}</p></div><div className="hero-flower" aria-hidden="true"><span className="petal p1" /><span className="petal p2" /><span className="petal p3" /><span className="petal p4" /><span className="flower-center"><Sparkles size={27} /></span><i className="orbit" /></div></section>
        {viewer && <div className="viewer-strip"><span>{patient ? 'Your private space' : `${viewer.role === 'family' ? 'Family' : 'Clinician'} view · Shared by ${visit?.patient.preferred_name ?? 'the patient'}`}</span><button className="source-link" onClick={() => void leave()}>Leave this session</button></div>}
        {error && <div className="error-banner" role="alert" aria-label="Visit error"><CircleHelp size={20} /><div><strong>We couldn't update your visit.</strong><p>{error}</p></div><button onClick={() => setRefresh(r => r + 1)}><RefreshCw size={16} />Try again</button></div>}
        {loading && !visit ? <div className="loading" role="status"><LoaderCircle size={24} className="spin" /><p>Getting your visit ready…</p></div> : visit ? <>
          <div className="visit-strip"><div className="calendar-icon"><CalendarDays size={22} /></div><div><strong>{visit.title}</strong><span>{date(visit.visit_at, { weekday: 'long', month: 'short', day: 'numeric' })} · {date(visit.visit_at, { hour: 'numeric', minute: '2-digit' })} ET</span></div><span className="pill">Upcoming visit</span></div>
          {stage==='visit'&&viewer&&<CallPanel visit={visit} viewer={viewer}/>}
          {stage==='visit'&&patient&&<UnderstandingPanel visit={visit} onReplace={setVisit}/>}
          {stage === 'prepare' && patient && <DraftedAgenda visit={visit}/>}
          {stage === 'prepare' && !patient ? <GuestPreparation visit={visit} mutate={mutate} disabled={saving !== null} onSource={openSource} /> : stage === 'prepare' ? <div className="content-grid">
            <section className="card priorities"><div className="section-heading"><div><div className="eyebrow small">START WITH YOU</div><h2>What would you like to discuss?</h2></div><span className="count-pill">{selected.length} on your list</span></div><p className="muted intro">Choose what matters today. You can change your list.</p>
              <div className="priority-list">{visit.priorities.map((p, i) => <div key={p.id} className={'priority-card ' + (p.selected ? 'selected' : '')}>
                <label className="priority-choice"><input type="checkbox" checked={p.selected} disabled={saving !== null} onChange={e => toggle(p.id, e.target.checked)} aria-label={p.title} /><span className="checkbox" aria-hidden="true">{saving === p.id ? <LoaderCircle size={14} className="spin" /> : p.selected ? <Check size={14} /> : null}</span><span><span className="priority-number">QUESTION 0{i + 1}</span><strong>{p.title}</strong><span className="priority-detail">{p.detail}</span></span></label>
                <div className="priority-bottom"><span>{p.selected ? 'On your visit list' : 'Optional for today'}</span>{p.evidence_refs[0] && <button className="source-link" onClick={e => { const ev = visit.evidence.find(x => x.id === p.evidence_refs[0]); if (ev) openSource(ev, e.currentTarget); }}><FileText size={13} />View source</button>}</div>
                <div className="question-controls"><AudienceChoices item={p} label={'question: ' + p.title} mutate={mutate} disabled={saving !== null} /><QuestionEditor item={p} mutate={mutate} disabled={saving !== null} /></div>
              </div>)}</div>
              <div className="card-foot"><ShieldCheck size={17} /><span>Choosing a question adds it to your list. It does not send a message.</span></div>
            </section>
            <aside className="right-column"><section className="companion-card"><div className="companion-icon"><Sparkles size={24} /></div><h2>Your questions,<br />{' '}coming with you.</h2><p>You don't have to hold everything in your head. Your list will stay here throughout the visit.</p><Link className="primary-button" href="/visit">Review your visit <ArrowRight size={17} /></Link></section><section className="card compact"><h3>A little context</h3><div className="context-row"><span>Prepared for</span><strong>{visit.patient.name}</strong></div><div className="context-row"><span>Conversation with</span><strong>{visit.clinician}</strong></div><div className="context-row"><span>Questions selected</span><strong>{selected.length}</strong></div></section></aside>
          </div> : stage === 'visit' ? <EvolvingVisitCard visit={visit} patient={patient} onSource={openSource} onReplace={setVisit} sharing={mutate} disabled={saving!==null}/> : <div className="content-grid">
            <section className="card follow-card"><div className="section-heading"><div><div className="eyebrow small">KEEPING THINGS CLEAR</div><h2>Still to be resolved</h2></div><span className="pill amber">{visit.plan.length} open {visit.plan.length===1?'item':'items'}</span></div>{visit.plan.map(item => <div className="follow-item" key={item.id}><div className="timeline-dot" /><div><h3>{item.title}</h3><p>{item.detail}</p><div className="detail-tags"><span>Owner: {item.owner||'not yet clarified'}</span><span>When: {item.timeframe||'not yet clarified'}</span>{item.location&&<span>Where: {item.location}</span>}<span>External completion: {item.external_completed?'reported complete':'unconfirmed'}</span></div></div></div>)}<div className="soft-note"><ShieldCheck size={20} /><p>Discussing a next step doesn't mean it's done. Any action will need the right confirmation and your approval.</p></div></section>
            <aside className="right-column"><section className="card compact"><h3>Nothing for you to relay yet.</h3><p className="muted">An update for family can be prepared once the next steps are clear and you choose what to share.</p><Link className="text-link" href="/visit">Back to your visit <ArrowRight size={15} /></Link></section><div className="gentle-note"><Leaf size={18} /><p>Care moves forward<br />one clear step at a time.</p></div></aside>
          </div>}
          {stage === 'prepare' && patient && <PreparationControls visit={visit} mutate={mutate} disabled={saving !== null} onSource={openSource} onReplace={setVisit} />}
          {stage === 'prepare' && patient && viewer && <InRoomChecks visit={visit} viewer={viewer} mode="permission"/>}
          {stage !== 'prepare' && viewer && <InRoomChecks visit={visit} viewer={viewer} mode="checks"/>}
          {stage !== 'prepare' && viewer && <ExecutionPanel visit={visit} viewer={viewer}/>}
          {stage === 'follow-up' && viewer && <ContinuityPanel visit={visit} viewer={viewer} onReplace={setVisit} sharing={mutate}/>}
          <div className="save-note" aria-live="polite">{saving ? 'Saving your list…' : error ? 'Please refresh before making another change.' : 'Your visit list is saved.'}</div>
        </> : null}
        <footer className="footer"><span><ShieldCheck size={14} />Your visit, at your pace.</span><span>Local preview · Fictional patient</span></footer>
      </main>
    </div>
    <dialog ref={dialog} className="source-dialog" aria-labelledby="source-title" onCancel={e => { e.preventDefault(); closeSource(); }} onClick={e => { if (e.target === e.currentTarget) closeSource(); }}>
      {source && <div><div className="dialog-heading"><span className="eyebrow small">WHERE THIS CAME FROM</span><button aria-label="Close source" onClick={closeSource}><X size={20} /></button></div><h2 id="source-title">{source.title}</h2><span className="source-type">{source.source_type === 'patient_report' ? 'Reported by you' : source.source_type === 'office_message' ? 'Office message' : source.source_type === 'conversation' ? `Conversation · v${source.version??1}${source.origin==='fixture'?' · fictional turn':''}` : 'Imported record'} · {date(source.observed_at, { month: 'short', day: 'numeric', year: 'numeric' })}</span><blockquote>{source.text}</blockquote><p className="muted">This source describes what was reported at that time.</p>{visit&&patient&&source.source_type==='conversation'&&<><ConversationSourceCorrection visit={visit} source={source} onReplace={setVisit}/><AudienceChoices item={source} label={'source: '+source.title} mutate={mutate} disabled={saving!==null}/></>}</div>}
    </dialog>
  </div>;
}

