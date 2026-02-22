'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Button } from "@/components/ui/button";
import { Icon } from "@iconify/react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useWebSocket } from "@/lib/useWebSocket";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

// Componente de Imagen Protegida — Anti-Zoom + Anti-Print + Anti-Drag
const ImageWithBlur = ({ src, alt, className, imgClassName = "w-full h-full object-cover" }: { src: string, alt: string, className?: string, imgClassName?: string }) => {
  const [isZoomed, setIsZoomed] = useState(false)

  useEffect(() => {
    const detectZoom = () => {
      if (window.visualViewport) {
        setIsZoomed(window.visualViewport.scale > 1.25)
      } else {
        setIsZoomed(false)
      }
    }
    detectZoom()

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', detectZoom)
      window.visualViewport.addEventListener('scroll', detectZoom)
    } else {
      window.addEventListener('resize', detectZoom)
    }

    return () => {
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', detectZoom)
        window.visualViewport.removeEventListener('scroll', detectZoom)
      } else {
        window.removeEventListener('resize', detectZoom)
      }
    }
  }, [])

  return (
    <div
      className={`lola-protected-img relative overflow-hidden select-none ${className}`}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* Imagen con pointer-events desactivados para bloquear drag/right-click directo */}
      <img
        src={src}
        alt={alt}
        className={`${imgClassName} transition-all duration-500`}
        loading="lazy"
        draggable={false}
        style={{
          filter: isZoomed ? 'blur(12px) grayscale(70%)' : 'none',
          WebkitUserSelect: 'none',
          userSelect: 'none',
          pointerEvents: 'none',
          touchAction: 'none',
          transition: 'filter 0.4s ease',
        }}
      />
      {/* Capa transparente encima que intercepta todos los eventos del mouse */}
      <div
        className="absolute inset-0"
        onContextMenu={(e) => e.preventDefault()}
        style={{ backgroundColor: 'transparent', cursor: 'default' }}
      />
      {/* Watermark diagonal sutil */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(233,30,99,0.05) 35px, rgba(233,30,99,0.05) 70px)',
        }}
      />
    </div>
  )
}

// Componente de Imagen de Chat — Sin protecciones, visor via Portal para escapar
// el containing block del DialogContent (transform: translate(-50%,-50%) permanente)
const ChatImage = ({ src, alt, caption }: { src: string; alt: string; caption?: string }) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="space-y-1">
      <img
        src={src}
        alt={alt}
        className="w-full rounded-lg shadow-md cursor-zoom-in"
        style={{ touchAction: 'pinch-zoom' }}
        onClick={() => setIsOpen(true)}
      />
      {caption && <p className="text-sm italic">{caption}</p>}

      {isOpen &&
        typeof document !== 'undefined' &&
        createPortal(
          <div
            onClick={() => setIsOpen(false)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 99999,
              backgroundColor: 'rgba(0,0,0,0.92)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              touchAction: 'pinch-zoom',
            }}
          >
            <img
              src={src}
              alt={alt}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                touchAction: 'pinch-zoom',
              }}
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setIsOpen(false)}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                background: 'rgba(0,0,0,0.5)',
                border: 'none',
                borderRadius: '50%',
                width: '2.5rem',
                height: '2.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '1.25rem',
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>,
          document.body
        )}
    </div>
  )
}

export function LolaJiménezStudioLandingPage() {
  const [chatOpen, setChatOpen] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const userId = typeof window !== 'undefined'
    ? localStorage.getItem('lola-user-id') || crypto.randomUUID()
    : 'guest'

  const { status, messages, sendText, sendImage, isUploading, connect, disconnect } = useWebSocket(userId)

  const { scrollY } = useScroll()

  const heroOpacity = useTransform(scrollY, [0, 300], [1, 0])
  const heroScale = useTransform(scrollY, [0, 300], [1, 0.9])

  const handleOpenChat = () => {
    if (typeof window !== 'undefined' && !localStorage.getItem('lola-user-id')) {
      localStorage.setItem('lola-user-id', userId)
    }
    setChatOpen(true)
    connect()
  }

  const handleCloseChat = () => {
    setChatOpen(false)
    disconnect()
  }

  const handleSend = () => {
    if (inputValue.trim()) {
      sendText(inputValue.trim())
      setInputValue('')
    }
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      sendImage(file)
      e.target.value = '' // Reset input
    }
  }

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed top-0 left-0 right-0 z-50 h-20 px-6 bg-white/95 backdrop-blur-sm shadow-md">
        <div className="max-w-7xl mx-auto h-full flex items-center justify-between">
          <div className="text-2xl font-bold text-primary font-serif italic">LOLA Jiménez</div>
          <nav className="hidden md:flex items-center gap-2">
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary"
              onClick={() => scrollToSection('inicio')}
            >
              Inicio
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary"
              onClick={() => scrollToSection('sobre-mi')}
            >
              Sobre mí
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary"
              onClick={() => scrollToSection('portfolio')}
            >
              Portfolio
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary"
              onClick={() => scrollToSection('contacto')}
            >
              Contacto
            </Button>
          </nav>
          <Button
            size="icon"
            variant="ghost"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Icon icon={mobileMenuOpen ? "solar:close-circle-bold" : "solar:hamburger-menu-bold"} className="size-6" />
          </Button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="fixed top-20 left-0 right-0 bg-white shadow-lg z-40 md:hidden">
          <nav className="flex flex-col p-4 space-y-2">
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary justify-start"
              onClick={() => {
                scrollToSection('inicio')
                setMobileMenuOpen(false)
              }}
            >
              Inicio
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary justify-start"
              onClick={() => {
                scrollToSection('sobre-mi')
                setMobileMenuOpen(false)
              }}
            >
              Sobre mí
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary justify-start"
              onClick={() => {
                scrollToSection('portfolio')
                setMobileMenuOpen(false)
              }}
            >
              Portfolio
            </Button>
            <Button
              variant="ghost"
              className="text-foreground hover:text-primary justify-start"
              onClick={() => {
                scrollToSection('contacto')
                setMobileMenuOpen(false)
              }}
            >
              Contacto
            </Button>
          </nav>
        </div>
      )}

      <section id="inicio" className="relative pt-28 pb-20 md:pt-36 md:pb-28 overflow-hidden">
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-primary to-secondary"
          style={{ opacity: heroOpacity, scale: heroScale }}
        />
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          {/* Mobile: texto arriba, imagen abajo — Desktop: texto izq, imagen der */}
          <div className="flex flex-col md:flex-row items-center gap-10 md:gap-14">
            <div className="flex-1 text-center md:text-left">
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
                className="font-heading text-5xl md:text-6xl font-bold text-white mb-6 font-serif italic"
              >
                Bienvenidos a mi mundo creativo
              </motion.h1>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                className="text-xl text-white/90 mb-8 font-light"
              >
                Donde la creatividad y la conexión se encuentran
              </motion.p>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 }}
              >
                <Button
                  size="lg"
                  onClick={() => scrollToSection('sobre-mi')}
                  className="bg-accent text-accent-foreground hover:bg-white hover:text-primary hover:scale-105 transition-all duration-300 px-8 py-6 text-lg font-semibold shadow-lg"
                >
                  Conóceme
                  <Icon icon="solar:heart-bold" className="size-5" />
                </Button>
              </motion.div>
            </div>
            {/* Imagen hero 5:4 horizontal — borde translúcido blanco */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="flex-shrink-0 w-full md:w-[400px] lg:w-[460px] p-[3px] rounded-2xl shadow-2xl"
              style={{ background: 'rgba(255,255,255,0.25)' }}
            >
              <div className="rounded-[14px] overflow-hidden">
                <ImageWithBlur
                  alt="Lola Jiménez"
                  src="/images/hero.webp"
                  className="w-full aspect-[5/4]"
                />
              </div>
            </motion.div>
          </div>
        </div>
      </section>
      <section id="sobre-mi" className="py-20 bg-background">
        <div className="max-w-6xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="font-heading text-4xl md:text-5xl font-bold text-primary mb-12 text-center md:text-left font-serif italic"
          >
            Sobre mí
          </motion.h2>
          <div className="grid md:grid-cols-2 gap-12 mb-16">
            {/* Foto de perfil circular */}
            <motion.div
              initial={{ opacity: 0, scale: 0.85 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="flex flex-col items-center gap-4"
            >
              {/* Anillo gradiente fucsia→violet */}
              <div
                className="p-[3px] rounded-full shadow-2xl"
                style={{ background: 'linear-gradient(135deg, #E91E63, #9C27B0, #E91E63)' }}
              >
                <div className="rounded-full overflow-hidden w-56 h-56 md:w-72 md:h-72">
                  <ImageWithBlur
                    alt="Lola Jiménez — foto de perfil"
                    src="/images/about.webp"
                    className="w-full h-full"
                  />
                </div>
              </div>
              <p className="text-sm text-muted-foreground font-medium tracking-wider">✦ Lola Jiménez Studio ✦</p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="flex flex-col justify-center"
            >
              <p className="text-lg text-foreground leading-relaxed mb-8">
                Soy Lola Jiménez, creadora de contenido apasionada por el arte y las conexiones
                auténticas. Mi espacio es donde la creatividad cobra vida a través de conversaciones
                íntimas, contenido exclusivo y experiencias personalizadas que van más allá de lo
                superficial.
              </p>
            </motion.div>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-card/50 border-2 border-primary p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <CardContent className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                  <Icon icon="solar:palette-bold" className="size-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-primary">Creatividad</h3>
                <p className="text-muted-foreground">
                  Arte y contenido único que inspira y conecta
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-2 border-primary p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <CardContent className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-secondary/10 rounded-full flex items-center justify-center">
                  <Icon icon="solar:heart-bold" className="size-8 text-secondary" />
                </div>
                <h3 className="text-xl font-bold text-secondary">Autenticidad</h3>
                <p className="text-muted-foreground">
                  Conexiones reales sin filtros ni pretensiones
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-2 border-primary p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <CardContent className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-accent/20 rounded-full flex items-center justify-center">
                  <Icon icon="solar:star-bold" className="size-8 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-primary">Exclusividad</h3>
                <p className="text-muted-foreground">Experiencias premium diseñadas para ti</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
      <section id="portfolio" className="py-16 md:py-24 bg-gradient-to-b from-white to-pink-50/40">
        <div className="max-w-6xl mx-auto px-4 md:px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="font-heading text-4xl md:text-5xl font-bold text-primary mb-2 text-center font-serif italic"
          >
            Mi Portfolio
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 }}
            className="text-center text-muted-foreground mb-10 md:mb-14 text-sm tracking-widest uppercase"
          >
            ✦ Contenido exclusivo ✦
          </motion.p>

          {/*
            Layout mampostería (Pinterest style):
            — móvil  : 2 cols
            — desktop: 3 cols
            Las imágenes respetan su ratio real.
          */}
          <div className="columns-2 md:columns-3 gap-3 md:gap-4 space-y-3 md:space-y-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n, idx) => (
              <motion.div
                key={n}
                initial={{ opacity: 0, y: 28 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ delay: idx * 0.07, duration: 0.5, ease: 'easeOut' }}
                className="group relative overflow-hidden rounded-2xl cursor-pointer break-inside-avoid shadow-sm"
                style={{
                  /* Gradiente borde 2px fucsia→violet */
                  background: `linear-gradient(135deg, #E91E63 0%, #9C27B0 50%, #E91E63 100%)`,
                  padding: '2px',
                }}
              >
                <div className="relative rounded-[14px] overflow-hidden bg-pink-50 flex">
                  <ImageWithBlur
                    alt={`Portfolio ${n}`}
                    src={`/images/portafolio-${n}.webp`}
                    className="w-full"
                    imgClassName="w-full h-auto object-contain block"
                  />
                  {/* Hover overlay con icono ✦ */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end justify-center pb-5 pointer-events-none">
                    <span
                      className="text-white text-3xl drop-shadow-lg"
                      style={{ textShadow: '0 0 20px rgba(233,30,99,0.8)' }}
                    >
                      ✦
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      <section className="py-20 bg-gradient-to-b from-background to-card/30">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-secondary mb-12 text-center font-serif italic">
            ¿Por qué elegir mi espacio?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="bg-background border-2 border-primary p-8 hover:bg-card hover:border-secondary transition-all duration-300">
              <CardContent className="space-y-6">
                <div className="w-20 h-20 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                  <Icon icon="solar:star-bold" className="size-10 text-primary" />
                </div>
                <h3 className="text-2xl font-bold text-primary text-center">Contenido Exclusivo</h3>
                <p className="text-muted-foreground text-center">
                  Acceso a material único y personalizado que no encontrarás en ningún otro lugar
                </p>
              </CardContent>
            </Card>
            <Card className="bg-background border-2 border-primary p-8 hover:bg-card hover:border-secondary transition-all duration-300">
              <CardContent className="space-y-6">
                <div className="w-20 h-20 mx-auto bg-secondary/10 rounded-full flex items-center justify-center">
                  <Icon icon="solar:chat-round-bold" className="size-10 text-secondary" />
                </div>
                <h3 className="text-2xl font-bold text-secondary text-center">
                  Conversaciones Auténticas
                </h3>
                <p className="text-muted-foreground text-center">
                  Conexión real y genuina sin filtros, donde ser tú mismo es celebrado
                </p>
              </CardContent>
            </Card>
            <Card className="bg-background border-2 border-primary p-8 hover:bg-card hover:border-secondary transition-all duration-300">
              <CardContent className="space-y-6">
                <div className="w-20 h-20 mx-auto bg-accent/20 rounded-full flex items-center justify-center">
                  <Icon icon="solar:crown-bold" className="size-10 text-primary" />
                </div>
                <h3 className="text-2xl font-bold text-primary text-center">Experiencia Premium</h3>
                <p className="text-muted-foreground text-center">
                  Atención personalizada de alta calidad diseñada especialmente para ti
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
      <section className="py-20 bg-background">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <Button
            size="lg"
            onClick={handleOpenChat}
            className="bg-gradient-to-br from-primary to-secondary text-primary-foreground hover:shadow-[0_20px_50px_rgba(233,30,99,0.5)] hover:scale-105 transition-all duration-300 px-12 py-8 text-xl font-bold rounded-full shadow-2xl"
          >
            Chat Privado 💟
          </Button>
        </div>
      </section>
      <footer id="contacto" className="bg-gradient-to-br from-black to-gray-900 text-white py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-12 mb-12">
            <div>
              <div className="text-2xl font-bold text-primary mb-4 font-serif italic">
                LOLA Jiménez
              </div>
              <p className="text-gray-400">Creatividad y conexión auténtica</p>
            </div>
            <div>
              <h3 className="text-lg font-bold mb-4">Navegación</h3>
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  onClick={() => scrollToSection('inicio')}
                  className="text-gray-400 hover:text-primary w-full justify-start"
                >
                  Inicio
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => scrollToSection('sobre-mi')}
                  className="text-gray-400 hover:text-primary w-full justify-start"
                >
                  Sobre mí
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => scrollToSection('portfolio')}
                  className="text-gray-400 hover:text-primary w-full justify-start"
                >
                  Portfolio
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => scrollToSection('contacto')}
                  className="text-gray-400 hover:text-primary w-full justify-start"
                >
                  Contacto
                </Button>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-bold mb-4">Conéctate</h3>
              <div className="flex gap-3 mb-6">
                <Button
                  size="icon"
                  variant="ghost"
                  className="text-white hover:text-accent hover:scale-110 transition-transform w-10 h-10"
                >
                  <Icon icon="solar:instagram-bold" className="size-6" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  className="text-white hover:text-accent hover:scale-110 transition-transform w-10 h-10"
                >
                  <Icon icon="solar:twitter-bold" className="size-6" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  className="text-white hover:text-accent hover:scale-110 transition-transform w-10 h-10"
                >
                  <Icon icon="solar:facebook-bold" className="size-6" />
                </Button>
              </div>
              <div className="space-y-3">
                <Input
                  type="email"
                  className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                  placeholder="Tu email"
                />
                <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                  Suscribirse
                </Button>
              </div>
            </div>
          </div>
          <Separator className="bg-white/10 mb-8" />
          <div className="text-center text-sm text-muted">
            © 2025 Lola Jiménez Studio. Todos los derechos reservados.
          </div>
        </div>
      </footer>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 md:hidden">
        <Button
          size="lg"
          onClick={handleOpenChat}
          className="bg-gradient-to-br from-primary to-secondary text-primary-foreground hover:shadow-[0_20px_50px_rgba(233,30,99,0.5)] hover:scale-105 transition-all duration-300 px-8 py-6 text-lg font-bold rounded-full shadow-2xl"
        >
          Chat Privado 💟
        </Button>
      </div>

      {/* Chat Modal */}
      <Dialog open={chatOpen} onOpenChange={handleCloseChat}>
        <DialogContent className="sm:max-w-md h-[600px] flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-primary font-serif italic">
              Chat Privado con Lola 💟
            </DialogTitle>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500' :
                status === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`} />
              <span className="text-xs text-muted-foreground">
                {status === 'connected' ? 'Conectado' :
                  status === 'connecting' ? 'Conectando...' :
                    'Desconectado'}
              </span>
            </div>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-card/50 rounded-lg">
            {messages.length === 0 && (
              <p className="text-center text-muted-foreground text-sm">
                Holi!
              </p>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.isBot ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2 ${msg.isBot
                    ? 'bg-secondary/20 text-foreground'
                    : 'bg-primary text-primary-foreground'
                    }`}
                >
                  {/* Renderizar imagen inline si es tipo image */}
                  {msg.type === 'image' && msg.imageUrl ? (
                    <ChatImage
                      src={msg.imageUrl}
                      alt={msg.caption || "Imagen de Lola"}
                      caption={msg.caption}
                    />
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 pt-4">
            <input
              type="file"
              id="image-upload"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
            <Button
              size="icon"
              variant="outline"
              onClick={() => document.getElementById('image-upload')?.click()}
              disabled={status !== 'connected' || isUploading}
              className="border-primary hover:bg-primary/10"
              title="Adjuntar comprobante de pago"
            >
              {isUploading ? (
                <Icon icon="solar:refresh-circle-bold" className="size-5 animate-spin" />
              ) : (
                <Icon icon="solar:paperclip-bold" className="size-5" />
              )}
            </Button>
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Escribe tu mensaje..."
              className="flex-1"
              disabled={status !== 'connected' || isUploading}
            />
            <Button
              onClick={handleSend}
              disabled={status !== 'connected' || !inputValue.trim() || isUploading}
              className="bg-primary hover:bg-primary/90"
            >
              <Icon icon="solar:send-bold" className="size-5" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}