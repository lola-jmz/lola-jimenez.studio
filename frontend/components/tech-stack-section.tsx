'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface Tech {
  name: string;
  category: string;
  icon: string;
  color: string;
}

const TECH_STACK: Tech[] = [
  { name: 'Next.js', category: 'Frontend', icon: '▲', color: '#ffffff' },
  { name: 'React 19', category: 'UI Library', icon: '⚛', color: '#61dafb' },
  { name: 'TypeScript', category: 'Language', icon: 'TS', color: '#3178c6' },
  { name: 'Tailwind v4', category: 'Styling', icon: '~', color: '#38bdf8' },
  { name: 'FastAPI', category: 'Backend', icon: '⚡', color: '#009688' },
  { name: 'WebSockets', category: 'Real-time', icon: '⟳', color: '#E91E63' },
  { name: 'Gemini AI', category: 'Intelligence', icon: '✦', color: '#ffd700' },
  { name: 'PostgreSQL', category: 'Database', icon: '⬡', color: '#336791' },
  { name: 'Backblaze B2', category: 'Storage', icon: '☁', color: '#e05d0b' },
  { name: 'Redis', category: 'Cache', icon: '◈', color: '#dc382d' },
  { name: 'Framer Motion', category: 'Animation', icon: '◉', color: '#E91E63' },
  { name: 'Railway', category: 'Deployment', icon: '⊞', color: '#7c3aed' },
];

const CONTAINER_VARIANTS = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06 },
  },
};

const ITEM_VARIANTS = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] } },
};

export function TechStackSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-80px' });

  return (
    <section
      ref={sectionRef}
      id="tecnologia"
      className="relative py-28 overflow-hidden"
      style={{ background: '#0a0a0a' }}
    >
      {/* Background grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(233,30,99,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(233,30,99,0.04) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />

      {/* Ambient glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center top, rgba(233,30,99,0.12) 0%, transparent 70%)',
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="mb-16 text-center"
        >
          <span className="text-[#E91E63] text-sm font-semibold tracking-[0.2em] uppercase font-sans">
            Stack Tecnologico
          </span>
          <h2
            className="mt-3 text-4xl md:text-5xl font-bold text-white leading-tight"
            style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}
          >
            Construido con lo mejor
          </h2>
          <p className="mt-4 text-white/50 max-w-lg mx-auto text-base font-sans">
            Cada pieza elegida para rendimiento, escalabilidad y experiencia de usuario de primera clase.
          </p>
        </motion.div>

        {/* Cards grid */}
        <motion.div
          variants={CONTAINER_VARIANTS}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4"
        >
          {TECH_STACK.map((tech) => (
            <TechCard key={tech.name} tech={tech} />
          ))}
        </motion.div>

        {/* Bottom stat row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, delay: 0.6 }}
          className="mt-20 grid grid-cols-3 gap-8 max-w-xl mx-auto text-center"
        >
          {[
            { value: '99%', label: 'Uptime' },
            { value: '<50ms', label: 'Latencia WS' },
            { value: '24/7', label: 'Disponible' },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col gap-1">
              <span
                className="text-3xl font-bold"
                style={{ color: '#E91E63', fontFamily: 'var(--font-sans)' }}
              >
                {stat.value}
              </span>
              <span className="text-white/40 text-sm font-sans">{stat.label}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

function TechCard({ tech }: { tech: Tech }) {
  return (
    <motion.div
      variants={ITEM_VARIANTS}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.25 }}
      className="group relative rounded-2xl p-5 flex flex-col items-center gap-3 cursor-default"
      style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Icon */}
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold font-mono"
        style={{
          background: `${tech.color}18`,
          border: `1px solid ${tech.color}30`,
          color: tech.color,
          transition: 'background 0.2s, border-color 0.2s',
        }}
      >
        {tech.icon}
      </div>

      <div className="text-center">
        <p className="text-white text-sm font-semibold leading-tight font-sans">{tech.name}</p>
        <p className="text-white/35 text-xs mt-0.5 font-sans">{tech.category}</p>
      </div>

      {/* Hover glow — CSS only */}
      <div
        className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ border: `1px solid ${tech.color}50` }}
      />
    </motion.div>
  );
}
