import os
import re
import unicodedata
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# =========================================================================
# ⚙️ CONFIGURACIÓN DE DATOS DE VILLA MORALES (Modificable en cualquier momento)
# =========================================================================
# Puedes cambiar los textos de abajo cuando quieras sin romper el Webhook.
DATOS_VILLA = {
    "precio": (
        "💰 *¡Hola! Con gusto te comparto nuestras tarifas para Villa Morales:*\n\n"
        "Contamos con una promoción especial de fin de semana:\n"
        "✨ *Estadía de Viernes a Domingo por solo Q2,500.*\n\n"
        "_El precio incluye el uso exclusivo de todas las instalaciones, piscina y áreas recreativas._ 🌴\n\n"
        "📅 ¿Te gustaría saber si tenemos libre el fin de semana de tu interés? Solo dime qué fecha buscas."
    ),
    "ubicacion": (
        "📍 *¡Ubicación de Villa Morales!*\n\n"
        "Nos encontramos en el *Km 143, Aldea El Banco*, a tan solo 300 metros del mar 🌊. "
        "Una zona tranquila, segura y perfecta para relajarse en la costa.\n\n"
        "Si deseas ver fotos o la ruta exacta en mapa, con gusto te la comparto. 🧭 "
        "¿Estás planeando tu visita para este mes o el próximo?"
    ),
    "capacidad": (
        "🏡 *¡Villa Morales está lista para recibir a todo tu grupo!*\n\n"
        "Nuestra capacidad máxima es de *16 personas*. Las instalaciones incluyen:\n"
        "• 🛏️ 4 amplias habitaciones totalmente acondicionadas.\n"
        "• 🏊‍♂️ Piscina privada espectacular.\n"
        "• 🍳 Cocina equipada y área de churrasquera.\n"
        "• 🐶 ¡Somos 100% Pet Friendly! Tus peluditos son bienvenidos sin costo adicional.\n\n"
        "👥 ¿Cuántas personas planean viajar contigo en esta ocasión?"
    )
}

# =========================================================================
# 🔐 CONFIGURACIÓN DE SEGURIDAD DE LA API DE WHATSAPP (META)
# =========================================================================
# Estos tokens te los entrega Meta Developers al registrar tu app de WhatsApp.
TOKEN_VERIFICACION = "MI_TOKEN_SECRETO_DE_WHATSAPP"  # Elige una frase segura para vincular Meta
TOKEN_ACCESO_META = "EAAb...."  # Tu Token de Acceso Permanente de Meta
ID_TELEFONO_VILLA = "1092837465"  # Identificador de tu número comercial en Meta

# Diccionario de intenciones (Mapeo de palabras clave)
KEYWORDS_INTENTS = {
    r"\b(precio|cuanto cuesta|valor|costo|tarifa|promocion|q2500|cuanto)\b": "PRECIO",
    r"\b(disponib|fecha|libre|esta ocupado|cuando puedo|dia|mes|calendario)\b": "DISPONIBILIDAD",
    r"\b(donde|ubic|direccion|como llegar|km 143|aldea el banco|mapa)\b": "UBICACION",
    r"\b(capacidad|cuantas personas|cuantos caben|habitaciones|dormitorios|cuantos cuartos)\b": "CAPACIDAD",
    r"\b(reservar|reserva|quiero alquilar|separar|agendar|apartar)\b": "INICIAR_RESERVA"
}

# Almacenamiento temporal en memoria para rastrear el flujo del cliente
session_storage = {}

# =========================================================================
# 🧠 LÓGICA DE PROCESAMIENTO Y GENERACIÓN DE RESPUESTAS
# =========================================================================
def clean_text(text):
    text = text.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def detect_intent(text):
    cleaned = clean_text(text)
    for pattern, intent in KEYWORDS_INTENTS.items():
        if re.search(pattern, cleaned):
            return intent
    return "UNKNOWN"

def generate_response(client_phone, user_message):
    """Determina la respuesta correcta usando la máquina de estados y las plantillas"""
    if client_phone not in session_storage:
        session_storage[client_phone] = {"state": "START", "date": None, "guests": None}
        
    session = session_storage[client_phone]
    current_state = session["state"]
    
    # Flujo Guiado de Reserva
    if current_state == "WAITING_DATE":
        session["date"] = user_message
        session["state"] = "WAITING_GUESTS"
        return f"🗓️ *¡Entendido! Anotado para la fecha: {user_message}.*\n\nDéjame revisar el sistema rápido. Mientras tanto, *¿para cuántas personas (adultos y niños) sería tu grupo?*"

    elif current_state == "WAITING_GUESTS":
        session["guests"] = user_message
        session["state"] = "CONFIRMATION_PENDING"
        return (f"✨ *¡Buenas noticias! Tenemos disponibilidad para las fechas seleccionadas.* Aquí tienes el resumen preliminar de tu cotización:\n\n"
                f"🏡 *Lugar:* Villa Morales\n"
                f"🗓️ *Fecha:* {session['date']}\n"
                f"👥 *Total de huéspedes:* {session['guests']} personas\n\n"
                f"Para pre-reservar la fecha, asegurar tu espacio y recibir los datos bancarios, por favor responde con la palabra *CONFIRMAR*.")

    elif current_state == "CONFIRMATION_PENDING":
        if "confirmar" in clean_text(user_message):
            session_storage[client_phone] = {"state": "START", "date": None, "guests": None}
            return "✅ *¡Excelente elección! Tu pre-reserva para Villa Morales ha sido registrada con éxito.*\n\nUn asesor humano se unirá a este chat en breve para entregarte tu comprobante oficial. ¡Gracias! 🏖️"
        else:
            return "Por favor, para finalizar responde únicamente con la palabra *CONFIRMAR* o indícame si deseas corregir algún dato."

    # Respuestas Informativas Directas utilizando el diccionario configurable
    intent = detect_intent(user_message)
    if intent == "PRECIO":
        return DATOS_VILLA["precio"]
    elif intent == "UBICACION":
        return DATOS_VILLA["ubicacion"]
    elif intent == "CAPACIDAD":
        return DATOS_VILLA["capacidad"]
    elif intent == "DISPONIBILIDAD" or intent == "INICIAR_RESERVA":
        session["state"] = "WAITING_DATE"
        return "👋 *¡Perfecto! Nos encantaría recibirte en Villa Morales.*\n\nPara verificar nuestro calendario de inmediato, *¿en qué fecha o fin de semana te gustaría programar tu estadía?*"
    
    return "¡Hola! Bienvenido al chat oficial de *Villa Morales* 🌴. ¿En qué te puedo ayudar? Puedes consultarme sobre nuestro *precio*, *ubicación*, *capacidad* o decirme si deseas *reservar*."

# =========================================================================
# 🌐 CONEXIÓN EXTERNA CON LA API DE WHATSAPP (ENDPOINTS FLASK)
# =========================================================================

def send_message_to_whatsapp(to_number, text_response):
    """Envía el texto generado de vuelta al teléfono del cliente vía API de Meta"""
    url = f"https://facebook.com{ID_TELEFONO_VILLA}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN_ACCESO_META}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": True, "body": text_response}
    }
    try:
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        print(f"Error enviando mensaje a WhatsApp: {e}")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Paso obligatorio de Meta para validar que tu servidor Flask es seguro"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == TOKEN_VERIFICACION:
            print("¡Webhook Verificado Correctamente por Meta!")
            return challenge, 200
        else:
            return "Token de verificación inválido", 403
    return "Faltan parámetros", 400

@app.route('/webhook', methods=['POST'])
def receive_message():
    """Endpoint principal: se ejecuta cada vez que un cliente escribe a tu WhatsApp"""
    body = request.get_json()
    
    try:
        # Extraer el mensaje y el número del cliente de la estructura JSON de Meta
        if 'messages' in body['entry'][0]['changes'][0]['value']:
            message_data = body['entry'][0]['changes'][0]['value']['messages'][0]
            client_phone = message_data['from']
            
            # Verificar si es un mensaje de texto
            if message_data['type'] == 'text':
                user_message = message_data['text']['body']
                
                # 1. Procesar lógica y obtener la respuesta de la villa
                bot_reply = generate_response(client_phone, user_message)
                
                # 2. Enviar la respuesta de vuelta a WhatsApp
                send_message_to_whatsapp(client_phone, bot_reply)
                
    except KeyError:
        pass
        
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    # Ejecuta el servidor localmente en el puerto 5000
    app.run(port=5000, debug=True)
