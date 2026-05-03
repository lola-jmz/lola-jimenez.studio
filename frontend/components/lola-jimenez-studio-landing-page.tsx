'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import { useWebSocket } from '@/lib/useWebSocket';
import { HeroSection } from '@/components/hero-section';
import { TechStackSection } from '@/components/tech-stack-section';
import { PortfolioSection } from '@/components/portfolio-section';
import { Footer } from '@/components/footer';

// ─── Protected Image ─────────────────────────────────────────────────────────

interface ProtectedImageProps {
  src: string;
  alt: string;
  className?: string;
  imgClassName?: string;
}

function ProtectedImage({ src, alt, className = '', imgClassName = 'w-full h-full object-cover' }: ProtectedImageProps) {
  const [isZoomed, setIsZoomed] = useState(false);

  useEffect(() => {
    const detectZoom = () => {
      setIsZoomed(window.visualViewport ? window.visualViewport.scale > 1.25 : false);
    };
    detectZoom();
    const vp = window.visualViewport;
    if (vp) {
      vp.addEventListener('resize', detectZoom);
      vp.addEventListener('scroll', detectZoom);
      return () => { vp.removeEventListener('resize', detectZoom); vp.removeEventListener('scroll', detectZoom); };
    }
    window.addEventListener('resize', detectZoom);
    return () => window.removeEventListener('resize', detectZoom);
  }, []);

  return (
    <div
      className={`lola-protected-img relative overflow-hidden select-none ${className}`}
      onContextMenu={(e) => e.preventDefault()}
    >
      <img
        src={src}
        alt={alt}
        className={imgClassName}
        draggable={false}
        style={{
          filter: isZoomed ? 'blur(12px) grayscale(70%)' : 'none',
          userSelect: 'none',
          pointerEvents: 'none',
          touchAction: 'none',
          transition: 'filter 0.4s ease',
          WebkitUserSelect: 'none',
        }}
      />
      <div className="absolute inset-0" onContextMenu={(e) => e.preventDefault()} />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(233,30,99,0.04) 35px, rgba(233,30,99,0.04) 70px)',
        }}
      />
    </div>
  );
}

// ─── Chat Image Viewer ────────────────────────────────────────────────────────

interface ChatImageProps {
  src: string;
  alt?: string;
  caption?: string;
}

function ChatImage({ src, alt, caption }: ChatImageProps) {
  const [isOpen, setIsOpen] = useState(false);
  const close = useCallback(() => setIsOpen(false), []);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, close]);

  if (!src) return null;

  return (
    <div className="flex flex-col gap-1">
      <img
        src={src}
        alt={alt ?? 'Imagen del chat'}
        className="w-full rounded-xl shadow-md cursor-zoom-in"
        onClick={() => setIsOpen(true)}
      />
      {caption && <span className="text-xs opacity-60 px-1">{caption}</span>}
      {isOpen && typeof document !== 'undefined' &&
        createPortal(
          <div
            className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/92"
            onClick={close}
            style={{ backdropFilter: 'blur(6px)' }}
          >
            <img
              src={src}
              alt={alt ?? ''}
              className="max-w-[90vw] max-h-[90vh] object-contain rounded-xl"
              draggable={false}
              style={{ pointerEvents: 'none', userSelect: 'none' }}
              onContextMenu={(e) => e.preventDefault()}
            />
            <button
              onClick={close}
              className="absolute top-4 right-4 w-10 h-10 rounded-full flex items-center justify-center text-white/70 hover:text-white"
              style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)' }}
              aria-label="Cerrar"
            >
              &#10005;
            </button>
          </div>,
          document.body
        )}
    </div>
  );
}

// ─── Header ───────────────────────────────────────────────────────────────────

function Header({ onOpenChat }: { onOpenChat: () => void }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { scrollY } = useScroll();
  const headerBg = useTransform(scrollY, [0, 80], ['rgba(0,0,0,0)', 'rgba(8,8,8,0.95)']);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setMobileOpen(false);
  };

  const NAV = [
    { label: 'Inicio', id: 'inicio' },
    { label: 'Sobre mi', id: 'sobre-mi' },
    { label: 'Portfolio', id: 'portfolio' },
    { label: 'Tecnologia', id: 'tecnologia' },
    { label: 'Contacto', id: 'contacto' },
  ];

  return (
    <>
      <motion.header
        className="fixed top-0 left-0 right-0 z-50 h-[72px]"
        style={{
          background: headerBg,
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0)',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-12 h-full flex items-center justify-between">
          <button
            onClick={() => scrollTo('inicio')}
            className="text-2xl font-bold cursor-pointer bg-transparent border-0"
            style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic', color: '#E91E63' }}
          >
            Lola Jimenez
          </button>

          <nav className="hidden md:flex items-center gap-1">
            {NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className="px-4 py-2 text-sm text-white/60 hover:text-white transition-colors duration-200 rounded-lg hover:bg-white/5 font-sans cursor-pointer bg-transparent border-0"
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={onOpenChat}
              className="px-5 py-2.5 text-sm font-semibold text-white rounded-full transition-all duration-200 hover:scale-105 cursor-pointer font-sans border-0"
              style={{ background: 'linear-gradient(135deg, #E91E63, #c2185b)', boxShadow: '0 4px 16px rgba(233,30,99,0.35)' }}
            >
              Chat Privado
            </button>
          </div>

          <button
            className="md:hidden text-white/70 hover:text-white p-2 cursor-pointer bg-transparent border-0"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? 'Cerrar menu' : 'Abrir menu'}
          >
            {mobileOpen ? (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><path d="M3 12h18M3 6h18M3 18h18" /></svg>
            )}
          </button>
        </div>
      </motion.header>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            key="mobile-menu"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="fixed top-[72px] left-0 right-0 z-40 py-4 px-6"
            style={{
              background: 'rgba(8,8,8,0.97)',
              borderBottom: '1px solid rgba(255,255,255,0.07)',
              backdropFilter: 'blur(16px)',
            }}
          >
            {NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className="block w-full text-left py-3 text-white/60 hover:text-white text-sm font-sans transition-colors cursor-pointer bg-transparent border-0"
                style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}
              >
                {item.label}
              </button>
            ))}
            <button
              onClick={() => { onOpenChat(); setMobileOpen(false); }}
              className="mt-4 w-full py-3 text-sm font-semibold text-white rounded-xl cursor-pointer font-sans border-0"
              style={{ background: 'linear-gradient(135deg, #E91E63, #c2185b)' }}
            >
              Chat Privado
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// ─── About Section ────────────────────────────────────────────────────────────

function AboutSection() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { rootMargin: '-80px' }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <section id="sobre-mi" ref={ref} className="py-28 relative overflow-hidden" style={{ background: '#0d0d0d' }}>
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -32 }}
            animate={visible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.85, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div
              className="absolute -inset-2 rounded-3xl"
              style={{
                background: 'linear-gradient(135deg, rgba(233,30,99,0.3), transparent 50%)',
                filter: 'blur(2px)',
              }}
            />
            <div className="relative rounded-3xl overflow-hidden" style={{ aspectRatio: '3/4' }}>
              <ProtectedImage
                src="/images/about.webp"
                alt="Lola Jimenez"
                className="absolute inset-0 w-full h-full"
                imgClassName="w-full h-full object-cover"
              />
              <div
                className="absolute bottom-0 left-0 right-0 p-6"
                style={{
                  background: 'rgba(0,0,0,0.4)',
                  backdropFilter: 'blur(16px)',
                  borderTop: '1px solid rgba(255,255,255,0.1)',
                }}
              >
                <p className="text-white font-bold text-xl font-sans">Lola Jimenez</p>
                <p className="text-sm font-sans" style={{ color: '#FFB6C1' }}>Creadora de contenido · Queretaro, Mx</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 32 }}
            animate={visible ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.85, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="text-[#E91E63] text-sm font-semibold tracking-[0.2em] uppercase font-sans">Sobre mi</span>
            <h2
              className="mt-3 text-4xl md:text-5xl font-bold text-white leading-tight mb-6"
              style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}
            >
              Mi historia, mi arte
            </h2>
            <p className="text-white/55 text-base leading-relaxed mb-6 font-sans">
              Soy Lola Jimenez, creadora de contenido apasionada por las conexiones autenticas y el arte de la expresion personal. Mi espacio es donde la creatividad cobra vida a traves de conversaciones intimas, contenido exclusivo y experiencias personalizadas.
            </p>
            <p className="text-white/40 text-base leading-relaxed mb-10 font-sans">
              Cada pieza que creo refleja mi vision y mi mundo. Aqui no hay filtros ni pretensiones — solo autenticidad y calidad sin compromiso.
            </p>
            <div className="grid grid-cols-3 gap-6">
              {[
                { value: '100%', label: 'Original' },
                { value: 'Exclusivo', label: 'Contenido' },
                { value: 'Privado', label: 'Acceso' },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="p-4 rounded-2xl text-center"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
                >
                  <p className="font-bold text-lg font-sans" style={{ color: '#E91E63' }}>{stat.value}</p>
                  <p className="text-white/35 text-xs mt-0.5 font-sans">{stat.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ─── CTA Section ─────────────────────────────────────────────────────────────

function CTASection({ onOpenChat }: { onOpenChat: () => void }) {
  return (
    <section className="relative py-28 overflow-hidden" style={{ background: '#080808' }}>
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at center, rgba(233,30,99,0.1) 0%, transparent 60%)' }}
      />
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(233,30,99,0.3), transparent)' }}
      />
      <div className="relative z-10 max-w-3xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2
            className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight"
            style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}
          >
            Listo para acceder?
          </h2>
          <p className="text-white/45 text-lg mb-10 font-sans">
            Contenido exclusivo disponible solo via chat privado. Trato personalizado, respuesta inmediata.
          </p>
          <button
            onClick={onOpenChat}
            className="inline-flex items-center gap-3 px-10 py-5 text-base font-semibold text-white rounded-full transition-all duration-300 hover:scale-105 cursor-pointer font-sans border-0"
            style={{
              background: 'linear-gradient(135deg, #E91E63, #c2185b)',
              boxShadow: '0 16px 48px rgba(233,30,99,0.4)',
            }}
          >
            Iniciar Chat Privado
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </motion.div>
      </div>
    </section>
  );
}

// ─── Chat Dialog ──────────────────────────────────────────────────────────────

interface ChatDialogProps {
  open: boolean;
  userId: string;
  onClose: () => void;
}

function ChatDialog({ open, userId, onClose }: ChatDialogProps) {
  const { status, messages, isUploading, connect, disconnect, sendText, sendImage } = useWebSocket(userId);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) connect();
    else disconnect();
  }, [open, connect, disconnect]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (input.trim()) { sendText(input.trim()); setInput(''); }
  };

  const handleImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) { sendImage(file); e.target.value = ''; }
  };

  if (!open) return null;

  return createPortal(
    <AnimatePresence>
      <motion.div
        key="chat-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[9000] flex items-center justify-center p-4"
        style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}
        onClick={onClose}
      >
        <motion.div
          key="chat-panel"
          initial={{ opacity: 0, scale: 0.93, y: 24 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.93, y: 24 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md h-[600px] flex flex-col rounded-3xl overflow-hidden"
          style={{
            background: 'rgba(12,12,12,0.95)',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 32px 80px rgba(0,0,0,0.6)',
            backdropFilter: 'blur(24px)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Chat header */}
          <div
            className="flex items-center justify-between px-5 py-4"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full overflow-hidden" style={{ border: '2px solid rgba(233,30,99,0.4)' }}>
                <img src="/images/about.webp" alt="Lola" className="w-full h-full object-cover" draggable={false} />
              </div>
              <div>
                <p className="text-white font-semibold text-sm font-sans">Lola Jimenez</p>
                <div className="flex items-center gap-1.5">
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      background: status === 'connected' ? '#4caf50' : status === 'connecting' ? '#ff9800' : '#555',
                      boxShadow: status === 'connected' ? '0 0 6px #4caf50' : 'none',
                    }}
                  />
                  <span className="text-white/40 text-xs font-sans">
                    {status === 'connected' ? 'Activa' : status === 'connecting' ? 'Conectando...' : 'Desconectada'}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full flex items-center justify-center text-white/40 hover:text-white transition-colors cursor-pointer bg-transparent border-0"
              style={{ background: 'rgba(255,255,255,0.06)' }}
              aria-label="Cerrar chat"
            >
              &#10005;
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="h-full flex items-center justify-center">
                <p className="text-white/25 text-sm font-sans text-center">Inicia la conversacion escribiendo un mensaje</p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.isBot ? 'justify-start' : 'justify-end'}`}>
                <div
                  className="max-w-[78%] px-4 py-2.5 rounded-2xl text-sm font-sans leading-relaxed"
                  style={
                    msg.isBot
                      ? { background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.9)' }
                      : { background: 'linear-gradient(135deg, #E91E63, #c2185b)', color: '#fff' }
                  }
                >
                  {msg.type === 'image' && msg.imageUrl ? (
                    <ChatImage src={msg.imageUrl} alt={msg.caption} caption={msg.caption} />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input row */}
          <div
            className="px-4 py-4 flex items-center gap-2"
            style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}
          >
            <input
              type="file"
              id="chat-file-input"
              accept="image/*"
              onChange={handleImage}
              className="hidden"
            />
            <button
              onClick={() => document.getElementById('chat-file-input')?.click()}
              disabled={status !== 'connected' || isUploading}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white/40 hover:text-white/70 transition-colors disabled:opacity-30 cursor-pointer border-0"
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
              aria-label="Adjuntar imagen"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.47" />
              </svg>
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Escribe un mensaje..."
              disabled={status !== 'connected'}
              className="flex-1 text-sm text-white bg-transparent outline-none font-sans disabled:opacity-30"
              style={{ caretColor: '#E91E63' }}
            />

            <button
              onClick={handleSend}
              disabled={status !== 'connected' || !input.trim()}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white transition-all disabled:opacity-30 cursor-pointer border-0"
              style={{ background: 'linear-gradient(135deg, #E91E63, #c2185b)' }}
              aria-label="Enviar"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" />
              </svg>
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
}

// ─── Root Component ───────────────────────────────────────────────────────────

export function LolaJiménezStudioLandingPage() {
  const [chatOpen, setChatOpen] = useState(false);
  const [userId] = useState<string>(() => {
    if (typeof window === 'undefined') return 'guest';
    const stored = localStorage.getItem('lola-user-id');
    if (stored) return stored;
    const id = crypto.randomUUID();
    localStorage.setItem('lola-user-id', id);
    return id;
  });

  const openChat = useCallback(() => setChatOpen(true), []);
  const closeChat = useCallback(() => setChatOpen(false), []);

  return (
    <div className="min-h-screen" style={{ background: '#080808' }}>
      <Header onOpenChat={openChat} />
      <HeroSection onOpenChat={openChat} />
      <AboutSection />
      <PortfolioSection />
      <TechStackSection />
      <CTASection onOpenChat={openChat} />
      <Footer />

      {/* Floating mobile CTA */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 md:hidden">
        <button
          onClick={openChat}
          className="px-7 py-4 text-sm font-semibold text-white rounded-full shadow-2xl transition-all duration-300 hover:scale-105 cursor-pointer font-sans border-0"
          style={{
            background: 'linear-gradient(135deg, #E91E63, #c2185b)',
            boxShadow: '0 8px 32px rgba(233,30,99,0.5)',
          }}
        >
          Chat Privado
        </button>
      </div>

      {typeof document !== 'undefined' && (
        <ChatDialog open={chatOpen} userId={userId} onClose={closeChat} />
      )}
    </div>
  );
}
