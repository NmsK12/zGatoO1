#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database PostgreSQL - WolfData Dox
Manejo de base de datos PostgreSQL para API Keys
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        if not DATABASE_URL:
            raise Exception("DATABASE_URL no está configurada")
        
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a PostgreSQL: {e}")
        raise

def init_database():
    """Inicializar la base de datos y crear tablas si no existen"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Crear tabla api_keys si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(255) DEFAULT 'zGatoO',
                time_remaining INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Base de datos PostgreSQL inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise

def validate_api_key(api_key):
    """Validar si una API key es válida y no ha expirado"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT key, expires_at, is_active, time_remaining
            FROM api_keys 
            WHERE key = %s AND is_active = true
        """, (api_key,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return False, "API Key no encontrada o inactiva"
        
        # Verificar si ha expirado
        from datetime import datetime
        now = datetime.now()
        expires_at = result['expires_at']
        
        if now > expires_at:
            return False, "API Key expirada"
        
        return True, "API Key válida"
        
    except Exception as e:
        logger.error(f"Error validando API key: {e}")
        return False, f"Error interno: {str(e)}"

def update_last_used(api_key):
    """Actualizar timestamp de último uso de la API key"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys 
            SET last_used = CURRENT_TIMESTAMP 
            WHERE key = %s
        """, (api_key,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error actualizando último uso: {e}")

def get_api_key_info(api_key):
    """Obtener información de una API key"""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT key, expires_at, description, created_at, created_by, 
                   time_remaining, last_used, is_active
            FROM api_keys 
            WHERE key = %s
        """, (api_key,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo información de API key: {e}")
        return None
