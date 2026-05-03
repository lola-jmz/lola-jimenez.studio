'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface HeroSectionProps {
  onOpenChat: () => void;
}

export function HeroSection({ onOpenChat }: HeroSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  });

  // Smooth spring physics for parallax — no memory leaks, pure transform
  const rawY = useTransform(scrollYProgress, [0, 1], [0, 180]);
  const parallaxY = useSpring(rawY, { stiffness: 60, damping: 20, mass: 0.5 });

  const rawScale = useTransform(scrollYProgress, [0, 1], [1, 1.08]);
  const bgScale = useSpring(rawScale, { stiffness: 60, damping: 20, mass: 0.5 });

  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const contentY = useTransform(scrollYProgress, [0, 1], [0, 60]);

  return (
    <section
      ref={containerRef}
      id="inicio"
      className="relative h-screen min-h-[680px] overflow-hidden flex items-center"
    >
      {/* Parallax background image */}
      <motion.div
        className="absolute inset-0 will-change-transform"
        style={{ y: parallaxY, scale: bgScale }}
      >
        <img
          src="/images/hero.webp"
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
          draggable={false}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        />
        {/* Deep color overlay for readability */}
        <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-[#E91E63]/20 to-black/60" />
      </motion.div>

      {/* Ambient orbs — CSS only, no JS animation loops */}
      <div
        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(233,30,99,0.18) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
      />
      <div
        className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(233,30,99,0.12) 0%, transparent 70%)',
          filter: 'blur(80px)',
        }}
      />

      {/* Content */}
      <motion.div
        className="relative z-10 w-full max-w-7xl mx-auto px-6 lg:px-12"
        style={{ y: contentY, opacity }}
      >
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left: text + CTA */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 32 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            >
              <span className="inline-block text-[#FFB6C1] text-sm font-semibold tracking-[0.2em] uppercase mb-4 font-sans">
                Contenido Exclusivo
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
              className="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-[1.05] mb-6"
              style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}
            >
              Lola
              <br />
              <span style={{ color: '#E91E63' }}>Jiménez</span>
              <br />
              Studio
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="text-lg text-white/75 mb-10 max-w-md leading-relaxed font-sans"
            >
              Creatividad, autenticidad y experiencias premium. Bienvenido a mi mundo.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-wrap gap-4"
            >
              <Button
                size="lg"
                onClick={onOpenChat}
                className="relative overflow-hidden px-8 py-6 text-base font-semibold rounded-full text-white border-0 cursor-pointer"
                style={{
                  background: 'linear-gradient(135deg, #E91E63, #c2185b)',
                  boxShadow: '0 8px 32px rgba(233,30,99,0.45)',
                }}
              >
                <span className="relative z-10">Chat Privado</span>
              </Button>

              <Button
                size="lg"
                variant="ghost"
                onClick={() => document.getElementById('portfolio')?.scrollIntoView({ behavior: 'smooth' })}
                className="px-8 py-6 text-base font-semibold rounded-full text-white border border-white/25 hover:border-white/50 hover:bg-white/10 transition-all duration-300 backdrop-blur-sm cursor-pointer"
              >
                Ver Portfolio
              </Button>
            </motion.div>
          </div>

          {/* Right: glassmorphism card with portrait */}
          <motion.div
            initial={{ opacity: 0, x: 40, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="hidden lg:flex justify-center"
          >
            <GlassCard />
          </motion.div>
        </div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        style={{ opacity }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.6 }}
      >
        <span className="text-white/50 text-xs tracking-widest uppercase font-sans">Scroll</span>
        <motion.div
          className="w-px h-12 bg-gradient-to-b from-white/50 to-transparent"
          animate={{ scaleY: [1, 0.4, 1] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          style={{ originY: 0 }}
        />
      </motion.div>
    </section>
  );
}

function GlassCard() {
  return (
    <div className="relative w-[340px] h-[440px]">
      {/* Outer glow ring */}
      <div
        className="absolute -inset-1 rounded-3xl"
        style={{
          background: 'linear-gradient(135deg, rgba(233,30,99,0.6), rgba(233,30,99,0.1), rgba(255,182,193,0.4))',
          filter: 'blur(1px)',
        }}
      />

      {/* Glass panel */}
      <div
        className="relative h-full rounded-3xl overflow-hidden"
        style={{
          background: 'rgba(255,255,255,0.08)',
          backdropFilter: 'blur(20px) saturate(180%)',
          WebkitBackdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255,255,255,0.18)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
        }}
      >
        {/* Image fills 75% of card */}
        <div className="absolute inset-0 bottom-[25%]">
          <img
            src="/images/hero.webp"
            alt="Lola Jiménez"
            className="w-full h-full object-cover"
            draggable={false}
            style={{ pointerEvents: 'none', userSelect: 'none' }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        </div>

        {/* Bottom info bar */}
        <div
          className="absolute bottom-0 left-0 right-0 p-5"
          style={{
            background: 'rgba(0,0,0,0.35)',
            backdropFilter: 'blur(12px)',
            borderTop: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <p className="text-white font-bold text-lg font-sans">Lola Jiménez</p>
          <p className="text-[#FFB6C1] text-sm font-sans">Querétaro, México</p>
          <div className="mt-3 flex gap-2 items-center">
            <span
              className="inline-flex items-center gap-1.5 text-xs text-white/80 px-3 py-1 rounded-full font-sans"
              style={{ background: 'rgba(233,30,99,0.3)', border: '1px solid rgba(233,30,99,0.4)' }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: '#4caf50', boxShadow: '0 0 6px #4caf50' }}
              />
              Activa
            </span>
          </div>
        </div>

        {/* Inner highlight */}
        <div
          className="absolute inset-0 pointer-events-none rounded-3xl"
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.12) 0%, transparent 50%)',
          }}
        />
      </div>
    </div>
  );
}
