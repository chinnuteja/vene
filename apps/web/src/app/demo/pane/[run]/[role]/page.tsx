import {notFound} from 'next/navigation';
import {DemoPane} from '@/components/demo-pane';
export default async function Page({params}:{params:Promise<{run:string;role:string}>}){
  const {run,role}=await params;
  if(!/^[a-f0-9-]{36}$/.test(run)||!['patient','clinician','family'].includes(role))notFound();
  return <DemoPane run={run} role={role as 'patient'|'clinician'|'family'}/>;
}
