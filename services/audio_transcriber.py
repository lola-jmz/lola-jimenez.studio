"""
Transcriptor de audio usando faster-whisper.
Optimizado para transcripción local con bajo consumo de recursos.

Ventajas de faster-whisper:
- 4x más rápido que whisper original
- 50% menos memoria RAM
- Sin costo de API (100% local)
- Ahorro estimado: $1,800/año vs OpenAI Whisper API
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from faster_whisper import WhisperModel
except ImportError:
    raise ImportError(
        "faster-whisper no está instalado. "
        "Instala con: pip install faster-whisper"
    )

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """
    Transcriptor de audio usando faster-whisper.

    Usa el modelo "base" por defecto para balance entre velocidad y precisión.
    Soporta español y otros idiomas.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "es"
    ):
        """
        Args:
            model_size: Tamaño del modelo ("tiny", "base", "small", "medium", "large")
                - tiny: más rápido, menos preciso (~1GB RAM)
                - base: balance recomendado (~1.5GB RAM)
                - small: mejor precisión (~2GB RAM)
                - medium: muy bueno (~5GB RAM)
                - large: máxima precisión (~10GB RAM)
            device: "cpu" o "cuda" (GPU)
            compute_type: "int8" (más rápido) o "float16" (más preciso, requiere GPU)
            language: Código de idioma ISO 639-1 ("es", "en", etc.)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language

        logger.info(f"Inicializando AudioTranscriber con modelo '{model_size}'")

        try:
            # Inicializar modelo
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            logger.info(f"✅ Modelo '{model_size}' cargado correctamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando faster-whisper: {e}")
            raise

        # Estadísticas
        self.stats = {
            "total_transcriptions": 0,
            "total_errors": 0,
            "total_duration_seconds": 0.0,
            "average_transcription_time": 0.0
        }

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True
    ) -> str:
        """
        Transcribe un archivo de audio a texto.

        Args:
            audio_path: Path al archivo de audio (.ogg, .mp3, .wav, .m4a, etc.)
            language: Idioma del audio (None = auto-detección)
            beam_size: Tamaño del beam search (5 = balance velocidad/precisión)
            vad_filter: Voice Activity Detection para filtrar silencio

        Returns:
            Texto transcrito

        Raises:
            FileNotFoundError: Si el archivo no existe
            Exception: Si falla la transcripción
        """
        start_time = datetime.now()

        # Validar que el archivo existe
        if not os.path.exists(audio_path):
            logger.error(f"Archivo no encontrado: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Usar idioma configurado si no se especifica
        lang = language or self.language

        try:
            logger.info(f"Transcribiendo: {audio_path}")

            # Transcribir
            segments, info = self.model.transcribe(
                audio_path,
                language=lang,
                beam_size=beam_size,
                vad_filter=vad_filter,
                word_timestamps=False
            )

            # Consolidar segmentos
            transcription = " ".join([segment.text for segment in segments])
            transcription = transcription.strip()

            # Métricas
            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats["total_transcriptions"] += 1
            self.stats["total_duration_seconds"] += elapsed
            self.stats["average_transcription_time"] = (
                self.stats["total_duration_seconds"] / self.stats["total_transcriptions"]
            )

            logger.info(
                f"✅ Transcripción completada en {elapsed:.2f}s | "
                f"Idioma detectado: {info.language} | "
                f"Longitud: {len(transcription)} caracteres"
            )

            return transcription

        except Exception as e:
            self.stats["total_errors"] += 1
            logger.error(f"❌ Error transcribiendo {audio_path}: {e}")
            raise

    def transcribe_with_metadata(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe y retorna metadata detallada.

        Returns:
            Dict con:
                - text: Transcripción
                - language: Idioma detectado
                - duration: Duración del audio en segundos
                - segments: Lista de segmentos con timestamps
        """
        start_time = datetime.now()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang = language or self.language

        try:
            # Transcribir con timestamps
            segments, info = self.model.transcribe(
                audio_path,
                language=lang,
                word_timestamps=True
            )

            # Procesar segmentos
            segments_list = []
            full_text = []

            for segment in segments:
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text.append(segment.text)

            transcription = " ".join(full_text).strip()

            # Construir resultado
            result = {
                "text": transcription,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": segments_list,
                "transcription_time": (datetime.now() - start_time).total_seconds()
            }

            logger.info(f"✅ Transcripción con metadata completada")
            return result

        except Exception as e:
            logger.error(f"❌ Error en transcripción con metadata: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        return self.stats.copy()

    def reset_stats(self):
        """Reinicia estadísticas"""
        self.stats = {
            "total_transcriptions": 0,
            "total_errors": 0,
            "total_duration_seconds": 0.0,
            "average_transcription_time": 0.0
        }
        logger.info("Estadísticas reiniciadas")


# === FUNCIONES DE UTILIDAD ===

def get_audio_duration(audio_path: str) -> float:
    """
    Obtiene la duración de un archivo de audio en segundos.

    Requiere ffprobe (parte de ffmpeg).
    """
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())

    except Exception as e:
        logger.warning(f"No se pudo obtener duración del audio: {e}")
        return 0.0


def convert_to_wav(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convierte un archivo de audio a formato WAV.

    Requiere ffmpeg instalado.

    Args:
        input_path: Path del archivo de entrada
        output_path: Path de salida (opcional, se genera automáticamente)

    Returns:
        Path del archivo WAV generado
    """
    import subprocess

    if output_path is None:
        base_name = Path(input_path).stem
        output_path = f"/tmp/{base_name}.wav"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i", input_path,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                output_path
            ],
            capture_output=True,
            check=True
        )
        logger.info(f"✅ Convertido a WAV: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"❌ Error convirtiendo a WAV: {e}")
        raise


# === EJEMPLO DE USO ===

async def test_transcriber():
    """Test del transcriptor de audio"""

    # Inicializar
    transcriber = AudioTranscriber(
        model_size="base",
        device="cpu",
        language="es"
    )

    # Crear audio de prueba (requiere librería TTS, opcional)
    print("\n=== Test AudioTranscriber ===\n")

    # Si tienes un archivo de prueba:
    # audio_path = "/path/to/audio.ogg"
    # transcription = transcriber.transcribe(audio_path)
    # print(f"Transcripción: {transcription}")

    # Estadísticas
    stats = transcriber.get_stats()
    print(f"\nEstadísticas:")
    print(f"  Total transcripciones: {stats['total_transcriptions']}")
    print(f"  Errores: {stats['total_errors']}")
    print(f"  Tiempo promedio: {stats['average_transcription_time']:.2f}s")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_transcriber())
