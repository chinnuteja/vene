import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Bring Vene — your visit, together', description: 'Prepare what matters, keep the conversation clear, and carry next steps forward.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

