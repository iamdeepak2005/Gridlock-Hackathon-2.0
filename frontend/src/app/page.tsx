
"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import TrafficMap from '@/components/dashboard/TrafficMap';
import TrafficCopilot from '@/components/dashboard/TrafficCopilot';
import ImpactDashboard from '@/components/dashboard/ImpactDashboard';
import ResourcePanel from '@/components/dashboard/ResourcePanel';
import MemoryExplorer from '@/components/dashboard/MemoryExplorer';
import DiversionSimulator from '@/components/dashboard/DiversionSimulator';
import { ChevronRight, GripHorizontal, Maximize2, Minimize2, Database, Route, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { DashboardProvider } from '@/context/DashboardContext';

export default function DashboardPage() {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
}

function DashboardContent() {
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState<'memory' | 'simulator'>('memory');
  const [bottomHeight, setBottomHeight] = useState(350); 
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const startResizing = useCallback(() => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e: MouseEvent) => {
    if (isResizing && containerRef.current) {
      const containerHeight = containerRef.current.getBoundingClientRect().height;
      const newHeight = containerHeight - e.clientY;
      if (newHeight > 100 && newHeight < containerHeight * 0.7) {
        setBottomHeight(newHeight);
      }
    }
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [resize, stopResizing]);

  const toggleRightSidebar = (tab: 'memory' | 'simulator') => {
    if (rightSidebarOpen && activeRightTab === tab) {
      setRightSidebarOpen(false);
    } else {
      setActiveRightTab(tab);
      setRightSidebarOpen(true);
    }
  };

  return (
    <div ref={containerRef} className="h-full flex overflow-hidden bg-[#020408]">
      {/* Tactical Sidebar (Left) - AI Copilot */}
      <aside 
        className={cn(
          "border-r border-white/10 bg-[#05070a] transition-all duration-300 ease-in-out shrink-0 relative overflow-hidden z-20",
          leftSidebarOpen ? "w-[320px]" : "w-0"
        )}
      >
        <div className="w-[320px] h-full">
          <TrafficCopilot onToggle={() => setLeftSidebarOpen(false)} />
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Toggle Left Sidebar Button */}
        {!leftSidebarOpen && (
          <button 
            onClick={() => setLeftSidebarOpen(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-[60] bg-primary/20 hover:bg-primary/40 text-primary p-1.5 rounded-r-md border border-l-0 border-primary/30 transition-all shadow-lg"
          >
            <ChevronRight size={18} />
          </button>
        )}

        {/* Top Section: Map */}
        <section className="flex-1 relative overflow-hidden">
          <div className="absolute top-4 right-4 z-40 flex gap-2">
             <Button 
                variant="outline" 
                size="sm" 
                className="bg-black/80 backdrop-blur-xl border-white/20 text-[10px] font-bold uppercase tracking-widest h-8 shadow-2xl hover:bg-primary/10 hover:text-primary"
                onClick={() => setBottomHeight(bottomHeight > 150 ? 100 : 400)}
              >
                {bottomHeight > 150 ? <Maximize2 size={12} className="mr-2"/> : <Minimize2 size={12} className="mr-2"/>}
                {bottomHeight > 150 ? "Focus Map" : "Expand Analytics"}
             </Button>
             
             <div className="flex bg-black/80 backdrop-blur-xl border border-white/20 rounded-md overflow-hidden shadow-2xl">
               <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "text-[10px] font-bold uppercase tracking-widest h-8 rounded-none border-r border-white/10 hover:bg-primary/10 hover:text-primary",
                  rightSidebarOpen && activeRightTab === 'memory' ? "bg-primary/20 text-primary" : "text-white/70"
                )}
                onClick={() => toggleRightSidebar('memory')}
               >
                 <Database size={12} className="mr-2" /> Memory
               </Button>
               <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "text-[10px] font-bold uppercase tracking-widest h-8 rounded-none hover:bg-primary/10 hover:text-primary",
                  rightSidebarOpen && activeRightTab === 'simulator' ? "bg-primary/20 text-primary" : "text-white/70"
                )}
                onClick={() => toggleRightSidebar('simulator')}
               >
                 <Route size={12} className="mr-2" /> Simulator
               </Button>
             </div>
          </div>
          <TrafficMap />
        </section>

        {/* Resize Handle */}
        <div 
          onMouseDown={startResizing}
          className="h-1.5 w-full cursor-row-resize bg-white/5 hover:bg-primary/50 transition-colors flex items-center justify-center group relative z-50 border-y border-white/10"
        >
          <div className="absolute -top-3 bottom-0 left-0 right-0" />
          <GripHorizontal size={14} className="text-white/20 group-hover:text-white transition-colors" />
        </div>

        {/* Bottom Section: Core Analytics Panels (Side-by-Side) */}
        <section 
          style={{ height: `${bottomHeight}px` }}
          className="shrink-0 overflow-hidden bg-[#080b12] shadow-[0_-20px_50px_-15px_rgba(0,0,0,0.8)] z-10"
        >
          <div className="flex h-full w-full">
            <div className="flex-1 border-r border-white/10 overflow-hidden h-full">
              <ImpactDashboard />
            </div>
            <div className="flex-1 overflow-hidden h-full">
              <ResourcePanel />
            </div>
          </div>
        </section>
      </main>

      {/* Right Sidebar - Tactical Memory & Advanced Simulation (Tabbed) */}
      <aside 
        className={cn(
          "border-l border-white/10 bg-[#05070a] transition-all duration-300 ease-in-out shrink-0 relative overflow-hidden z-20 shadow-2xl",
          rightSidebarOpen ? "w-[400px]" : "w-0"
        )}
      >
        <div className="w-[400px] h-full flex flex-col">
          <Tabs 
            value={activeRightTab} 
            onValueChange={(v) => setActiveRightTab(v as 'memory' | 'simulator')} 
            className="flex-1 flex flex-col overflow-hidden"
          >
            <div className="h-16 border-b border-white/5 bg-black/40 flex items-center justify-between px-4 shrink-0">
              <TabsList className="bg-white/5 border border-white/10">
                <TabsTrigger value="memory" className="text-[10px] uppercase font-bold tracking-[0.1em] h-7">Memory</TabsTrigger>
                <TabsTrigger value="simulator" className="text-[10px] uppercase font-bold tracking-[0.1em] h-7">Simulator</TabsTrigger>
              </TabsList>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setRightSidebarOpen(false)} 
                className="text-muted-foreground hover:text-white hover:bg-white/5 h-8 w-8"
              >
                <X size={16} />
              </Button>
            </div>
            
            <TabsContent value="memory" className="flex-1 overflow-hidden m-0 border-none">
              <MemoryExplorer />
            </TabsContent>
            
            <TabsContent value="simulator" className="flex-1 overflow-hidden m-0 border-none">
              <DiversionSimulator />
            </TabsContent>
          </Tabs>
        </div>
      </aside>
    </div>
  );
}
