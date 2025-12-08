'use client'

import { useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { Button } from "@/components/ui/button";
import { Icon } from "@iconify/react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useWebSocket } from "@/lib/useWebSocket";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

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

      <section id="inicio" className="relative pt-32 pb-24 md:pt-40 md:pb-32 overflow-hidden">
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-primary to-secondary"
          style={{
            opacity: heroOpacity,
            scale: heroScale
          }}
        />
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="flex flex-col md:flex-row items-center gap-12">
            <div className="flex-shrink-0">
              <img
                alt="Lola Jiménez"
                src="/images/hero.webp"
                className="w-64 h-64 rounded-full border-4 border-white shadow-2xl object-cover"
              />
            </div>
            <div className="flex-1 text-center md:text-left">
              <h1 className="font-heading text-5xl md:text-6xl font-bold text-white mb-6 font-serif italic">
                Bienvenidos a mi mundo creativo
              </h1>
              <p className="text-xl text-white/90 mb-8 font-light">
                Donde la creatividad y la conexión se encuentran
              </p>
              <Button
                size="lg"
                onClick={() => scrollToSection('sobre-mi')}
                className="bg-accent text-accent-foreground hover:bg-primary hover:text-primary-foreground hover:scale-105 transition-all duration-300 px-8 py-6 text-lg font-semibold shadow-lg"
              >
                Conóceme
                <Icon icon="solar:heart-bold" className="size-5" />
              </Button>
            </div>
          </div>
        </div>
      </section>
      <section id="sobre-mi" className="py-20 bg-background">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-primary mb-12 text-center md:text-left font-serif italic">
            Sobre mí
          </h2>
          <div className="grid md:grid-cols-2 gap-12 mb-16">
            <div>
              <img
                alt="About Lola"
                src="/images/about.webp"
                className="w-full aspect-[3/4] object-cover rounded-lg shadow-lg border-4 border-primary"
              />
            </div>
            <div className="flex flex-col justify-center">
              <p className="text-lg text-foreground leading-relaxed mb-8">
                Soy Lola Jiménez, creadora de contenido apasionada por el arte y las conexiones
                auténticas. Mi espacio es donde la creatividad cobra vida a través de conversaciones
                íntimas, contenido exclusivo y experiencias personalizadas que van más allá de lo
                superficial.
              </p>
            </div>
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
      <section id="portfolio" className="py-20 bg-card/20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-primary mb-12 text-center font-serif italic">
            Mi Portfolio
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="overflow-hidden border-4 border-primary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-primary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 1"
                src="/images/portafolio-1.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
            <Card className="overflow-hidden border-4 border-secondary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-secondary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 2"
                src="/images/portafolio-2.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
            <Card className="overflow-hidden border-4 border-primary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-primary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 3"
                src="/images/portafolio-3.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
            <Card className="overflow-hidden border-4 border-secondary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-secondary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 4"
                src="/images/portafolio-4.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
            <Card className="overflow-hidden border-4 border-primary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-primary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 5"
                src="/images/portafolio-5.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
            <Card className="overflow-hidden border-4 border-secondary rounded-xl hover:scale-105 hover:shadow-2xl hover:shadow-secondary/30 transition-all duration-300 cursor-pointer">
              <img
                alt="Portfolio 6"
                src="/images/portafolio-6.webp"
                className="w-full aspect-[3/4] object-cover"
              />
            </Card>
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
                  {msg.content}
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
