#!/usr/bin/env python3
"""
connection_manager.py

Gestor de conexiones WebSocket para chat en tiempo real.
Maneja múltiples conexiones concurrentes y broadcast de mensajes.
"""

import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestor de conexiones WebSocket activas.
    Permite enviar mensajes a usuarios específicos.
    """

    def __init__(self):
        # Dict[user_id: str, WebSocket]
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("ConnectionManager inicializado")

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Acepta una nueva conexión WebSocket y la registra.
        
        Args:
            websocket: Objeto WebSocket de FastAPI
            user_id: ID único del usuario (UUID string)
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"✅ Usuario {user_id} conectado. Total conexiones: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        """
        Elimina una conexión del registro cuando se desconecta.
        
        Args:
            user_id: ID del usuario desconectado
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"❌ Usuario {user_id} desconectado. Total conexiones: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, user_id: str):
        """
        Envía un mensaje JSON a un usuario específico.
        
        Args:
            message: Texto del mensaje
            user_id: ID del usuario destinatario
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                # Enviar como JSON para compatibilidad con frontend
                await websocket.send_json({"content": message})
                logger.debug(f"Mensaje enviado a {user_id}: {message[:50]}...")
            except Exception as e:
                logger.error(f"Error enviando mensaje a {user_id}: {e}")
                self.disconnect(user_id)
        else:
            logger.warning(f"Usuario {user_id} no tiene conexión activa")

    async def broadcast(self, message: str):
        """
        Envía un mensaje a todos los usuarios conectados.
        
        Args:
            message: Texto del mensaje a broadcast
        """
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error en broadcast para {user_id}: {e}")
                disconnected.append(user_id)
        
        # Limpiar conexiones muertas
        for user_id in disconnected:
            self.disconnect(user_id)

    def get_active_users(self) -> List[str]:
        """Retorna lista de IDs de usuarios actualmente conectados"""
        return list(self.active_connections.keys())

    def is_connected(self, user_id: str) -> bool:
        """Verifica si un usuario está conectado"""
        return user_id in self.active_connections
