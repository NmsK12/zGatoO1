# WolfData DNI API - Básico

Servidor especializado para consultas básicas de DNI con foto.

## Endpoints

- `GET /dniresult?dni=12345678` - Consulta básica de DNI con foto
- `GET /health` - Estado de salud del servicio
- `GET /` - Información del servicio

## Características

- Consulta básica de DNI con información esencial
- Foto de la persona en base64
- Sistema de cola inteligente
- Manejo de errores y reintentos
- Sin sistema de tokens (ilimitado)

## Instalación

```bash
pip install -r requirements.txt
python api_dni.py
```

## Variables de Entorno

- `API_ID` - ID de la API de Telegram
- `API_HASH` - Hash de la API de Telegram
- `TARGET_BOT` - Bot objetivo (@OlimpoDataBot)
- `PORT` - Puerto del servidor (default: 8080)
