#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API DNI Básico - WolfData Dox
Servidor especializado para consultas básicas de DNI con foto
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
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaPhoto

import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables globales
client = None
loop = None

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
    fecha_insc_match = re.search(r'FECHA\s*INSCRIPCION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_insc_match:
        data['FECHA_INSCRIPCION'] = fecha_insc_match.group(1).strip()
    
    # Extraer fecha de emisión
    fecha_emi_match = re.search(r'FECHA\s*EMISION\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_emi_match:
        data['FECHA_EMISION'] = fecha_emi_match.group(1).strip()
    
    # Extraer fecha de caducidad
    fecha_cad_match = re.search(r'FECHA\s*CADUCIDAD\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if fecha_cad_match:
        data['FECHA_CADUCIDAD'] = fecha_cad_match.group(1).strip()
    
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
    ubigeo_reneic_match = re.search(r'UBIGEO\s*RENIEC\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_reneic_match:
        data['UBIGEO_RENIEC'] = ubigeo_reneic_match.group(1).strip()
    
    # Extraer UBIGEO INE
    ubigeo_ine_match = re.search(r'UBIGEO\s*INE\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_ine_match:
        data['UBIGEO_INE'] = ubigeo_ine_match.group(1).strip()
    
    # Extraer UBIGEO SUNAT
    ubigeo_sunat_match = re.search(r'UBIGEO\s*SUNAT\s*[➾\-=]\s*([^\n\r]+)', clean_text)
    if ubigeo_sunat_match:
        data['UBIGEO_SUNAT'] = ubigeo_sunat_match.group(1).strip()
    
    return data

def consult_dni_sync(dni_number):
    """Consulta el DNI usando Telethon de forma síncrona."""
    global client, loop
    
    if not client:
        return {
            'success': False,
            'error': 'Cliente de Telegram no inicializado'
        }
    
    try:
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

async def consult_dni_async(dni_number):
    """Consulta asíncrona del DNI con manejo inteligente de colas."""
    global client
    
    try:
        max_attempts = 3  # Máximo 3 intentos
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Intento {attempt}/{max_attempts} para DNI {dni_number}")
            
            # Enviar comando /dni
            await client.send_message(config.TARGET_BOT, f"/dni {dni_number}")
            logger.info(f"Comando /dni enviado correctamente (intento {attempt})")
            
            # Esperar un poco antes de revisar mensajes
            await asyncio.sleep(2)
            
            # Obtener mensajes recientes
            messages = await client.get_messages(config.TARGET_BOT, limit=10)
            current_timestamp = time.time()
            new_messages = [msg for msg in messages if msg.date.timestamp() > current_timestamp - 60]
            
            logger.info(f"Revisando {len(new_messages)} mensajes nuevos para DNI {dni_number}...")
            
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
                
                # Buscar respuesta específica para DNI
                clean_message = message.text.replace('`', '').replace('*', '').replace('**', '')
                if (f"DNI ➾ {dni_number}" in clean_message and 
                    ("RENIEC ONLINE" in clean_message or "OLIMPO_BOT" in clean_message)):
                    
                    logger.info(f"¡Respuesta encontrada para DNI {dni_number}!")
                    logger.info(f"Texto completo: {message.text}")
                    
                    # Encontramos la respuesta
                    text_data = message.text
                    photo_data = None
                    
                    # Verificar si hay foto adjunta
                    if message.media and hasattr(message.media, 'photo'):
                        logger.info("Descargando foto...")
                        # Descargar foto en memoria
                        photo_bytes = await client.download_media(message.media, file=BytesIO())
                        photo_data = base64.b64encode(photo_bytes.getvalue()).decode('utf-8')
                        logger.info(f"Foto descargada: {len(photo_data)} caracteres")
                    
                    parsed_data = parse_dni_response(text_data)
                    logger.info(f"Datos parseados: {parsed_data}")
                    
                    return {
                        'success': True,
                        'text_data': text_data,
                        'photo_data': photo_data,
                        'parsed_data': parsed_data
                    }
            
            # Si no se encontró respuesta, esperar antes del siguiente intento
            if attempt < max_attempts:
                logger.warning(f"No se detectó respuesta en intento {attempt}. Esperando 3 segundos...")
                await asyncio.sleep(3)
        
        logger.error(f"Timeout consultando DNI {dni_number}")
        return {
            'success': False,
            'error': 'Timeout: No se recibió respuesta después de 3 intentos'
        }
        
    except Exception as e:
        logger.error(f"Error consultando DNI {dni_number}: {str(e)}")
        return {
            'success': False,
            'error': f'Error en la consulta: {str(e)}'
        }

# Crear la aplicación Flask
app = Flask(__name__)

@app.route('/dniresult', methods=['GET'])
def dni_result():
    """Endpoint para consultar DNI."""
    dni = request.args.get('dni')
    
    if not dni:
        return jsonify({
            'success': False,
            'error': 'Parámetro DNI requerido. Use: /dniresult?dni=12345678'
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

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud de la API."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'WolfData DNI API - Básico'
    })

@app.route('/', methods=['GET'])
def home():
    """Página de inicio de la API."""
    return jsonify({
        'service': 'WolfData DNI API - Básico',
        'version': '1.0.0',
        'endpoints': {
            'dni_query': '/dniresult?dni=12345678',
            'health': '/health'
        },
        'description': 'API especializada para consultas básicas de DNI con foto'
    })

def restart_telethon():
    """Reinicia el cliente de Telethon."""
    global client, loop
    try:
        if client:
            client.disconnect()
        if loop:
            loop.close()
        
        # Reinicializar en un nuevo hilo
        init_telethon_thread()
        logger.info("Cliente de Telethon reiniciado")
    except Exception as e:
        logger.error(f"Error reiniciando Telethon: {str(e)}")

def init_telethon_thread():
    """Inicializa Telethon en un hilo separado."""
    global client, loop
    
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
            
            loop.run_until_complete(client.start())
            logger.info("Cliente de Telethon iniciado correctamente")
            
            # Mantener el loop corriendo
            loop.run_forever()
            
        except Exception as e:
            logger.error(f"Error inicializando Telethon: {str(e)}")
    
    # Iniciar en hilo separado
    thread = threading.Thread(target=run_telethon, daemon=True)
    thread.start()
    
    # Esperar un poco para que se inicialice
    time.sleep(3)

def main():
    """Función principal."""
    # Inicializar Telethon en hilo separado
    init_telethon_thread()
    
    # Iniciar Flask
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Iniciando API en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
