-- Bot de Telegram "María" - PostgreSQL Database Schema
-- Versión: 1.0
-- Optimizado para 150+ usuarios concurrentes

-- Extension para UUID (opcional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Tabla: users
-- Almacena información de usuarios
-- =====================================================

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_bot BOOLEAN DEFAULT FALSE,
    language_code VARCHAR(10),

    -- Estado de pago
    has_paid BOOLEAN DEFAULT FALSE,
    payment_data JSONB DEFAULT '{}',
    total_purchases INTEGER DEFAULT 0,

    -- Metadatos
    is_blocked BOOLEAN DEFAULT FALSE,
    abuse_score INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_has_paid ON users(has_paid);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_users_is_blocked ON users(is_blocked);


-- =====================================================
-- Tabla: conversations
-- Sesiones de conversación con estado
-- =====================================================

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Estado de la conversación
    state VARCHAR(50) DEFAULT 'INITIAL',
    context JSONB DEFAULT '{}',

    -- Productos
    selected_product_id VARCHAR(255),

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);

-- Índices para conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations(state);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);


-- =====================================================
-- Tabla: messages
-- Historial completo de mensajes
-- =====================================================

CREATE TABLE IF NOT EXISTS messages (
    message_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,

    -- Contenido del mensaje
    message TEXT NOT NULL,
    is_bot BOOLEAN DEFAULT FALSE,
    message_type VARCHAR(20) DEFAULT 'text',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para messages
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_is_bot ON messages(is_bot);


-- =====================================================
-- Tabla: payments
-- Transacciones de pago
-- =====================================================

CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,

    -- Información del pago
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(50),

    -- Validación
    status VARCHAR(20) DEFAULT 'pending',
    proof_image_path TEXT,
    validation_result JSONB DEFAULT '{}',
    validation_score DECIMAL(3, 2),
    is_validated BOOLEAN DEFAULT FALSE,
    validated_by VARCHAR(50),

    -- Producto
    product_id VARCHAR(255),
    product_delivered BOOLEAN DEFAULT FALSE,
    delivery_data JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- Índices para payments
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_is_validated ON payments(is_validated);
CREATE INDEX IF NOT EXISTS idx_payments_product_delivered ON payments(product_delivered);


-- =====================================================
-- Tabla: audit_log
-- Log de eventos importantes del sistema
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para audit_log
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);


-- =====================================================
-- Funciones y Triggers
-- =====================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para users
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para conversations
DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =====================================================
-- Vistas útiles
-- =====================================================

-- Vista: usuarios activos en las últimas 24 horas
CREATE OR REPLACE VIEW active_users_24h AS
SELECT
    u.user_id,
    u.username,
    u.first_name,
    u.has_paid,
    u.last_activity,
    COUNT(DISTINCT m.message_id) AS message_count
FROM users u
LEFT JOIN messages m ON u.user_id = m.user_id
    AND m.created_at > NOW() - INTERVAL '24 hours'
WHERE u.last_activity > NOW() - INTERVAL '24 hours'
GROUP BY u.user_id, u.username, u.first_name, u.has_paid, u.last_activity;


-- Vista: estadísticas de conversiones
CREATE OR REPLACE VIEW conversion_stats AS
SELECT
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN u.has_paid THEN u.user_id END) AS paid_users,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN u.has_paid THEN u.user_id END) /
        NULLIF(COUNT(DISTINCT u.user_id), 0),
        2
    ) AS conversion_rate,
    SUM(CASE WHEN p.status = 'completed' THEN p.amount ELSE 0 END) AS total_revenue
FROM users u
LEFT JOIN payments p ON u.user_id = p.user_id;


-- =====================================================
-- Datos iniciales (opcional)
-- =====================================================

-- Insertar usuario admin si no existe (ajusta el user_id según tu ADMIN_USER_ID)
-- INSERT INTO users (user_id, username, first_name, is_bot, has_paid)
-- VALUES (123456789, 'admin', 'Admin', FALSE, TRUE)
-- ON CONFLICT (user_id) DO NOTHING;


-- =====================================================
-- Permisos (ajusta según tu configuración)
-- =====================================================

-- Ejemplo de permisos para el usuario del bot
-- GRANT CONNECT ON DATABASE maria_bot TO maria_bot;
-- GRANT USAGE ON SCHEMA public TO maria_bot;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO maria_bot;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO maria_bot;


-- =====================================================
-- Mantenimiento
-- =====================================================

-- Limpieza periódica de mensajes antiguos (ejecutar mensualmente)
-- DELETE FROM messages WHERE created_at < NOW() - INTERVAL '6 months';

-- Limpieza de conversaciones inactivas
-- DELETE FROM conversations WHERE ended_at < NOW() - INTERVAL '3 months';


-- =====================================================
-- Verificación
-- =====================================================

-- Verificar que las tablas se crearon correctamente
DO $$
BEGIN
    RAISE NOTICE 'Schema creado exitosamente';
    RAISE NOTICE 'Tablas: users, conversations, messages, payments, audit_log';
    RAISE NOTICE 'Vistas: active_users_24h, conversion_stats';
END $$;
