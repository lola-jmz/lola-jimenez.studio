import { useEffect, useRef, useState, useCallback } from "react";

export interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  type?: "text" | "image";  // Tipo de mensaje
  imageUrl?: string;        // URL de imagen (si type === "image")
  caption?: string;         // Caption de imagen
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket(userId: string) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/${userId}`);

    ws.onopen = () => {
      console.log("✅ WebSocket conectado");
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Detectar tipo de mensaje (text, image, typing)
        const msgType = data.type || "text";

        if (msgType === "typing") {
          // Indicador de escritura - no agregar a mensajes
          console.log("🔄 Lola está escribiendo...");
          return;
        }

        const botMessage: Message = {
          id: crypto.randomUUID(),
          content: data.content || data.caption || "",
          isBot: true,
          timestamp: new Date(),
          type: msgType,
          imageUrl: data.url,           // URL de imagen si es tipo image
          caption: data.caption,        // Caption si aplica
        };

        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        console.error("Error parseando mensaje:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
      setStatus("error");
    };

    ws.onclose = () => {
      console.log("❌ WebSocket desconectado");
      setStatus("disconnected");
    };

    socketRef.current = ws;
  }, [userId]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const sendText = useCallback((content: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      // Agregar mensaje del usuario a la UI
      const userMessage: Message = {
        id: crypto.randomUUID(),
        content,
        isBot: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Enviar por WebSocket
      socketRef.current.send(
        JSON.stringify({
          type: "text",
          content,
        })
      );
    }
  }, []);

  const sendImage = useCallback(async (file: File) => {
    try {
      setIsUploading(true);

      // 1. Validar tamaño (5 MB máximo)
      const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
      if (file.size > MAX_SIZE) {
        alert("La imagen es muy pesada. El límite es 5 MB.");
        setIsUploading(false);
        return;
      }

      // 2. Convertir a Base64
      const base64 = await fileToBase64(file);

      // 3. Agregar mensaje visual del usuario (imagen)
      const userMessage: Message = {
        id: crypto.randomUUID(),
        content: "[Imagen enviada: comprobante de pago]",
        isBot: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // 4. Enviar por WebSocket
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(
          JSON.stringify({
            type: "image",
            content: base64,
          })
        );
      }
    } catch (error) {
      console.error("Error enviando imagen:", error);
      alert("Error al enviar la imagen. Inténtalo de nuevo.");
    } finally {
      setIsUploading(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    messages,
    isUploading,
    sendText,
    sendImage,
    connect,
    disconnect,
  };
}

// Helper: Convertir archivo a Base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
      } else {
        reject(new Error("Error leyendo archivo"));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
