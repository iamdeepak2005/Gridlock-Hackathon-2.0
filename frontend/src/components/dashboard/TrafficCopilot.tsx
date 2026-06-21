
"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Terminal, ChevronLeft } from "lucide-react";
import { trinetraApi } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/context/DashboardContext";

interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface TrafficCopilotProps {
  onToggle?: () => void;
}

export default function TrafficCopilot({ onToggle }: TrafficCopilotProps) {
  const { submitNewIncident } = useDashboard();
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: 'TRINETRA AI initialized. Strategic uplink established. Waiting for operator input.', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    const queryInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const copilotResponse = await trinetraApi.copilotQuery({ query: queryInput });
      const response = copilotResponse.response;
      
      let cleanResponse = response;
      const jsonMarker = "[EVENT_JSON] ";
      const markerIndex = response.indexOf(jsonMarker);
      
      if (markerIndex !== -1) {
        cleanResponse = response.substring(0, markerIndex).trim();
        const jsonStr = response.substring(markerIndex + jsonMarker.length).trim();
        try {
          const eventData = JSON.parse(jsonStr);
          await submitNewIncident(eventData);
        } catch (jsonErr) {
          console.error("Failed to parse event JSON from AI", jsonErr);
        }
      }

      setMessages(prev => [...prev, { role: 'ai', content: cleanResponse, timestamp: new Date() }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: 'PROTOCOL_FAILURE: Secure uplink timed out. Re-establish connection.', timestamp: new Date() }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#05070a]">
      {/* Header */}
      <div className="h-16 border-b border-white/5 flex items-center justify-between px-4 bg-black/40 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center border border-primary/30">
            <Terminal size={14} className="text-primary" />
          </div>
          <div>
            <h3 className="font-headline font-bold text-xs tracking-widest uppercase text-white">Copilot</h3>
            <span className="text-[8px] text-primary font-black tracking-[0.2em] uppercase">Tactical_v2</span>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={onToggle} className="text-muted-foreground hover:text-white h-8 w-8 hover:bg-white/5">
           <ChevronLeft size={16} />
        </Button>
      </div>

      {/* Chat History */}
      <ScrollArea className="flex-1 px-4 py-6 bg-[radial-gradient(circle_at_top_left,rgba(0,145,255,0.03),transparent)]">
        <div className="flex flex-col gap-8">
          {messages.map((msg, i) => (
            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className="flex items-center gap-2 mb-2 px-1 opacity-60">
                <span className="text-[9px] uppercase font-black tracking-[0.1em] text-white/80">
                  {msg.role === 'user' ? 'Operator' : 'AI_SYSTEM'}
                </span>
                <span className="text-[8px] font-mono text-muted-foreground">{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <div className={`max-w-[90%] p-4 rounded-xl text-[12px] leading-relaxed shadow-2xl ${
                msg.role === 'user' 
                  ? 'bg-primary text-white ml-6' 
                  : 'bg-white/5 border border-white/10 text-white mr-6'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-2 text-primary px-1 animate-pulse">
              <Sparkles size={14} className="animate-spin" />
              <span className="text-[10px] font-black uppercase tracking-[0.2em]">Processing Neural Request...</span>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-white/5 bg-black/80">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type tactical command..."
            className="flex-1 bg-white/5 border border-white/10 rounded-md px-4 py-3 text-[12px] font-mono text-white focus:outline-none focus:ring-1 focus:ring-primary transition-all placeholder:text-white/20"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <Button size="icon" onClick={handleSend} disabled={isLoading} className="h-11 w-11 bg-primary hover:bg-primary/90 shadow-[0_0_15px_rgba(0,145,255,0.3)]">
            <Send size={18} />
          </Button>
        </div>
        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 no-scrollbar scrollbar-hide">
          {["Traffic status", "Resource deployment", "Simulate event"].map(suggest => (
            <button 
              key={suggest}
              onClick={() => setInput(suggest)}
              className="whitespace-nowrap px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-[9px] hover:bg-primary/20 hover:border-primary/40 hover:text-primary transition-all uppercase font-black text-white/60"
            >
              {suggest}
            </button>
          ))}
        </div>
      </div>

      <style jsx>{`
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
