-- Fase 1 - Blindaje: Respaldo de estado de conversaciones
-- Tabla para respaldo automático de Redis a PostgreSQL

CREATE TABLE IF NOT EXISTS conversation_state_backup (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    state_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_conv_backup_user_id ON conversation_state_backup(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_backup_created_at ON conversation_state_backup(created_at DESC);

-- Función para auto-actualizar updated_at
CREATE OR REPLACE FUNCTION update_conversation_backup_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar timestamp automáticamente
DROP TRIGGER IF EXISTS trigger_update_conversation_backup_timestamp ON conversation_state_backup;
CREATE TRIGGER trigger_update_conversation_backup_timestamp
BEFORE UPDATE ON conversation_state_backup
FOR EACH ROW
EXECUTE FUNCTION update_conversation_backup_timestamp();

-- Comentario descriptivo
COMMENT ON TABLE conversation_state_backup IS 'Respaldo automático de estados de conversación desde Redis. Permite recuperación ante fallos.';
COMMENT ON COLUMN conversation_state_backup.user_id IS 'Identificador único del usuario (UUID string)';
COMMENT ON COLUMN conversation_state_backup.state_data IS 'Estado completo de conversación en formato JSON';
COMMENT ON COLUMN conversation_state_backup.created_at IS 'Fecha de primer guardado';
COMMENT ON COLUMN conversation_state_backup.updated_at IS 'Última actualización (automática via trigger)';
