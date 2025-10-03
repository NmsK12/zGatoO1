#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API DNI - WolfData Dox
API simple para consultas de DNI con foto en base64
"""

import asyncio
import base64
import json
import logging
import os
import re
import time
import threading
from datetime import datetime, timedelta
from io import BytesIO

from flask import Flask, jsonify, request, send_file, make_response
from PIL import Image
from database_postgres import validate_api_key, init_database, register_api_key, delete_api_key
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaPhoto

# Configuración
import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Variables globales
client = None
loop = None

# La función validate_api_key ahora se importa desde database_postgres

def parse_dni_response(text):
    """Parsea la respuesta del bot y extrae los datos del DNI."""
    data = {}
    
    # Limpiar el texto de caracteres especiales de Markdown
    clean_text = text.replace('**', '').replace('`', '').replace('*', '')
    
    # Extraer DNI
    dni_match = re.search(r'DNI\s*[➾\-=]\s*(\d+)', clean_text)
    if dni_match:
        data['DNI'] = dni_match.group(1)
    
    # Extraer nombres
    nombres_match = re.search(r'NOMBRES\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if nombres_match:
        data['NOMBRES'] = nombres_match.group(1).strip()
    
    # Extraer apellidos
    apellidos_match = re.search(r'APELLIDOS\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if apellidos_match:
        data['APELLIDOS'] = apellidos_match.group(1).strip()
    
    # Extraer género
    genero_match = re.search(r'GENERO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if genero_match:
        data['GENERO'] = genero_match.group(1).strip()
    
    # Extraer fecha de nacimiento
    fecha_nac_match = re.search(r'FECHA\s*NACIMIENTO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_nac_match:
        data['FECHA_NACIMIENTO'] = fecha_nac_match.group(1).strip()
    
    # Extraer edad
    edad_match = re.search(r'EDAD\s*[➾\-=]\s*(\d+)\s*AÑOS?', clean_text)
    if edad_match:
        data['EDAD'] = f"{edad_match.group(1)} AÑOS"
    
    # Extraer departamento
    dept_match = re.search(r'DEPARTAMENTO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if dept_match:
        data['DEPARTAMENTO'] = dept_match.group(1).strip()
    
    # Extraer provincia
    prov_match = re.search(r'PROVINCIA\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if prov_match:
        data['PROVINCIA'] = prov_match.group(1).strip()
    
    # Extraer distrito
    dist_match = re.search(r'DISTRITO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if dist_match:
        data['DISTRITO'] = dist_match.group(1).strip()
    
    # Extraer nivel educativo
    nivel_match = re.search(r'NIVEL\s*EDUCATIVO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if nivel_match:
        data['NIVEL_EDUCATIVO'] = nivel_match.group(1).strip()
    
    # Extraer estado civil
    estado_match = re.search(r'ESTADO\s*CIVIL\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if estado_match:
        data['ESTADO_CIVIL'] = estado_match.group(1).strip()
    
    # Extraer estatura
    estatura_match = re.search(r'ESTATURA\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if estatura_match:
        data['ESTATURA'] = estatura_match.group(1).strip()
    
    # Extraer fecha de inscripción
    inscripcion_match = re.search(r'FECHA\s*INSCRIPCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if inscripcion_match:
        data['FECHA_INSCRIPCION'] = inscripcion_match.group(1).strip()
    
    # Extraer fecha de emisión
    emision_match = re.search(r'FECHA\s*EMISION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if emision_match:
        data['FECHA_EMISION'] = emision_match.group(1).strip()
    
    # Extraer fecha de caducidad
    caducidad_match = re.search(r'FECHA\s*CADUCIDAD\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if caducidad_match:
        data['FECHA_CADUCIDAD'] = caducidad_match.group(1).strip()
    
    # Extraer donante de órganos
    donante_match = re.search(r'DONANTE\s*ORGANOS\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if donante_match:
        data['DONANTE_ORGANOS'] = donante_match.group(1).strip()
    
    # Extraer padre
    padre_match = re.search(r'PADRE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if padre_match:
        data['PADRE'] = padre_match.group(1).strip()
    
    # Extraer madre
    madre_match = re.search(r'MADRE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if madre_match:
        data['MADRE'] = madre_match.group(1).strip()
    
    # Extraer restricción
    restriccion_match = re.search(r'RESTRICCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if restriccion_match:
        data['RESTRICCION'] = restriccion_match.group(1).strip()
    
    # Extraer dirección
    direccion_match = re.search(r'DIRECCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if direccion_match:
        data['DIRECCION'] = direccion_match.group(1).strip()
    
    # Extraer UBIGEO RENIEC
    ubigeo_reniec_match = re.search(r'UBIGEO\s*RENIEC\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_reniec_match:
        data['UBIGEO_RENIEC'] = ubigeo_reniec_match.group(1).strip()
    
    # Extraer UBIGEO INE
    ubigeo_ine_match = re.search(r'UBIGEO\s*INE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_ine_match:
        data['UBIGEO_INE'] = ubigeo_ine_match.group(1).strip()
    
    # Extraer UBIGEO SUNAT
    ubigeo_sunat_match = re.search(r'UBIGEO\s*SUNAT\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_sunat_match:
        data['UBIGEO_SUNAT'] = ubigeo_sunat_match.group(1).strip()
    
    return data

def parse_dnit_response(text):
    """Parsea la respuesta del bot para extraer datos detallados del DNI (comando /dnit)."""
    data = {}
    
    # Limpiar el texto de caracteres especiales
    clean_text = text.replace('**', '').replace('`', '').replace('*', '')
    
    # Información básica
    dni_match = re.search(r'DNI\s*[➾\-=]\s*(\d+)', clean_text)
    if dni_match:
        data['DNI'] = dni_match.group(1)
    
    nombres_match = re.search(r'NOMBRES\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if nombres_match:
        data['NOMBRES'] = nombres_match.group(1).strip()
    
    apellidos_match = re.search(r'APELLIDOS\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if apellidos_match:
        data['APELLIDOS'] = apellidos_match.group(1).strip()
    
    genero_match = re.search(r'GENERO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if genero_match:
        data['GENERO'] = genero_match.group(1).strip()
    
    # Información de nacimiento
    fecha_nacimiento_match = re.search(r'FECHA NACIMIENTO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_nacimiento_match:
        data['FECHA_NACIMIENTO'] = fecha_nacimiento_match.group(1).strip()
    
    edad_match = re.search(r'EDAD\s*[➾\-=]\s*(\d+)\s*AÑOS?', clean_text)
    if edad_match:
        data['EDAD'] = f"{edad_match.group(1)} AÑOS"
    
    departamento_match = re.search(r'DEPARTAMENTO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if departamento_match:
        data['DEPARTAMENTO'] = departamento_match.group(1).strip()
    
    provincia_match = re.search(r'PROVINCIA\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if provincia_match:
        data['PROVINCIA'] = provincia_match.group(1).strip()
    
    distrito_match = re.search(r'DISTRITO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if distrito_match:
        data['DISTRITO'] = distrito_match.group(1).strip()
    
    # Información general
    nivel_educativo_match = re.search(r'NIVEL EDUCATIVO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if nivel_educativo_match:
        data['NIVEL_EDUCATIVO'] = nivel_educativo_match.group(1).strip()
    
    estado_civil_match = re.search(r'ESTADO CIVIL\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if estado_civil_match:
        data['ESTADO_CIVIL'] = estado_civil_match.group(1).strip()
    
    estatura_match = re.search(r'ESTATURA\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if estatura_match:
        data['ESTATURA'] = estatura_match.group(1).strip()
    
    fecha_inscripcion_match = re.search(r'FECHA INSCRIPCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_inscripcion_match:
        data['FECHA_INSCRIPCION'] = fecha_inscripcion_match.group(1).strip()
    
    fecha_emision_match = re.search(r'FECHA EMISION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_emision_match:
        data['FECHA_EMISION'] = fecha_emision_match.group(1).strip()
    
    fecha_caducidad_match = re.search(r'FECHA CADUCIDAD\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_caducidad_match:
        data['FECHA_CADUCIDAD'] = fecha_caducidad_match.group(1).strip()
    
    donante_organos_match = re.search(r'DONANTE ORGANOS\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if donante_organos_match:
        data['DONANTE_ORGANOS'] = donante_organos_match.group(1).strip()
    
    padre_match = re.search(r'PADRE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if padre_match:
        data['PADRE'] = padre_match.group(1).strip()
    
    madre_match = re.search(r'MADRE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if madre_match:
        data['MADRE'] = madre_match.group(1).strip()
    
    restriccion_match = re.search(r'RESTRICCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if restriccion_match:
        data['RESTRICCION'] = restriccion_match.group(1).strip()
    
    # Domicilio
    direccion_match = re.search(r'DIRECCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if direccion_match:
        data['DIRECCION'] = direccion_match.group(1).strip()
    
    # Ubigeos
    ubigeo_reneic_match = re.search(r'UBIGEO RENIEC\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_reneic_match:
        data['UBIGEO_RENIEC'] = ubigeo_reneic_match.group(1).strip()
    
    ubigeo_ine_match = re.search(r'UBIGEO INE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_ine_match:
        data['UBIGEO_INE'] = ubigeo_ine_match.group(1).strip()
    
    ubigeo_sunat_match = re.search(r'UBIGEO SUNAT\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_sunat_match:
        data['UBIGEO_SUNAT'] = ubigeo_sunat_match.group(1).strip()
    
    return data

def parse_antecedentes_response(text, tipo):
    """Parsea la respuesta de antecedentes (penales, policiales, judiciales)."""
    data = {}
    
    # Limpiar el texto de caracteres especiales
    clean_text = text.replace('**', '').replace('`', '').replace('*', '')
    
    # Extraer DNI
    dni_match = re.search(r'DNI\s*[➾\-=]\s*(\d+)', clean_text)
    if dni_match:
        data['DNI'] = dni_match.group(1)
    
    # Extraer nombres
    nombres_match = re.search(r'NOMBRES\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if nombres_match:
        data['NOMBRES'] = nombres_match.group(1).strip()
    
    # Extraer apellidos
    apellidos_match = re.search(r'APELLIDOS\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if apellidos_match:
        data['APELLIDOS'] = apellidos_match.group(1).strip()
    
    # Extraer género
    genero_match = re.search(r'GENERO\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if genero_match:
        data['GENERO'] = genero_match.group(1).strip()
    
    # Extraer edad
    edad_match = re.search(r'EDAD\s*[➾\-=]\s*(\d+)', clean_text)
    if edad_match:
        data['EDAD'] = edad_match.group(1)
    
    # Agregar tipo de certificado
    data['TIPO_CERTIFICADO'] = tipo
    
    return data

def consult_dni_sync(dni_number):
    """Consulta el DNI usando Telethon de forma síncrona."""
    global client, loop
    
    try:
        # Verificar que el cliente esté disponible
        if not client or not loop:
            logger.error("Cliente de Telethon no está disponible")
            return {
                'success': False,
                'error': 'Cliente de Telegram no disponible. Intenta nuevamente en unos segundos.'
            }
    
        # Ejecutar la consulta asíncrona en el loop existente
        future = asyncio.run_coroutine_threadsafe(consult_dni_async(dni_number), loop)
        result = future.result(timeout=35)  # 35 segundos de timeout
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout consultando DNI {dni_number}")
        return {
            'success': False,
            'error': 'Timeout: No se recibió respuesta en 35 segundos'
        }
    except Exception as e:
        logger.error(f"Error consultando DNI {dni_number}: {str(e)}")
        # Si es un error de Constructor ID, intentar reiniciar la sesión
        if "Constructor ID" in str(e) or "8f97c628" in str(e):
            logger.error("Error de Constructor ID detectado - versión de Telethon incompatible")
            logger.info("Intentando reiniciar sesión...")
            restart_telethon()
            return {
                'success': False,
                'error': 'Error de compatibilidad detectado. Intenta nuevamente en unos segundos.'
            }
        
        # Si es un error de sesión usada en múltiples IPs
        if "authorization key" in str(e) and "two different IP addresses" in str(e):
            logger.error("Sesión usada en múltiples IPs. Detén el proceso local y usa solo en contenedor.")
            return {
                'success': False,
                'error': 'Sesión en conflicto. Detén el proceso local y usa solo en contenedor.'
            }
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

def consult_dnit_sync(dni_number):
    """Consulta el DNI detallado usando Telethon de forma síncrona."""
    global client, loop
    
    if not client:
        return {
            'success': False,
            'error': 'Cliente de Telegram no inicializado'
        }
    
    try:
        # Ejecutar la consulta asíncrona en el loop existente
        future = asyncio.run_coroutine_threadsafe(consult_dnit_async(dni_number), loop)
        result = future.result(timeout=35)  # 35 segundos de timeout
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout consultando DNI detallado {dni_number}")
        return {
            'success': False,
            'error': 'Timeout: No se recibió respuesta en 35 segundos'
        }
    except Exception as e:
        logger.error(f"Error consultando DNI detallado {dni_number}: {str(e)}")
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

def consult_antecedentes_sync(dni_number, tipo):
    """Consulta antecedentes usando Telethon de forma síncrona."""
    global client, loop
    
    try:
        # Verificar que el cliente esté disponible
        if not client or not loop:
            logger.error("Cliente de Telethon no está disponible")
            return {
                'success': False,
                'error': 'Cliente de Telegram no disponible. Intenta nuevamente en unos segundos.'
            }
        
        # Ejecutar la consulta asíncrona en el loop existente
        future = asyncio.run_coroutine_threadsafe(consult_antecedentes_async(dni_number, tipo), loop)
        result = future.result(timeout=35)  # 35 segundos de timeout
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout consultando {tipo.upper()} DNI {dni_number}")
        return {
            'success': False,
            'error': 'Timeout: No se recibió respuesta en 35 segundos'
        }
    except Exception as e:
        logger.error(f"Error consultando {tipo.upper()} DNI {dni_number}: {str(e)}")
        # Si es un error de Constructor ID, intentar reiniciar la sesión
        if "Constructor ID" in str(e) or "8f97c628" in str(e):
            logger.error("Error de Constructor ID detectado - versión de Telethon incompatible")
            logger.info("Intentando reiniciar sesión...")
            restart_telethon()
            return {
                'success': False,
                'error': 'Error de compatibilidad detectado. Intenta nuevamente en unos segundos.'
            }
        
        # Si es un error de sesión usada en múltiples IPs
        if "authorization key" in str(e) and "two different IP addresses" in str(e):
            logger.error("Sesión usada en múltiples IPs. Detén el proceso local y usa solo en contenedor.")
            return {
                'success': False,
                'error': 'Sesión en conflicto. Detén el proceso local y usa solo en contenedor.'
            }
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

async def consult_dni_async(dni_number):
    """Consulta asíncrona del DNI con manejo inteligente de colas."""
    global client
    
    try:
        max_attempts = 3  # Máximo 3 intentos
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Intento {attempt}/{max_attempts} para DNI {dni_number}")
            
            # Enviar comando al bot objetivo
            await client.send_message(config.TARGET_BOT, f"/dni {dni_number}")
            logger.info(f"Comando enviado correctamente (intento {attempt})")
            
            # Esperar respuesta (máximo 20 segundos por intento)
            start_time = time.time()
            processing_detected = False
            wait_detected = False
            wait_seconds = 0
            last_message_id = 0  # Para rastrear mensajes nuevos
            
            while time.time() - start_time < 20:
                # Obtener mensajes recientes (solo los nuevos)
                messages = await client.get_messages(config.TARGET_BOT, limit=5)
                
                # Filtrar solo mensajes nuevos y que contengan nuestro DNI
                new_messages = []
                for message in messages:
                    if message.id > last_message_id and message.text and dni_number in message.text:
                        new_messages.append(message)
                        last_message_id = max(last_message_id, message.id)
                
                if new_messages:
                    logger.info(f"Revisando {len(new_messages)} mensajes nuevos para DNI {dni_number}...")
                
                for message in new_messages:
                    logger.info(f"Mensaje nuevo: {message.text[:100]}...")
                    
                    # Detectar mensaje de espera/cola/anti-spam (más específico)
                    wait_patterns = [
                        r'anti-spam.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'por favor.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'⏱️.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'espera\s+(\d+\.?\d*)\s*segundos?'
                    ]
                    
                    for pattern in wait_patterns:
                        wait_match = re.search(pattern, message.text.lower())
                        if wait_match:
                            wait_seconds = float(wait_match.group(1))
                            # Limitar espera máxima a 30 segundos
                            if wait_seconds > 30:
                                wait_seconds = 30
                            if not wait_detected:
                                logger.info(f"¡Mensaje de espera detectado! Esperando {wait_seconds} segundos...")
                                wait_detected = True
                            break
                    
                    if wait_detected:
                        continue
                    
                    # Detectar mensaje de procesamiento
                    if "procesando" in message.text.lower() or "⏳" in message.text or "un momento" in message.text.lower():
                        if not processing_detected:
                            logger.info("¡Mensaje de procesamiento detectado! Esperando respuesta final...")
                            processing_detected = True
                        continue
                    
                    # Ignorar nuestros propios comandos
                    if message.text.strip() == f"/dni {dni_number}":
                        continue
                    
                    # Buscar respuesta específica para este DNI
                    if (f"DNI ➾ {dni_number}" in message.text or 
                        f"DNI = {dni_number}" in message.text or
                        f"DNI: {dni_number}" in message.text or
                        (dni_number in message.text and "NOMBRES" in message.text and "APELLIDOS" in message.text)):
                        
                        logger.info(f"¡Respuesta encontrada para DNI {dni_number}!")
                        logger.info(f"Texto completo: {message.text}")
                        
                        # Encontramos la respuesta
                        text_data = message.text
                        photo_data = None
                        
                        # Verificar si hay foto
                        if message.media and isinstance(message.media, MessageMediaPhoto):
                            logger.info("Descargando foto...")
                            # Descargar la foto
                            photo_bytes = await client.download_media(message.media, file=BytesIO())
                            photo_data = base64.b64encode(photo_bytes.getvalue()).decode('utf-8')
                            logger.info("Foto descargada y convertida a base64")
                        
                        parsed_data = parse_dni_response(text_data)
                        logger.info(f"Datos parseados: {parsed_data}")
                        
                        return {
                            'success': True,
                            'text_data': text_data,
                            'photo_data': photo_data,
                            'parsed_data': parsed_data
                        }
                
                await asyncio.sleep(1)  # Esperar 1 segundo entre verificaciones (más rápido)
            
            # Si detectamos espera, esperar y reintentar
            if wait_detected and wait_seconds > 0:
                logger.info(f"Esperando {wait_seconds} segundos antes del siguiente intento...")
                await asyncio.sleep(wait_seconds + 1)  # Esperar un poco más para estar seguros
                continue
            
            # Si no detectamos espera pero no obtuvimos respuesta, esperar un poco y reintentar
            if not wait_detected and not processing_detected:
                logger.warning(f"No se detectó respuesta en intento {attempt}. Esperando 3 segundos...")
                await asyncio.sleep(3)
                continue
        
        logger.warning(f"Timeout: No se recibió respuesta para DNI {dni_number} después de {max_attempts} intentos")
        return {
            'success': False,
            'error': f'Timeout: No se recibió respuesta después de {max_attempts} intentos'
        }
        
    except Exception as e:
        logger.error(f"Error consultando DNI {dni_number}: {str(e)}")
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

async def consult_dnit_async(dni_number):
    """Consulta asíncrona del DNI detallado con manejo inteligente de colas."""
    global client
    
    try:
        max_attempts = 3  # Máximo 3 intentos
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Intento {attempt}/{max_attempts} para DNI detallado {dni_number}")
            
            # Enviar comando /dnit
            await client.send_message(config.TARGET_BOT, f"/dnit {dni_number}")
            logger.info(f"Comando /dnit enviado correctamente (intento {attempt})")
            
            # Esperar un poco antes de revisar mensajes
            await asyncio.sleep(2)
            
            # Obtener mensajes recientes
            messages = await client.get_messages(config.TARGET_BOT, limit=10)
            current_timestamp = time.time()
            new_messages = [msg for msg in messages if msg.date.timestamp() > current_timestamp - 60]
            
            logger.info(f"Revisando {len(new_messages)} mensajes nuevos para DNI detallado {dni_number}...")
            
            for message in new_messages:
                logger.info(f"Mensaje nuevo: {message.text[:100]}...")
                logger.info(f"Texto limpio: {message.text.replace('`', '').replace('*', '').replace('**', '')[:100]}...")
                
                # Buscar mensajes de espera/procesamiento
                if "espera" in message.text.lower() and "segundos" in message.text.lower():
                    wait_match = re.search(r'(\d+)\s*segundos?', message.text)
                    if wait_match:
                        wait_time = int(wait_match.group(1))
                        logger.info(f"Esperando {wait_time} segundos...")
                        await asyncio.sleep(wait_time)
                        continue
                
                # Buscar respuesta específica para DNI detallado
                clean_message = message.text.replace('`', '').replace('*', '').replace('**', '')
                if (f"DNI ➾ {dni_number}" in clean_message and 
                    ("RENIEC ONLINE" in clean_message or "OLIMPO_BOT" in clean_message)):
                    
                    logger.info(f"¡Respuesta encontrada para DNI detallado {dni_number}!")
                    logger.info(f"Texto completo: {message.text}")
                    
                    # Encontramos la respuesta
                    text_data = message.text
                    images = []
                    
                    # Verificar si hay imágenes adjuntas
                    if message.media and hasattr(message.media, 'photo'):
                        logger.info("Descargando imágenes...")
                        # Descargar imagen en memoria
                        image_bytes = await client.download_media(message.media, file=BytesIO())
                        image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                        images.append({
                            'type': 'CARA',
                            'base64': image_base64
                        })
                        logger.info(f"Imagen de cara descargada: {len(image_base64)} caracteres")
                    
                    # Buscar más mensajes con imágenes (huellas y firma)
                    additional_messages = await client.get_messages(config.TARGET_BOT, limit=5, offset_id=message.id)
                    for additional_msg in additional_messages:
                        if additional_msg.media and hasattr(additional_msg.media, 'photo'):
                            logger.info("Descargando imagen adicional...")
                            image_bytes = await client.download_media(additional_msg.media, file=BytesIO())
                            image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                            
                            # Determinar tipo de imagen basado en el contexto
                            img_type = 'HUELLAS'  # Por defecto
                            if len(images) == 1:  # Segunda imagen
                                img_type = 'HUELLAS'
                            elif len(images) == 2:  # Tercera imagen
                                img_type = 'FIRMA'
                            elif len(images) == 3:  # Cuarta imagen (otra huella)
                                img_type = 'HUELLAS'
                            
                            images.append({
                                'type': img_type,
                                'base64': image_base64
                            })
                            logger.info(f"Imagen {img_type} descargada: {len(image_base64)} caracteres")
                    
                    parsed_data = parse_dnit_response(text_data)
                    logger.info(f"Datos parseados: {parsed_data}")
                    
                    return {
                        'success': True,
                        'text_data': text_data,
                        'images': images,
                        'parsed_data': parsed_data
                    }
            
            # Si no se encontró respuesta, esperar antes del siguiente intento
            if attempt < max_attempts:
                logger.warning(f"No se detectó respuesta en intento {attempt}. Esperando 3 segundos...")
                await asyncio.sleep(3)
        
        logger.error(f"Timeout consultando DNI detallado {dni_number}")
        return {
            'success': False,
            'error': 'Timeout: No se recibió respuesta después de 3 intentos'
        }
        
    except Exception as e:
        logger.error(f"Error consultando DNI detallado {dni_number}: {str(e)}")
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

async def consult_antecedentes_async(dni_number, tipo):
    """Consulta asíncrona de antecedentes (penales, policiales, judiciales)."""
    global client
    
    try:
        max_attempts = 3  # Máximo 3 intentos
        attempt = 0
        
        # Mapear tipos a comandos
        comandos = {
            'penales': '/antpen',
            'policiales': '/antpol', 
            'judiciales': '/antjud'
        }
        
        comando = comandos.get(tipo)
        if not comando:
            return {
                'success': False,
                'error': f'Tipo de antecedentes no válido: {tipo}'
            }
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Intento {attempt}/{max_attempts} para {tipo.upper()} DNI {dni_number}")
            
            # Enviar comando al bot objetivo
            await client.send_message(config.TARGET_BOT, f"{comando} {dni_number}")
            logger.info(f"Comando {comando} enviado correctamente (intento {attempt})")
            
            # Esperar respuesta (máximo 20 segundos por intento)
            start_time = time.time()
            processing_detected = False
            wait_detected = False
            wait_seconds = 0
            last_message_id = 0  # Para rastrear mensajes nuevos
            
            while time.time() - start_time < 20:
                # Obtener mensajes recientes (solo los nuevos)
                messages = await client.get_messages(config.TARGET_BOT, limit=5)
                
                # Filtrar solo mensajes nuevos y que contengan nuestro DNI
                new_messages = []
                for message in messages:
                    if message.id > last_message_id and message.text and dni_number in message.text:
                        new_messages.append(message)
                        last_message_id = max(last_message_id, message.id)
                
                if new_messages:
                    logger.info(f"Revisando {len(new_messages)} mensajes nuevos para {tipo.upper()} DNI {dni_number}...")
                
                for message in new_messages:
                    logger.info(f"Mensaje nuevo: {message.text[:100]}...")
                    logger.info(f"Texto limpio: {message.text.replace('`', '').replace('*', '').replace('**', '')[:100]}...")
                    
                    # Detectar mensaje de espera/cola/anti-spam
                    wait_patterns = [
                        r'anti-spam.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'por favor.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'⏱️.*?espera\s+(\d+\.?\d*)\s*[sS]',
                        r'espera\s+(\d+\.?\d*)\s*segundos?'
                    ]
                    
                    for pattern in wait_patterns:
                        wait_match = re.search(pattern, message.text.lower())
                        if wait_match:
                            wait_seconds = float(wait_match.group(1))
                            if wait_seconds > 30:
                                wait_seconds = 30
                            if not wait_detected:
                                logger.info(f"¡Mensaje de espera detectado! Esperando {wait_seconds} segundos...")
                                wait_detected = True
                            break
                    
                    if wait_detected:
                        continue
                    
                    # Detectar mensaje de procesamiento
                    if "procesando" in message.text.lower() or "⏳" in message.text or "un momento" in message.text.lower():
                        if not processing_detected:
                            logger.info("¡Mensaje de procesamiento detectado! Esperando respuesta final...")
                            processing_detected = True
                        continue
                    
                    # Ignorar nuestros propios comandos
                    if message.text.strip() == f"{comando} {dni_number}":
                        continue
                    
                    # Buscar respuesta específica para antecedentes
                    # Limpiar el texto para comparación
                    clean_message = message.text.replace('`', '').replace('*', '').replace('**', '')
                    if (f"DNI ➾ {dni_number}" in clean_message and 
                        ("CERTIFICADO" in clean_message or "ANTECEDENTES" in clean_message or "OLIMPO_BOT" in clean_message)):
                        
                        logger.info(f"¡Respuesta encontrada para {tipo.upper()} DNI {dni_number}!")
                        logger.info(f"Texto completo: {message.text}")
                        
                        # Encontramos la respuesta
                        text_data = message.text
                        pdf_data = None
                        
                        # Verificar si hay PDF adjunto
                        pdf_data = None
                        if message.media and hasattr(message.media, 'document'):
                            logger.info("Descargando PDF...")
                            # Descargar el PDF en memoria
                            pdf_bytes = await client.download_media(message.media, file=BytesIO())
                            pdf_data = pdf_bytes.getvalue()
                            logger.info(f"PDF descargado en memoria: {len(pdf_data)} bytes")
                        else:
                            logger.info("No se detectó PDF adjunto en el mensaje")
                        
                        parsed_data = parse_antecedentes_response(text_data, tipo.upper())
                        logger.info(f"Datos parseados: {parsed_data}")
                        
                        return {
                            'success': True,
                            'text_data': text_data,
                            'pdf_data': pdf_data,
                            'parsed_data': parsed_data
                        }
                
                await asyncio.sleep(1)  # Esperar 1 segundo entre verificaciones
            
            # Si detectamos espera, esperar y reintentar
            if wait_detected and wait_seconds > 0:
                logger.info(f"Esperando {wait_seconds} segundos antes del siguiente intento...")
                await asyncio.sleep(wait_seconds + 1)
                continue
            
            # Si no detectamos espera pero no obtuvimos respuesta, esperar un poco y reintentar
            if not wait_detected and not processing_detected:
                logger.warning(f"No se detectó respuesta en intento {attempt}. Esperando 3 segundos...")
                await asyncio.sleep(3)
                continue
        
        logger.warning(f"Timeout: No se recibió respuesta para {tipo.upper()} DNI {dni_number} después de {max_attempts} intentos")
        return {
            'success': False,
            'error': f'Timeout: No se recibió respuesta después de {max_attempts} intentos'
        }
        
    except Exception as e:
        logger.error(f"Error consultando {tipo.upper()} DNI {dni_number}: {str(e)}")
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

@app.route('/dniresult', methods=['GET'])
def dni_result():
    """Endpoint para consultar DNI."""
    dni = request.args.get('dni')
    api_key = request.args.get('key')
    
    # Validar API key
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API Key requerida. Use: /dniresult?dni=12345678&key=TU_API_KEY'
        }), 401
    
    # Validar API key en base de datos
    validation = validate_api_key(api_key)
    if not validation['valid']:
        return jsonify({
            'success': False,
            'error': validation['error']
        }), 401
    
    if not dni:
        return jsonify({
            'success': False,
            'error': 'Parámetro DNI requerido. Use: /dniresult?dni=12345678&key=TU_API_KEY'
        }), 400
    
    # Verificar formato del DNI
    if not dni.isdigit() or len(dni) != 8:
            return jsonify({
                'success': False,
            'error': 'DNI debe ser un número de 8 dígitos'
            }), 400
        
    # Ejecutar consulta síncrona
    result = consult_dni_sync(dni)
        
    if result['success']:
        response = {
            'success': True,
            'dni': dni,
            'timestamp': datetime.now().isoformat()
        }
        
        # Agregar foto base64 primero si existe
        if result['photo_data']:
            response['photo_base64'] = f"data:image/jpeg;base64,{result['photo_data']}"
        
        # Agregar datos del DNI después
        response['data'] = result['parsed_data']
        
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500
            
@app.route('/dnit', methods=['GET'])
def dnit_result():
    """Endpoint para consultar DNI detallado."""
    dni = request.args.get('dni')
    
    if not dni:
        return jsonify({
            'success': False,
            'error': 'Parámetro DNI requerido. Use: /dnit?dni=12345678'
        }), 400
    
    # Verificar formato del DNI
    if not dni.isdigit() or len(dni) != 8:
        return jsonify({
            'success': False,
            'error': 'DNI debe ser un número de 8 dígitos'
        }), 400
    
    # Ejecutar consulta síncrona
    result = consult_dnit_sync(dni)
    
    if result['success']:
        response = {
            'success': True,
            'dni': dni,
            'timestamp': datetime.now().isoformat(),
            'data': result['parsed_data']
        }
        
        # Agregar imágenes si existen
        if result['images']:
            response['images'] = result['images']
        
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500

@app.route('/antpen', methods=['GET'])
def antpen_result():
    """Endpoint para consultar antecedentes penales."""
    dni = request.args.get('dni')
    
    if not dni:
            return jsonify({
                'success': False,
            'error': 'Parámetro DNI requerido. Use: /antpen?dni=12345678'
            }), 400
        
    # Verificar formato del DNI
    if not dni.isdigit() or len(dni) != 8:
            return jsonify({
                'success': False,
            'error': 'DNI debe ser un número de 8 dígitos'
            }), 400
        
    # Ejecutar consulta síncrona
    result = consult_antecedentes_sync(dni, 'penales')
    
    if result['success']:
        # Si hay PDF, devolver JSON con descarga automática
        if result['pdf_data']:
            # Crear respuesta JSON con PDF en base64 para descarga automática
            import base64
            pdf_base64 = base64.b64encode(result['pdf_data']).decode('utf-8')
            
            json_data = {
                'success': True,
                'dni': dni,
                'tipo': 'ANTECEDENTES_PENALES',
                'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data'],
                'pdf_base64': pdf_base64,
                'pdf_filename': f"antecedentes_penales_{dni}.pdf"
            }
            
            # Crear respuesta HTML completa con descarga automática
            response_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Antecedentes Penales - DNI {dni}</title>
                <meta charset="utf-8">
            </head>
            <body>
                <pre id="json-data">{json.dumps(json_data, indent=2, ensure_ascii=False)}</pre>
                <script>
                    // Descargar PDF automáticamente cuando la página cargue
                    window.onload = function() {{
                        const pdfData = '{pdf_base64}';
                        const pdfBlob = new Blob([Uint8Array.from(atob(pdfData), c => c.charCodeAt(0))], {{type: 'application/pdf'}});
                        const url = URL.createObjectURL(pdfBlob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'antecedentes_penales_{dni}.pdf';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }};
                </script>
            </body>
            </html>
            """
            
            return response_html
        else:
            # Si no hay PDF, devolver solo JSON
            response = {
                'success': True,
                'dni': dni,
                'tipo': 'ANTECEDENTES_PENALES',
                'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data']
            }
            return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500

@app.route('/antpol', methods=['GET'])
def antpol_result():
    """Endpoint para consultar antecedentes policiales."""
    dni = request.args.get('dni')
    
    if not dni:
        return jsonify({
            'success': False,
            'error': 'Parámetro DNI requerido. Use: /antpol?dni=12345678'
        }), 400
    
    # Verificar formato del DNI
    if not dni.isdigit() or len(dni) != 8:
        return jsonify({
            'success': False,
            'error': 'DNI debe ser un número de 8 dígitos'
        }), 400
    
    # Ejecutar consulta síncrona
    result = consult_antecedentes_sync(dni, 'policiales')
    
    if result['success']:
        # Si hay PDF, devolver JSON con descarga automática
        if result['pdf_data']:
            # Crear respuesta JSON con PDF en base64 para descarga automática
            import base64
            pdf_base64 = base64.b64encode(result['pdf_data']).decode('utf-8')
            
            json_data = {
                'success': True,
                'dni': dni,
                'tipo': 'ANTECEDENTES_POLICIALES',
                'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data'],
                'pdf_base64': pdf_base64,
                'pdf_filename': f"antecedentes_policiales_{dni}.pdf"
            }
            
            # Crear respuesta HTML completa con descarga automática
            response_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Antecedentes Policiales - DNI {dni}</title>
                <meta charset="utf-8">
            </head>
            <body>
                <pre id="json-data">{json.dumps(json_data, indent=2, ensure_ascii=False)}</pre>
                <script>
                    // Descargar PDF automáticamente cuando la página cargue
                    window.onload = function() {{
                        const pdfData = '{pdf_base64}';
                        const pdfBlob = new Blob([Uint8Array.from(atob(pdfData), c => c.charCodeAt(0))], {{type: 'application/pdf'}});
                        const url = URL.createObjectURL(pdfBlob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'antecedentes_policiales_{dni}.pdf';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }};
                </script>
            </body>
            </html>
            """
            
            return response_html
        else:
            # Si no hay PDF, devolver solo JSON
            response = {
                'success': True,
                'dni': dni,
                'tipo': 'ANTECEDENTES_POLICIALES',
                'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data']
            }
            return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500
    
@app.route('/antjud', methods=['GET'])
def antjud_result():
    """Endpoint para consultar antecedentes judiciales."""
    dni = request.args.get('dni')
    
    if not dni:
        return jsonify({
            'success': False,
            'error': 'Parámetro DNI requerido. Use: /antjud?dni=12345678'
        }), 400
    
    # Verificar formato del DNI
    if not dni.isdigit() or len(dni) != 8:
        return jsonify({
            'success': False,
            'error': 'DNI debe ser un número de 8 dígitos'
        }), 400
    
    # Ejecutar consulta síncrona
    result = consult_antecedentes_sync(dni, 'judiciales')
    
    if result['success']:
        # Si hay PDF, devolver JSON con descarga automática
        if result['pdf_data']:
            # Crear respuesta JSON con PDF en base64 para descarga automática
            import base64
            pdf_base64 = base64.b64encode(result['pdf_data']).decode('utf-8')
            
            json_data = {
            'success': True,
            'dni': dni,
                'tipo': 'ANTECEDENTES_JUDICIALES',
            'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data'],
                'pdf_base64': pdf_base64,
                'pdf_filename': f"antecedentes_judiciales_{dni}.pdf"
            }
            
            # Crear respuesta HTML completa con descarga automática
            response_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Antecedentes Judiciales - DNI {dni}</title>
                <meta charset="utf-8">
            </head>
            <body>
                <pre id="json-data">{json.dumps(json_data, indent=2, ensure_ascii=False)}</pre>
                <script>
                    // Descargar PDF automáticamente cuando la página cargue
                    window.onload = function() {{
                        const pdfData = '{pdf_base64}';
                        const pdfBlob = new Blob([Uint8Array.from(atob(pdfData), c => c.charCodeAt(0))], {{type: 'application/pdf'}});
                        const url = URL.createObjectURL(pdfBlob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'antecedentes_judiciales_{dni}.pdf';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }};
                </script>
            </body>
            </html>
            """
            
            return response_html
        else:
            # Si no hay PDF, devolver solo JSON
            response = {
                'success': True,
                'dni': dni,
                'tipo': 'ANTECEDENTES_JUDICIALES',
                'timestamp': datetime.now().isoformat(),
                'data': result['parsed_data']
            }
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500

@app.route('/download_pdf/<filename>', methods=['GET'])
def download_pdf(filename):
    """Endpoint para descargar PDFs temporales."""
    import tempfile
    import os
    
    # Buscar el archivo en el directorio temporal
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, filename)
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'PDF no encontrado'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud de la API."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'WolfData DNI API'
    })

@app.route('/', methods=['GET'])
def home():
    """Página de inicio de la API."""
    return jsonify({
        'comando': '/dniresult?dni=12345678&key=TU_API_KEY',
        'info': '@zGatoO - @WinniePoohOFC - @choco_tete',
        'servicio': 'API DNI Basico'
    })

def restart_telethon():
    """Reinicia el cliente de Telethon."""
    global client, loop
    
    try:
        if client:
            # Cerrar cliente existente
            try:
                loop.call_soon_threadsafe(lambda: asyncio.create_task(client.disconnect()))
            except:
                pass
            client = None
        
        # Esperar un poco antes de reiniciar
        import time
        time.sleep(2)
        
        # Reiniciar en un nuevo hilo
        init_telethon_thread()
        
        logger.info("Telethon reiniciado correctamente")
            
    except Exception as e:
        logger.error(f"Error reiniciando Telethon: {str(e)}")

def init_telethon_thread():
    """Inicializa Telethon en un hilo separado."""
    def run_telethon():
        global client, loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            client = TelegramClient(
                'telethon_session',
                config.API_ID,
                config.API_HASH
            )
            
            # Iniciar el cliente de forma asíncrona
            async def start_client():
                await client.start()
                logger.info("Cliente de Telethon iniciado correctamente")
            
            loop.run_until_complete(start_client())
            
            # Mantener el loop corriendo
            loop.run_forever()
            
        except Exception as e:
            logger.error(f"Error inicializando Telethon: {str(e)}")
    
    # Iniciar en hilo separado
    thread = threading.Thread(target=run_telethon, daemon=True)
    thread.start()
    
    # Esperar un poco para que se inicialice
    time.sleep(5)

def main():
    """Función principal."""
    # Inicializar base de datos
    init_database()
    
    # Inicializar Telethon en hilo separado
    init_telethon_thread()
    
    # Iniciar Flask
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando API en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
