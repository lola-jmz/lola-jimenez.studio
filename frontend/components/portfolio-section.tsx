'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, useInView, AnimatePresence } from 'framer-motion';

const PORTFOLIO_IMAGES = [
  { src: '/images/portafolio-1.webp', label: 'Serie I' },
  { src: '/images/portafolio-2.webp', label: 'Serie II' },
  { src: '/images/portafolio-3.webp', label: 'Serie III' },
  { src: '/images/portafolio-4.webp', label: 'Serie IV' },
  { src: '/images/portafolio-5.webp', label: 'Serie V' },
  { src: '/images/portafolio-6.webp', label: 'Serie VI' },
  { src: '/images/portafolio-7.webp', label: 'Serie VII' },
  { src: '/images/portafolio-8.webp', label: 'Serie VIII' },
] as const;

const CONTAINER_VARIANTS = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
};

const ITEM_VARIANTS = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] } },
};

export function PortfolioSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-80px' });
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const openLightbox = useCallback((i: number) => setLightboxIndex(i), []);
  const closeLightbox = useCallback(() => setLightboxIndex(null), []);
  const prev = useCallback(() => setLightboxIndex((i) => (i === null ? null : (i - 1 + PORTFOLIO_IMAGES.length) % PORTFOLIO_IMAGES.length)), []);
  const next = useCallback(() => setLightboxIndex((i) => (i === null ? null : (i + 1) % PORTFOLIO_IMAGES.length)), []);

  useEffect(() => {
    if (lightboxIndex === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') prev();
      if (e.key === 'ArrowRight') next();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [lightboxIndex, closeLightbox, prev, next]);

  return (
    <>
      <section
        ref={sectionRef}
        id="portfolio"
        className="relative py-28 overflow-hidden"
        style={{ background: 'linear-gradient(180deg, #0a0a0a 0%, #111 100%)' }}
      >
        {/* Background texture */}
        <div
          className="absolute inset-0 pointer-events-none opacity-30"
          style={{
            backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(233,30,99,0.06) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(233,30,99,0.04) 0%, transparent 50%)',
          }}
        />

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-12">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="mb-14 flex flex-col md:flex-row md:items-end justify-between gap-6"
          >
            <div>
              <span className="text-[#E91E63] text-sm font-semibold tracking-[0.2em] uppercase font-sans">
                Portfolio
              </span>
              <h2
                className="mt-3 text-4xl md:text-5xl font-bold text-white leading-tight"
                style={{ fontFamily: 'var(--font-heading)', fontStyle: 'italic' }}
              >
                Trabajo Exclusivo
              </h2>
            </div>
            <p className="text-white/40 max-w-xs text-sm leading-relaxed font-sans">
              Cada imagen cuenta una historia. Contenido original, nunca reproducido.
            </p>
          </motion.div>

          {/* Masonry grid using CSS columns */}
          <motion.div
            variants={CONTAINER_VARIANTS}
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            className="columns-2 md:columns-3 lg:columns-4 gap-3 space-y-3"
          >
            {PORTFOLIO_IMAGES.map((img, i) => (
              <PortfolioCard
                key={img.src}
                src={img.src}
                label={img.label}
                index={i}
                onClick={() => openLightbox(i)}
              />
            ))}
          </motion.div>

          {/* Bottom CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.8 }}
            className="mt-16 text-center"
          >
            <p className="text-white/30 text-sm font-sans">
              Contenido de acceso privado — disponible via chat exclusivo
            </p>
          </motion.div>
        </div>
      </section>

      {/* Lightbox — rendered in portal */}
      {typeof document !== 'undefined' &&
        lightboxIndex !== null &&
        createPortal(
          <Lightbox
            src={PORTFOLIO_IMAGES[lightboxIndex].src}
            label={PORTFOLIO_IMAGES[lightboxIndex].label}
            index={lightboxIndex}
            total={PORTFOLIO_IMAGES.length}
            onClose={closeLightbox}
            onPrev={prev}
            onNext={next}
          />,
          document.body
        )}
    </>
  );
}

interface PortfolioCardProps {
  src: string;
  label: string;
  index: number;
  onClick: () => void;
}

function PortfolioCard({ src, label, onClick }: PortfolioCardProps) {
  return (
    <motion.div
      variants={ITEM_VARIANTS}
      className="group relative overflow-hidden rounded-2xl break-inside-avoid cursor-pointer mb-3"
      style={{
        border: '1px solid rgba(255,255,255,0.06)',
      }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      aria-label={`Ver ${label}`}
    >
      <img
        src={src}
        alt={label}
        className="w-full h-auto block"
        draggable={false}
        style={{ pointerEvents: 'none', userSelect: 'none', display: 'block' }}
        onContextMenu={(e) => e.preventDefault()}
      />

      {/* Hover overlay */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4"
        style={{
          background: 'linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 60%)',
        }}
      >
        <div className="flex items-center gap-2">
          <span
            className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white"
            style={{ background: '#E91E63' }}
          >
            +
          </span>
          <span className="text-white text-sm font-medium font-sans">{label}</span>
        </div>
      </div>

      {/* Gradient border on hover */}
      <div
        className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ border: '1px solid rgba(233,30,99,0.4)' }}
      />
    </motion.div>
  );
}

interface LightboxProps {
  src: string;
  label: string;
  index: number;
  total: number;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}

function Lightbox({ src, label, index, total, onClose, onPrev, onNext }: LightboxProps) {
  return (
    <AnimatePresence>
      <motion.div
        key="lightbox-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.25 }}
        className="fixed inset-0 z-[9999] flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.92)', backdropFilter: 'blur(8px)' }}
        onClick={onClose}
      >
        {/* Image */}
        <motion.div
          key={src}
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.92 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="relative max-w-[90vw] max-h-[85vh]"
          onClick={(e) => e.stopPropagation()}
        >
          <img
            src={src}
            alt={label}
            className="max-w-full max-h-[85vh] object-contain rounded-xl"
            draggable={false}
            style={{ pointerEvents: 'none', userSelect: 'none' }}
            onContextMenu={(e) => e.preventDefault()}
          />

          {/* Controls overlay */}
          <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-4">
            <button
              onClick={(e) => { e.stopPropagation(); onPrev(); }}
              className="w-10 h-10 rounded-full flex items-center justify-center text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)' }}
              aria-label="Anterior"
            >
              &#8249;
            </button>
            <span className="text-white/60 text-sm font-sans">{index + 1} / {total}</span>
            <button
              onClick={(e) => { e.stopPropagation(); onNext(); }}
              className="w-10 h-10 rounded-full flex items-center justify-center text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)' }}
              aria-label="Siguiente"
            >
              &#8250;
            </button>
          </div>
        </motion.div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-10 h-10 rounded-full flex items-center justify-center text-white/70 hover:text-white transition-colors"
          style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.15)' }}
          aria-label="Cerrar"
        >
          &#10005;
        </button>
      </motion.div>
    </AnimatePresence>
  );
}
