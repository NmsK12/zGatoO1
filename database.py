#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database SQLite - WolfData Dox
Manejo de base de datos SQLite para API Keys (fallback)
"""

import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def init_database():
    """Inicializar la base de datos SQLite"""
    try:
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        
        # Crear tabla api_keys si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'zGatoO',
                time_remaining INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Base de datos SQLite inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos SQLite: {e}")
        raise

def validate_api_key(api_key):
    """Validar si una API key es válida y no ha expirado"""
    try:
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, expires_at, is_active, time_remaining
            FROM api_keys 
            WHERE key = ? AND is_active = 1
        """, (api_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "API Key no encontrada o inactiva"
        
        # Verificar si ha expirado
        now = datetime.now()
        expires_at = datetime.fromisoformat(result[1])
        
        if now > expires_at:
            return False, "API Key expirada"
        
        return True, "API Key válida"
        
    except Exception as e:
        logger.error(f"Error validando API key: {e}")
        return False, f"Error interno: {str(e)}"

def update_last_used(api_key):
    """Actualizar timestamp de último uso de la API key"""
    try:
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys 
            SET last_used = CURRENT_TIMESTAMP 
            WHERE key = ?
        """, (api_key,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error actualizando último uso: {e}")

def get_api_key_info(api_key):
    """Obtener información de una API key"""
    try:
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, expires_at, description, created_at, created_by, 
                   time_remaining, last_used, is_active
            FROM api_keys 
            WHERE key = ?
        """, (api_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo información de API key: {e}")
        return None
