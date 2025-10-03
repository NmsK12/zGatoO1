#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Key - WolfData Dox
Generador de API Keys para el servidor DNI
"""

import secrets
import string
import hashlib
from datetime import datetime, timedelta

def generate_api_key(length=32):
    """Generar una API key segura"""
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return hashlib.md5(key.encode()).hexdigest()

def create_test_key():
    """Crear una API key de prueba"""
    key = generate_api_key()
    expires_at = datetime.now() + timedelta(hours=24)  # 24 horas de duración
    
    print(f"API Key generada: {key}")
    print(f"Expira en: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return key, expires_at

if __name__ == "__main__":
    create_test_key()
