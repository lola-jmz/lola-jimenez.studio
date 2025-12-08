-- ================================================================
-- Migración: Añadir columna user_identifier para usuarios web
-- Fecha: Noviembre 2025
-- Propósito: Soportar identificadores UUID para usuarios web
--            sin afectar user_id INT existente (Telegram legacy)
-- ================================================================

-- IMPORTANTE: Esta migración es NO DESTRUCTIVA
-- Mantiene todos los datos existentes intactos

BEGIN;

-- ============================
-- 1. Añadir columna user_identifier a tabla users
-- ============================
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS user_identifier VARCHAR(255);

COMMENT ON COLUMN users.user_identifier IS 
'Identificador único para usuarios web (UUID). NULL para usuarios Telegram legacy';

-- ============================
-- 2. Crear índice único en user_identifier
-- ============================
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_user_identifier 
ON users(user_identifier) 
WHERE user_identifier IS NOT NULL;

COMMENT ON INDEX idx_users_user_identifier IS 
'Índice único para búsquedas rápidas por user_identifier (solo valores no-NULL)';

-- ============================
-- 3. Poblar user_identifier para usuarios Telegram existentes
-- ============================
-- Convierte user_id INT a string para usuarios legacy
UPDATE users 
SET user_identifier = CONCAT('telegram_', user_id::TEXT)
WHERE user_identifier IS NULL 
  AND user_id IS NOT NULL;

-- ============================
-- 4. Añadir columna user_identifier a tabla conversations
-- ============================
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_identifier VARCHAR(255);

COMMENT ON COLUMN conversations.user_identifier IS 
'FK a users.user_identifier. NULL para conversaciones Telegram legacy';

-- Crear índice para joins y búsquedas
CREATE INDEX IF NOT EXISTS idx_conversations_user_identifier 
ON conversations(user_identifier);

-- ============================
-- 5. Añadir columna user_identifier a tabla messages
-- ============================
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS user_identifier VARCHAR(255);

COMMENT ON COLUMN messages.user_identifier IS 
'FK a users.user_identifier. NULL para mensajes Telegram legacy';

CREATE INDEX IF NOT EXISTS idx_messages_user_identifier 
ON messages(user_identifier);

-- ============================
-- 6. Añadir columna user_identifier a tabla payments
-- ============================
ALTER TABLE payments 
ADD COLUMN IF NOT EXISTS user_identifier VARCHAR(255);

COMMENT ON COLUMN payments.user_identifier IS 
'FK a users.user_identifier. NULL para pagos Telegram legacy';

CREATE INDEX IF NOT EXISTS idx_payments_user_identifier 
ON payments(user_identifier);

-- ============================
-- 7. Añadir columna user_identifier a tabla audit_log
-- ============================
ALTER TABLE audit_log 
ADD COLUMN IF NOT EXISTS user_identifier VARCHAR(255);

COMMENT ON COLUMN audit_log.user_identifier IS 
'FK a users.user_identifier. NULL para audits Telegram legacy';

CREATE INDEX IF NOT EXISTS idx_audit_log_user_identifier 
ON audit_log(user_identifier);

-- ============================
-- 8. Poblar user_identifier en tablas relacionadas
-- ============================
-- Para datos legacy de Telegram
UPDATE conversations 
SET user_identifier = CONCAT('telegram_', user_id::TEXT)
WHERE user_identifier IS NULL 
  AND user_id IS NOT NULL;

UPDATE messages 
SET user_identifier = CONCAT('telegram_', user_id::TEXT)
WHERE user_identifier IS NULL 
  AND user_id IS NOT NULL;

UPDATE payments 
SET user_identifier = CONCAT('telegram_', user_id::TEXT)
WHERE user_identifier IS NULL 
  AND user_id IS NOT NULL;

UPDATE audit_log 
SET user_identifier = CONCAT('telegram_', user_id::TEXT)
WHERE user_identifier IS NULL 
  AND user_id IS NOT NULL;

-- ============================
-- 9. Verificación
-- ============================
-- Contar usuarios con user_identifier
DO $$
DECLARE
    total_users INT;
    users_with_identifier INT;
BEGIN
    SELECT COUNT(*) INTO total_users FROM users;
    SELECT COUNT(*) INTO users_with_identifier FROM users WHERE user_identifier IS NOT NULL;
    
    RAISE NOTICE '✅ Migración completada';
    RAISE NOTICE 'Total usuarios: %', total_users;
    RAISE NOTICE 'Usuarios con identifier: %', users_with_identifier;
    
    IF total_users != users_with_identifier THEN
        RAISE WARNING '⚠️ Hay % usuarios sin user_identifier', (total_users - users_with_identifier);
    END IF;
END $$;

COMMIT;

-- ================================================================
-- Notas Importantes:
-- ================================================================
-- 1. user_id INT se mantiene para compatibilidad Telegram
-- 2. user_identifier VARCHAR(255) es para nuevos usuarios web (UUID)
-- 3. Usuarios Telegram legacy: user_identifier = "telegram_{user_id}"
-- 4. Usuarios web nuevos: user_identifier = UUID (ej: "a1b2c3d4...")
-- 5. Todas las columnas son NULLABLE para no romper datos existentes
-- 6. Los índices mejoran performance sin afectar datos
-- 
-- Rollback (si es necesario):
-- ALTER TABLE users DROP COLUMN IF EXISTS user_identifier;
-- ALTER TABLE conversations DROP COLUMN IF EXISTS user_identifier;
-- ALTER TABLE messages DROP COLUMN IF EXISTS user_identifier;
-- ALTER TABLE payments DROP COLUMN IF EXISTS user_identifier;
-- ALTER TABLE audit_log DROP COLUMN IF EXISTS user_identifier;
-- ================================================================
