import type {Metadata} from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Trinetra Intelligence | Traffic AI Command Center',
  description: 'Event-Driven Traffic Intelligence System for Modern Smart Cities',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body antialiased bg-background text-foreground overflow-hidden h-screen flex flex-col">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 shrink-0 bg-background/50 backdrop-blur-md z-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center glow-blue">
              <span className="font-headline font-bold text-white text-lg">T</span>
            </div>
            <h1 className="font-headline text-xl font-bold tracking-tight uppercase">Trinetra <span className="text-primary">Intelligence</span></h1>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">System Status</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-mono">OP_CENTRAL_ACTIVE</span>
              </div>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div className="flex gap-2">
              <button className="h-9 px-4 rounded-md bg-secondary text-xs font-bold hover:bg-secondary/80 transition-colors">LOGIN</button>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}