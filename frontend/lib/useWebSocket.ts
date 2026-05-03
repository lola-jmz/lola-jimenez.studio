'use client';

import { useState, useRef, useCallback } from 'react';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface ChatMessage {
  id: string;
  content: string;
  isBot: boolean;
  type: 'text' | 'image';
  imageUrl?: string;
  caption?: string;
  timestamp: Date;
}

interface IncomingMessage {
  type?: string;
  content?: string;
  url?: string;
  caption?: string;
}

export function useWebSocket(userId: string) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');

    const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000';
    const url = `${protocol}://${host}/ws/${userId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as IncomingMessage;
        const msgType = data.type ?? 'text';

        const msg: ChatMessage = {
          id: crypto.randomUUID(),
          content: data.content ?? '',
          isBot: true,
          type: msgType === 'image' ? 'image' : 'text',
          imageUrl: data.url,
          caption: data.caption,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, msg]);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => setStatus('error');
    ws.onclose = () => setStatus('disconnected');
  }, [userId]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('disconnected');
  }, []);

  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      content: text,
      isBot: false,
      type: 'text',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    wsRef.current.send(JSON.stringify({ type: 'text', content: text }));
  }, []);

  const sendImage = useCallback((file: File) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;

    setIsUploading(true);
    const reader = new FileReader();

    reader.onload = () => {
      const base64 = reader.result as string;
      wsRef.current?.send(JSON.stringify({ type: 'image', content: base64 }));
      setIsUploading(false);
    };

    reader.onerror = () => setIsUploading(false);
    reader.readAsDataURL(file);
  }, []);

  return { status, messages, isUploading, connect, disconnect, sendText, sendImage };
}
