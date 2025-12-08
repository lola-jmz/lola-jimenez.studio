"""
Máquina de Estados Finitos (FSM) para gestionar el flujo de conversación.

Estados posibles:
- INICIO: Usuario acaba de contactar
- CONVERSANDO: Interacción activa con María
- ESPERANDO_PAGO: María solicitó el pago
- VALIDANDO_COMPROBANTE: Usuario envió imagen, bot validando
- PAGO_APROBADO: Comprobante válido
- ENTREGANDO_PRODUCTO: Enviando imagen al cliente
- COMPLETADO: Transacción finalizada
- ERROR: Algo salió mal
"""

from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados posibles de una conversación"""
    INICIO = "inicio"
    CONVERSANDO = "conversando"
    ESPERANDO_PAGO = "esperando_pago"
    VALIDANDO_COMPROBANTE = "validando_comprobante"
    PAGO_RECHAZADO = "pago_rechazado"
    PAGO_APROBADO = "pago_aprobado"
    ENTREGANDO_PRODUCTO = "entregando_producto"
    COMPLETADO = "completado"
    ERROR = "error"
    BLOQUEADO = "bloqueado"  # Usuario sospechoso


class EventType(Enum):
    """Eventos que pueden disparar transiciones"""
    MENSAJE_RECIBIDO = "mensaje_recibido"
    AUDIO_RECIBIDO = "audio_recibido"
    IMAGEN_RECIBIDA = "imagen_recibida"
    SOLICITAR_PAGO = "solicitar_pago"
    COMPROBANTE_VALIDO = "comprobante_valido"
    COMPROBANTE_INVALIDO = "comprobante_invalido"
    PRODUCTO_ENTREGADO = "producto_entregado"
    ERROR_OCURRIDO = "error_ocurrido"
    RESETEAR = "resetear"
    BLOQUEAR_USUARIO = "bloquear_usuario"


@dataclass
class StateTransition:
    """Define una transición entre estados"""
    from_state: ConversationState
    event: EventType
    to_state: ConversationState
    condition: Optional[Callable[[Any], bool]] = None  # Condición opcional
    action: Optional[Callable[[Any], None]] = None     # Acción al transicionar


class ConversationStateMachine:
    """
    Máquina de estados finitos para gestionar conversaciones.
    
    Garantiza que los usuarios solo puedan transicionar entre estados
    válidos, previniendo inconsistencias.
    """
    
    def __init__(self):
        self.transitions: list[StateTransition] = []
        self._define_transitions()
    
    def _define_transitions(self):
        """Define todas las transiciones válidas del sistema"""
        
        # Desde INICIO
        self.add_transition(
            ConversationState.INICIO,
            EventType.MENSAJE_RECIBIDO,
            ConversationState.CONVERSANDO
        )
        self.add_transition(
            ConversationState.INICIO,
            EventType.AUDIO_RECIBIDO,
            ConversationState.CONVERSANDO
        )
        
        # Desde CONVERSANDO
        self.add_transition(
            ConversationState.CONVERSANDO,
            EventType.SOLICITAR_PAGO,
            ConversationState.ESPERANDO_PAGO
        )
        self.add_transition(
            ConversationState.CONVERSANDO,
            EventType.MENSAJE_RECIBIDO,
            ConversationState.CONVERSANDO  # Loop
        )
        
        # Desde ESPERANDO_PAGO
        self.add_transition(
            ConversationState.ESPERANDO_PAGO,
            EventType.IMAGEN_RECIBIDA,
            ConversationState.VALIDANDO_COMPROBANTE
        )
        self.add_transition(
            ConversationState.ESPERANDO_PAGO,
            EventType.MENSAJE_RECIBIDO,
            ConversationState.ESPERANDO_PAGO  # Usuario pregunta algo
        )
        
        # Desde VALIDANDO_COMPROBANTE
        self.add_transition(
            ConversationState.VALIDANDO_COMPROBANTE,
            EventType.COMPROBANTE_VALIDO,
            ConversationState.PAGO_APROBADO
        )
        self.add_transition(
            ConversationState.VALIDANDO_COMPROBANTE,
            EventType.COMPROBANTE_INVALIDO,
            ConversationState.PAGO_RECHAZADO
        )
        
        # Desde PAGO_RECHAZADO (reintento)
        self.add_transition(
            ConversationState.PAGO_RECHAZADO,
            EventType.IMAGEN_RECIBIDA,
            ConversationState.VALIDANDO_COMPROBANTE
        )
        
        # Desde PAGO_APROBADO
        self.add_transition(
            ConversationState.PAGO_APROBADO,
            EventType.PRODUCTO_ENTREGADO,
            ConversationState.COMPLETADO
        )
        
        # Transiciones de error (desde cualquier estado)
        for state in ConversationState:
            if state not in [ConversationState.ERROR, ConversationState.BLOQUEADO]:
                self.add_transition(
                    state,
                    EventType.ERROR_OCURRIDO,
                    ConversationState.ERROR
                )
                self.add_transition(
                    state,
                    EventType.BLOQUEAR_USUARIO,
                    ConversationState.BLOQUEADO
                )
        
        # Reset desde estados terminales
        for terminal_state in [ConversationState.COMPLETADO, ConversationState.ERROR]:
            self.add_transition(
                terminal_state,
                EventType.RESETEAR,
                ConversationState.INICIO
            )
    
    def add_transition(
        self,
        from_state: ConversationState,
        event: EventType,
        to_state: ConversationState,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None
    ):
        """Añade una transición al sistema"""
        self.transitions.append(
            StateTransition(from_state, event, to_state, condition, action)
        )
    
    def get_next_state(
        self,
        current_state: ConversationState,
        event: EventType,
        context: Optional[Dict] = None
    ) -> Optional[ConversationState]:
        """
        Obtiene el siguiente estado dada una transición.
        
        Args:
            current_state: Estado actual
            event: Evento disparador
            context: Datos adicionales para evaluar condiciones
        
        Returns:
            Siguiente estado o None si transición inválida
        """
        context = context or {}
        
        for transition in self.transitions:
            if (transition.from_state == current_state and 
                transition.event == event):
                
                # Verificar condición si existe
                if transition.condition and not transition.condition(context):
                    continue
                
                # Ejecutar acción si existe
                if transition.action:
                    try:
                        transition.action(context)
                    except Exception as e:
                        logger.error(f"Error ejecutando acción de transición: {e}")
                
                return transition.to_state
        
        # No se encontró transición válida
        logger.warning(
            f"Transición inválida: {current_state.value} -> {event.value}"
        )
        return None
    
    def is_terminal_state(self, state: ConversationState) -> bool:
        """Verifica si un estado es terminal (no puede progresar)"""
        return state in [
            ConversationState.COMPLETADO,
            ConversationState.BLOQUEADO
        ]


@dataclass
class UserConversation:
    """Representa el estado completo de una conversación de usuario"""
    user_id: int
    current_state: ConversationState
    state_history: list[tuple[ConversationState, datetime]]
    metadata: Dict[str, Any]
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_state = ConversationState.INICIO
        self.state_history = [(ConversationState.INICIO, datetime.now())]
        self.metadata = {
            "product_selected": None,
            "amount_expected": None,
            "payment_attempts": 0,
            "messages_count": 0,
            "created_at": datetime.now()
        }
    
    def transition_to(self, new_state: ConversationState):
        """Transiciona a un nuevo estado"""
        self.current_state = new_state
        self.state_history.append((new_state, datetime.now()))
        logger.info(f"Usuario {self.user_id}: {self.current_state.value}")
    
    def get_time_in_current_state(self) -> float:
        """Retorna segundos en el estado actual"""
        if not self.state_history:
            return 0
        last_transition_time = self.state_history[-1][1]
        return (datetime.now() - last_transition_time).total_seconds()
    
    def increment_payment_attempts(self):
        """Incrementa contador de intentos de pago"""
        self.metadata["payment_attempts"] += 1
    
    def should_block_for_suspicious_activity(self) -> bool:
        """Detecta actividad sospechosa"""
        # Demasiados intentos de pago
        if self.metadata["payment_attempts"] > 5:
            return True
        
        # Demasiado tiempo en validación
        if (self.current_state == ConversationState.VALIDANDO_COMPROBANTE and
            self.get_time_in_current_state() > 300):  # 5 minutos
            return True
        
        return False


class ConversationManager:
    """
    Gestor centralizado de conversaciones.
    Mantiene el estado de todos los usuarios activos.
    """
    
    def __init__(self):
        self.fsm = ConversationStateMachine()
        self.conversations: Dict[int, UserConversation] = {}
    
    def get_or_create_conversation(self, user_id: int) -> UserConversation:
        """Obtiene o crea conversación para un usuario"""
        if user_id not in self.conversations:
            self.conversations[user_id] = UserConversation(user_id)
        return self.conversations[user_id]
    
    def handle_event(
        self,
        user_id: int,
        event: EventType,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Procesa un evento para un usuario.
        
        Returns:
            True si transición fue exitosa, False si inválida
        """
        conversation = self.get_or_create_conversation(user_id)
        
        # Verificar actividad sospechosa
        if conversation.should_block_for_suspicious_activity():
            self.handle_event(user_id, EventType.BLOQUEAR_USUARIO)
            return False
        
        # Obtener siguiente estado
        next_state = self.fsm.get_next_state(
            conversation.current_state,
            event,
            context
        )
        
        if next_state is None:
            logger.warning(
                f"Evento {event.value} no válido en estado "
                f"{conversation.current_state.value} para usuario {user_id}"
            )
            return False
        
        # Transicionar
        conversation.transition_to(next_state)
        return True
    
    def get_state(self, user_id: int) -> ConversationState:
        """Obtiene estado actual de un usuario"""
        conversation = self.get_or_create_conversation(user_id)
        return conversation.current_state
    
    def get_conversation(self, user_id: int) -> UserConversation:
        """Obtiene conversación completa"""
        return self.get_or_create_conversation(user_id)


# === EJEMPLO DE USO ===

if __name__ == "__main__":
    manager = ConversationManager()
    user_id = 12345
    
    # Simular flujo
    print("🚀 Usuario inicia conversación")
    manager.handle_event(user_id, EventType.MENSAJE_RECIBIDO)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    print("💬 Usuario conversa")
    manager.handle_event(user_id, EventType.MENSAJE_RECIBIDO)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    print("💰 María solicita pago")
    manager.handle_event(user_id, EventType.SOLICITAR_PAGO)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    print("📸 Usuario envía comprobante")
    manager.handle_event(user_id, EventType.IMAGEN_RECIBIDA)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    print("✅ Comprobante validado")
    manager.handle_event(user_id, EventType.COMPROBANTE_VALIDO)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    print("📦 Producto entregado")
    manager.handle_event(user_id, EventType.PRODUCTO_ENTREGADO)
    print(f"Estado: {manager.get_state(user_id).value}\n")
    
    # Historial
    conv = manager.get_conversation(user_id)
    print("\n📊 Historial de estados:")
    for state, timestamp in conv.state_history:
        print(f"  {timestamp.strftime('%H:%M:%S')} - {state.value}")
