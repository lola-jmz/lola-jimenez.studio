'use client';

import { useRef, FormEvent, useState } from 'react';
import { motion, useInView } from 'framer-motion';

const NAV_LINKS = [
  { label: 'Inicio', href: '#inicio' },
  { label: 'Sobre mí', href: '#sobre-mi' },
  { label: 'Portfolio', href: '#portfolio' },
  { label: 'Tecnologia', href: '#tecnologia' },
  { label: 'Contacto', href: '#contacto' },
];

const SOCIAL_LINKS = [
  {
    label: 'Instagram',
    href: '#',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="17.5" cy="6.5" r="0.5" fill="currentColor" />
      </svg>
    ),
  },
  {
    label: 'Twitter/X',
    href: '#',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    label: 'OnlyFans',
    href: '#',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden>
        <circle cx="12" cy="12" r="10" />
        <path d="M8 12a4 4 0 1 0 8 0 4 4 0 0 0-8 0" />
      </svg>
    ),
  },
];

export function Footer() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-60px' });
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubscribe = (e: FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubmitted(true);
      setEmail('');
    }
  };

  const scrollTo = (href: string) => {
    const id = href.replace('#', '');
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <footer
      ref={ref}
      id="contacto"
      className="relative overflow-hidden"
      style={{ background: '#080808' }}
    >
      {/* Top border gradient */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(233,30,99,0.5), transparent)' }}
      />

      {/* Ambient background */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center bottom, rgba(233,30,99,0.06) 0%, transparent 70%)',
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-12">
        {/* Main footer content */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="pt-20 pb-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12"
        >
          {/* Brand column */}
          <div className="lg:col-span-1">
            <h3
              className="text-3xl font-bold text-white mb-3"
              style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic', color: '#E91E63' }}
            >
              Lola Jiménez
            </h3>
            <p className="text-white/40 text-sm leading-relaxed mb-6 font-sans">
              Contenido exclusivo y conexiones autenticas. Creatividad sin limites, experiencias que perduran.
            </p>
            <div className="flex gap-3">
              {SOCIAL_LINKS.map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  aria-label={s.label}
                  className="w-9 h-9 rounded-xl flex items-center justify-center text-white/50 hover:text-[#E91E63] transition-colors duration-200"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.08)',
                  }}
                >
                  {s.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Navigation column */}
          <div>
            <p className="text-white/60 text-xs font-semibold tracking-[0.15em] uppercase mb-5 font-sans">
              Navegacion
            </p>
            <ul className="space-y-3">
              {NAV_LINKS.map((link) => (
                <li key={link.label}>
                  <button
                    onClick={() => scrollTo(link.href)}
                    className="text-white/50 hover:text-white text-sm transition-colors duration-200 font-sans text-left"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact column */}
          <div>
            <p className="text-white/60 text-xs font-semibold tracking-[0.15em] uppercase mb-5 font-sans">
              Contacto
            </p>
            <address className="not-italic space-y-3 text-sm text-white/40 font-sans leading-relaxed">
              <p>Ignacio Perez 49A</p>
              <p>Col. Carrizal</p>
              <p>C.P. 76030</p>
              <p>Queretaro, Qro.</p>
            </address>
          </div>

          {/* Newsletter column */}
          <div>
            <p className="text-white/60 text-xs font-semibold tracking-[0.15em] uppercase mb-5 font-sans">
              Novedades
            </p>
            {submitted ? (
              <motion.p
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-sm text-[#E91E63] font-sans"
              >
                Gracias! Te avisamos cuando haya contenido nuevo.
              </motion.p>
            ) : (
              <form onSubmit={handleSubscribe} className="flex flex-col gap-3">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
                  required
                  className="w-full text-sm text-white placeholder-white/30 rounded-xl px-4 py-3 outline-none transition-all duration-200 font-sans"
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(233,30,99,0.5)'; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'; }}
                />
                <button
                  type="submit"
                  className="w-full text-sm font-semibold text-white py-3 rounded-xl transition-opacity duration-200 hover:opacity-90 font-sans"
                  style={{ background: 'linear-gradient(135deg, #E91E63, #c2185b)' }}
                >
                  Suscribirse
                </button>
              </form>
            )}
          </div>
        </motion.div>

        {/* Divider */}
        <div
          className="h-px"
          style={{ background: 'rgba(255,255,255,0.06)' }}
        />

        {/* Bottom bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="py-6 flex flex-col sm:flex-row items-center justify-between gap-3"
        >
          <p className="text-white/25 text-xs font-sans">
            &copy; {new Date().getFullYear()} Lola Jimenez Studio. Todos los derechos reservados.
          </p>
          <p className="text-white/20 text-xs font-sans">
            Contenido protegido. Uso no autorizado prohibido.
          </p>
        </motion.div>
      </div>
    </footer>
  );
}
