#!/usr/bin/env python3
"""
backblaze_b2.py

Cliente S3-compatible para Backblaze B2.
Maneja uploads, downloads, y generación de URLs firmadas para contenido.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

logger = logging.getLogger(__name__)


class BackblazeB2Client:
    """
    Cliente para Backblaze B2 usando la API S3-compatible.
    
    Uso:
        client = BackblazeB2Client(
            endpoint_url="https://s3.us-west-004.backblazeb2.com",
            key_id="your_key_id",
            application_key="your_application_key",
            bucket_name="lola-content"
        )
        
        # Upload archivo
        url = await client.upload_file("local.jpg", "remote/path.jpg")
        
        # Generar URL firmada (30 min por defecto)
        signed_url = client.get_presigned_url("remote/path.jpg", expiration=1800)
    """

    def __init__(
        self,
        endpoint_url: str,
        key_id: str,
        application_key: str,
        bucket_name: str
    ):
        """
        Inicializa el cliente de Backblaze B2.
        
        Args:
            endpoint_url: URL del endpoint S3 de B2 (ej: https://s3.us-west-004.backblazeb2.com)
            key_id: Application Key ID de B2
            application_key: Application Key de B2
            bucket_name: Nombre del bucket
        """
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        
        # Configuración para timeouts y retries
        config = Config(
            connect_timeout=10,
            read_timeout=30,
            retries={'max_attempts': 3}
        )
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=key_id,
                aws_secret_access_key=application_key,
                config=config
            )
            logger.info(f"✅ BackblazeB2Client inicializado para bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("❌ Error: Credenciales de B2 no proporcionadas")
            raise
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente B2: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        object_key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Sube un archivo local al bucket de B2.
        
        Args:
            file_path: Ruta local del archivo a subir
            object_key: Key/path en el bucket (ej: "products/image.jpg")
            content_type: MIME type del archivo (auto-detectado si no se proporciona)
            
        Returns:
            URL del objeto subido o None si falla
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            # Construir URL del objeto
            object_url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            
            logger.info(f"✅ Archivo subido: {object_key}")
            return object_url
            
        except ClientError as e:
            logger.error(f"❌ Error subiendo archivo a B2: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"❌ Archivo no encontrado: {file_path}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado en upload: {e}")
            return None

    def upload_file_obj(
        self,
        file_obj,
        object_key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Sube un objeto de archivo (file-like object) al bucket de B2.
        
        Args:
            file_obj: Objeto de archivo (ej: BytesIO, archivo abierto)
            object_key: Key/path en el bucket
            content_type: MIME type del archivo
            
        Returns:
            URL del objeto subido o None si falla
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            object_url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            
            logger.info(f"✅ Archivo (objeto) subido: {object_key}")
            return object_url
            
        except ClientError as e:
            logger.error(f"❌ Error subiendo file object a B2: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado en upload_file_obj: {e}")
            return None

    def get_presigned_url(
        self,
        object_key: str,
        expiration: int = 1800
    ) -> Optional[str]:
        """
        Genera una URL firmada para acceso temporal al objeto.
        
        Args:
            object_key: Key del objeto en el bucket
            expiration: Tiempo de expiración en segundos (default: 1800 = 30 min)
            
        Returns:
            URL firmada o None si falla
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            
            logger.debug(f"✅ URL firmada generada para: {object_key} (expira en {expiration}s)")
            return url
            
        except ClientError as e:
            logger.error(f"❌ Error generando URL firmada: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado en get_presigned_url: {e}")
            return None

    def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Lista archivos en el bucket, opcionalmente filtrados por prefijo.
        
        Args:
            prefix: Prefijo para filtrar archivos (ej: "products/")
            max_keys: Número máximo de resultados
            
        Returns:
            Lista de diccionarios con info de archivos
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            if prefix:
                params['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**params)
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag']
                })
            
            logger.info(f"✅ {len(files)} archivos listados (prefix: {prefix or 'ninguno'})")
            return files
            
        except ClientError as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado en list_files: {e}")
            return []

    def delete_file(self, object_key: str) -> bool:
        """
        Elimina un archivo del bucket.
        
        Args:
            object_key: Key del objeto a eliminar
            
        Returns:
            True si se eliminó exitosamente, False si falló
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"✅ Archivo eliminado: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error eliminando archivo: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado en delete_file: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """
        Verifica si un archivo existe en el bucket.
        
        Args:
            object_key: Key del objeto a verificar
            
        Returns:
            True si existe, False si no existe o hay error
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"❌ Error verificando existencia: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado en file_exists: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la conectividad con Backblaze B2.
        
        Returns:
            Diccionario con estado de salud
        """
        try:
            # Intentar listar con max_keys=1 para verificar conexión
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            
            return {
                "status": "healthy",
                "bucket": self.bucket_name,
                "endpoint": self.endpoint_url,
                "timestamp": datetime.now().isoformat()
            }
            
        except ClientError as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "bucket": self.bucket_name,
                "endpoint": self.endpoint_url,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def get_b2_client_from_env() -> BackblazeB2Client:
    """
    Factory function para crear cliente B2 desde variables de entorno.
    
    Variables requeridas:
        B2_ENDPOINT_URL
        B2_KEY_ID
        B2_APPLICATION_KEY
        B2_BUCKET_NAME
        
    Returns:
        Instancia configurada de BackblazeB2Client
        
    Raises:
        ValueError si faltan variables de entorno
    """
    endpoint_url = os.getenv("B2_ENDPOINT_URL")
    key_id = os.getenv("B2_KEY_ID")
    application_key = os.getenv("B2_APPLICATION_KEY")
    bucket_name = os.getenv("B2_BUCKET_NAME")
    
    missing = []
    if not endpoint_url:
        missing.append("B2_ENDPOINT_URL")
    if not key_id:
        missing.append("B2_KEY_ID")
    if not application_key:
        missing.append("B2_APPLICATION_KEY")
    if not bucket_name:
        missing.append("B2_BUCKET_NAME")
    
    if missing:
        raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
    
    return BackblazeB2Client(
        endpoint_url=endpoint_url,
        key_id=key_id,
        application_key=application_key,
        bucket_name=bucket_name
    )
