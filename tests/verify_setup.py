#!/usr/bin/env python3
"""
Script de verificación de setup para el Bot María.
Verifica que todas las dependencias, archivos y configuraciones estén correctas.
"""

import os
import sys
from pathlib import Path


class Colors:
    """Colores para output en terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_header(text):
    """Imprime un header"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def check_file_exists(filepath, required=True):
    """Verifica que un archivo existe"""
    exists = os.path.exists(filepath)
    status = f"{Colors.GREEN}✓{Colors.RESET}" if exists else f"{Colors.RED}✗{Colors.RESET}"
    req_text = "(REQUERIDO)" if required else "(opcional)"
    print(f"{status} {filepath} {req_text}")
    return exists


def check_env_var(var_name, required=True):
    """Verifica que una variable de entorno existe"""
    exists = os.getenv(var_name) is not None
    status = f"{Colors.GREEN}✓{Colors.RESET}" if exists else f"{Colors.RED}✗{Colors.RESET}"
    req_text = "(REQUERIDO)" if required else "(opcional)"
    print(f"{status} {var_name} {req_text}")
    return exists


def check_python_version():
    """Verifica la versión de Python"""
    print_header("Verificando Python")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 11:
        print(f"{Colors.GREEN}✓{Colors.RESET} Python {version_str} (compatible)")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.RESET} Python {version_str} (requiere 3.11+)")
        return False


def check_dependencies():
    """Verifica dependencias de Python"""
    print_header("Verificando Dependencias de Python")

    dependencies = [
        "telegram",
        "asyncpg",
        "cryptography",
        "google.generativeai",
        "PIL",  # Pillow
    ]

    optional_deps = [
        "faster_whisper",
        "pytest",
        "uvloop"
    ]

    all_ok = True

    print("\nRequeridas:")
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"{Colors.GREEN}✓{Colors.RESET} {dep}")
        except ImportError:
            print(f"{Colors.RED}✗{Colors.RESET} {dep} (NO INSTALADO)")
            all_ok = False

    print("\nOpcionales:")
    for dep in optional_deps:
        try:
            __import__(dep)
            print(f"{Colors.GREEN}✓{Colors.RESET} {dep}")
        except ImportError:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} {dep} (no instalado, pero opcional)")

    return all_ok


def check_project_files():
    """Verifica archivos del proyecto"""
    print_header("Verificando Archivos del Proyecto")

    required_files = [
        "bot_optimized.py",
        "database_pool.py",
        "state_machine.py",
        "message_buffer_optimized.py",
        "error_handler.py",
        "security.py",
        "audio_transcriber.py",
        "payment_validator.py",
        "MARÍA.md",
        "requirements.txt",
        ".env",
        "config/database_schema.sql"
    ]

    optional_files = [
        "README.md",
        ".env.example",
        ".gitignore"
    ]

    all_ok = True

    print("\nArchivos requeridos:")
    for filepath in required_files:
        if not check_file_exists(filepath, required=True):
            all_ok = False

    print("\nArchivos opcionales:")
    for filepath in optional_files:
        check_file_exists(filepath, required=False)

    return all_ok


def check_env_variables():
    """Verifica variables de entorno"""
    print_header("Verificando Variables de Entorno")

    # Cargar .env si existe
    env_path = Path(".env")
    if env_path.exists():
        print(f"{Colors.GREEN}✓{Colors.RESET} Archivo .env encontrado\n")

        # Cargar variables manualmente
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip('"')
    else:
        print(f"{Colors.RED}✗{Colors.RESET} Archivo .env NO encontrado\n")
        return False

    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "GEMINI_API_KEY",
        "DATABASE_URL",
        "ADMIN_USER_ID"
    ]

    optional_vars = [
        "ENCRYPTION_KEY",
        "MESSAGE_BUFFER_WAIT_SECONDS",
        "DB_POOL_MIN_SIZE",
        "DB_POOL_MAX_SIZE"
    ]

    all_ok = True

    print("Variables requeridas:")
    for var in required_vars:
        if not check_env_var(var, required=True):
            all_ok = False

    print("\nVariables opcionales:")
    for var in optional_vars:
        check_env_var(var, required=False)

    return all_ok


def check_external_commands():
    """Verifica comandos externos"""
    print_header("Verificando Comandos Externos")

    commands = {
        "ffmpeg": "requerido para procesamiento de audio",
        "psql": "requerido para PostgreSQL",
        "git": "opcional"
    }

    all_ok = True

    for cmd, description in commands.items():
        result = os.system(f"which {cmd} > /dev/null 2>&1")
        if result == 0:
            print(f"{Colors.GREEN}✓{Colors.RESET} {cmd} ({description})")
        else:
            if cmd in ["ffmpeg", "psql"]:
                print(f"{Colors.RED}✗{Colors.RESET} {cmd} ({description}) - NO INSTALADO")
                all_ok = False
            else:
                print(f"{Colors.YELLOW}⚠{Colors.RESET} {cmd} ({description}) - no instalado")

    return all_ok


def test_database_connection():
    """Intenta conectar a la base de datos"""
    print_header("Verificando Conexión a Base de Datos")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print(f"{Colors.RED}✗{Colors.RESET} DATABASE_URL no configurado")
        return False

    try:
        import asyncpg
        import asyncio

        async def test_conn():
            try:
                conn = await asyncpg.connect(database_url)
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                print(f"{Colors.GREEN}✓{Colors.RESET} Conexión exitosa")
                print(f"  PostgreSQL: {version.split(',')[0]}")
                return True
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.RESET} Error conectando: {e}")
                return False

        return asyncio.run(test_conn())

    except Exception as e:
        print(f"{Colors.RED}✗{Colors.RESET} Error: {e}")
        return False


def print_summary(results):
    """Imprime resumen final"""
    print_header("Resumen")

    total = len(results)
    passed = sum(results.values())

    if passed == total:
        print(f"{Colors.GREEN}✓ TODAS LAS VERIFICACIONES PASARON ({passed}/{total}){Colors.RESET}")
        print(f"\n{Colors.GREEN}¡El bot está listo para ejecutarse!{Colors.RESET}")
        print(f"\nEjecuta: {Colors.BLUE}python bot_optimized.py{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ ALGUNAS VERIFICACIONES FALLARON ({passed}/{total}){Colors.RESET}")
        print(f"\n{Colors.YELLOW}Por favor, revisa los errores arriba y corrígelos antes de ejecutar el bot.{Colors.RESET}")
        print(f"\nConsulta el README.md para más información sobre la instalación.")

    print()


def main():
    """Función principal"""
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BLUE}║         BOT MARÍA - VERIFICACIÓN DE SETUP                 ║{Colors.RESET}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.RESET}")

    results = {}

    # Ejecutar verificaciones
    results["Python Version"] = check_python_version()
    results["Dependencies"] = check_dependencies()
    results["Project Files"] = check_project_files()
    results["Environment Variables"] = check_env_variables()
    results["External Commands"] = check_external_commands()

    # Test de conexión a BD (opcional, puede fallar si BD no está configurada)
    print("\n")
    print(f"{Colors.YELLOW}Intentando conectar a la base de datos...{Colors.RESET}")
    db_result = test_database_connection()
    if db_result:
        results["Database Connection"] = True
    else:
        print(f"{Colors.YELLOW}⚠ La conexión a BD falló, pero puedes continuar.{Colors.RESET}")
        print(f"{Colors.YELLOW}  Asegúrate de configurar PostgreSQL antes de ejecutar el bot.{Colors.RESET}")

    # Imprimir resumen
    print_summary(results)

    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
