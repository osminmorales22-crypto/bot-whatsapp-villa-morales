import os
import re
import unicodedata
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# =========================================================================
# ⚙️ CONFIGURACIÓN DE DATOS REALES: APARTAMENTOS VILLA MORALES 🌴
# =========================================================================
DATOS_VILLA = {
    "bienvenida_formulario": (
        "¡Hola! Qué alegría saludarte. ☀️ Muchísimas gracias por interesarte en *Apartamentos Villa Morales*. "
        "Nos encanta la idea de ser tus anfitriones y ayudarte a disfrutar de un descanso espectacular aquí en el cálido Puerto San José. 🏖️\n\n"
        "Para brindarte una atención completamente personalizada, verificar la disponibilidad exacta y sugerirte la opción ideal para tu estadía, "
        "¿me ayudarías completando estos breves datos? 👇\n\n"
        "👤 *1. Nombre completo:*\n"
        "📅 *2. Fecha de ingreso (Check-in) y salida (Check-out):*\n"
        "👥 *3. Número total de personas (Adultos y niños):*\n\n"
        "En cuanto me compartas estos detalles, con gusto te armamos tu itinerario de inmediato. ¡Ya casi estás en la piscina! 🏊‍♂️🍹"
    ),
    "amenidades_instalaciones": (
        "¡Con muchísimo gusto! Te presento los detalles de *Apartamentos Villa Morales*, un espacio diseñado para tu total comodidad and descanso privado en el Puerto San José. 🌊✨\n\n"
        "🛏️ *Nuestros Apartamentos:*\n"
        "Contamos con *4 apartamentos exclusivos* (capacidad de *1 hasta 4 personas* cada uno), equipados con 1 cama matrimonial y 1 litera de dos camas imperiales. Puedes elegir entre:\n"
        "• 🍳 *Apartamentos Totalmente Equipados:* Ideales para cocinar en familia.\n"
        "• 🚪 *Apartamentos Estándar (No equipados):* Perfectos si tu plan es disfrutar de la gastronomía local.\n\n"
        "💎 *Amenidades Premium Incluidas:*\n"
        "• ❄️ *Climatización:* Aire acondicionado en tus habitaciones.\n"
        "• 🚿 *Privacidad:* Baño privado en cada apartamento.\n"
        "• 🛋️ *Confort:* Acogedora sala de estar y comedor.\n"
        "• 🌐 *Conectividad:* Conexión Wifi de alta velocidad y Televisión.\n"
        "• 🔒 *Seguridad:* Cerraduras inteligentes en las puertas.\n\n"
        "🏊‍♂️ *Áreas Sociales Compartidas:*\n"
        "Disfruta de nuestra espectacular piscina privada, churrasquera / parrilla para tus asados y baños dedicados exclusivamente para el área social. 🥰"
    ),
    "cocina_info": (
        "🍳 *Detalles de la Cocina en Apartamentos Villa Morales*\n\n"
        "Contamos con 2 apartamentos *totalmente equipados*, ideales si prefieres preparar tus propios platillos y bebidas. Incluyen:\n"
        "• Estufa con horno y horno de microondas.\n"
        "• Cristalería completa, cubertería y sartenes/ollas para cocinar.\n"
        "• Además, en el área social compartida tienes acceso a la parrilla/churrasquera. 🥩\n\n"
        "Nota: Los otros 2 apartamentos son estándar (sin equipo de cocina), perfectos si planeas comer en los restaurantes del puerto."
    ),
    "ubicacion_real": (
        "📍 *Ubicación Real de Villa Morales*\n\n"
        "Estamos ubicados estratégicamente justo en la entrada, en la *Colonia San Isidro de Puerto San José* 🏖️. Una zona de fácil acceso y muy segura.\n\n"
        "🚘 ¡Contamos con *estacionamiento gratuito* y cerrado dentro de las instalaciones para tu total tranquilidad!\n\n"
        "🗺️ *¿Cómo llegar?* Traza tu ruta con un solo clic en tu navegador desde aquí:\n"
        "Waze / Google Maps: https://google.com"
    ),
    "tarifas_inversion": (
        "¡Aquí tienes nuestra tabla de inversión! En *Apartamentos Villa Morales* manejamos tarifas súper accesibles para que disfrutes del puerto cualquier día de la semana. 🌴👇\n\n"
        "🍳 *Apartamentos Equipados con Cocina:*\n"
        "• 🗓️ *Domingo a Jueves:* Q350.00 por noche.\n"
        "• 🔥 *Viernes y Sábado:* Q380.00 por noche.\n"
        "_(Tarifa por noche para hasta 4 personas)_\n\n"
        "🚪 *Apartamentos Estándar (No equipados):*\n"
        "• 🗓️ *Domingo a Jueves:* Q250.00 por noche.\n"
        "• 🔥 *Viernes y Sábado:* Q300.00 por noche.\n"
        "_(Tarifa por noche para hasta 4 personas)_\n\n"
        "📅 Cuéntame qué tipo de apartamento se adapta mejor a tu viaje para confirmar disponibilidad."
    ),
    "politica_mascotas": (
        "🐾 *Política sobre Mascotas en Villa Morales*\n\n"
        "Con el fin de mantener los más estrictos estándares de higiene, limpieza y cuidar a huéspedes con condiciones de alergias, *no se permiten mascotas* en nuestras instalaciones bajo ninguna circunstancia. 🚫🐶\n\n"
        "Agradecemos enormemente tu comprensión al respecto para mantener la armonía del lugar."
    ),
    "politica_reserva_pagos": (
        "🔒 *Políticas de Pago y Reservación*\n\n"
        "Para garantizar una administración transparente y asegurar tu espacio, tomamos en cuenta lo siguiente:\n"
        "• 💳 *Garantía de espacio:* Para congelar tus fechas en el calendario, solicitamos el *depósito del 100% del valor total* de la estadía.\n"
        "• ⚠️ *Importante:* No se confirman ni se bloquean días en el sistema sin recibir un pago previo.\n"
        "• ⏰ *Horarios:* Nuestro horario de entrada (Check-in) es a las 3:00 PM y la salida (Check-out) a las 11:00 AM."
    ),
    "politica_cancelaciones": (
        "🔄 *Políticas de Cambios y Cancelaciones*\n\n"
        "Entendemos que los imprevistos suceden. Si necesitas cancelar o modificar tu fecha:\n"
        "• Debes notificarlo con un mínimo de *3 días de anticipación* para aplicar a una *devolución parcial* de tu depósito.\n"
        "• Las cancelaciones o modificaciones hechas con menos de 3 días de anticipación no aplican a ningún tipo de reembolso. 📝"
    ),
    "guion_traspaso_humano": (
        "✨ *¡Todo listo para tu escapada al puerto!*\n\n"
        "Con los datos que me compartiste, ya tengo pre-configurada tu solicitud para *Apartamentos Villa Morales*. "
        "Para asegurar que tu asignación de apartamento sea perfecta y entregarte nuestras cuentas bancarias oficiales de forma segura, "
        "*es momento de conectarte con tu anfitrión de confianza*. 🤵🏽‍♂️ En este mismo instante, nuestro administrador humano está revisando tu chat.\n\n"
        "Siguiente paso:\n"
        "👉 Por favor, escribe la palabra *ANFITRION* aquí abajo para congelar tus fechas y recibir los datos de depósito directamente de nuestro equipo. "
        "¡Te atenderemos en un abrir y cerrar de ojos! 🚀🌴"
    )
}

# =========================================================================
# 🔐 CONFIGURACIÓN DE CREDENCIALES DE TU INSTANCIA DE Z-API
# =========================================================================
Z_API_ID = "3FB9FDE8CBE8A1D70118"
Z_API_TOKEN = "252A87FAD09523C83EE5"

KEYWORDS_INTENTS = {
    r"\b(precio|cuanto cuesta|valor|costo|tarifa|promocion|cuanto|precios|cotiz|invertir|inversion|q350|q250)\b": "TARIFAS",
    r"\b(donde|ubic|direccion|como llegar|san isidro|mapa|waze|google maps|gps|localizacion|parqueo|estacionamiento)\b": "UBICACION",
    r"\b(amenidades|servicios|instalaciones|piscina|alberca|cuartos|habitaciones|camas|litera|aire|acondicionado|wifi|tv|television|cable|apartamentos|cuantos apartamentos|baño)\b": "AMENIDADES",
    r"\b(cocina|cocinar|estufa|horno|microondas|cristaleria|cuberteria|platos|vasos|utensilios|parrilla|churrasquera|asado|equipada|equipado)\b": "COCINA",
    r"\b(perro|gato|mascota|mascotas|animales|traer mi perro|aceptan animales|pet friendly)\b": "MASCOTAS",
    r"\b(reservar|reserva|separar|agendar|apartar|cuenta|banco|depositar|deposito|pago|pagar|100%|transferencia|check in|check out|horario)\b": "RESERVA_PAGOS",
    r"\b(cancelar|cancelacion|cambiar fecha|devolucion|reembolso|retornar dinero|anticipacion|postergar)\b": "CANCELACIONES",
    r"\b(hola|buenos dias|buenas tardes|buenas noches|disponib|fecha|libre|esta ocupado|cuando puedo|dia|mes|calendario|info|informacion|interesado)\b": "BIENVENIDA"
}

session_storage = {}

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
    if client_phone not in session_storage:
        session_storage[client_phone] = {"state": "START", "nombre": None, "fechas": None, "personas": None}
        
    session = session_storage[client_phone]
    current_state = session["state"]
    cleaned_message = clean_text(user_message)

    if "anfitrion" in cleaned_message or "humano" in cleaned_message or "asesor" in cleaned_message:
        session["state"] = "INTERVENCION_HUMANA"
        return "🔔 *Notificación:* He pausado mis respuestas automáticas. Nuestro anfitrión ya está en el chat y te responderá personalmente en un momento. ¡Gracias por tu paciencia! 👋"

    if current_state == "INTERVENCION_HUMANA":
        return None

    if current_state == "ESPERANDO_NOMBRE":
        session["nombre"] = user_message
        session["state"] = "ESPERANDO_FECHAS"
        return f"🗓️ Gracias *{user_message}*. Anotado en tu ficha.\n\nComo segundo paso: *¿Cuáles serían tus fechas de ingreso (Check-in) y de salida (Check-out)?*"

    elif current_state == "ESPERANDO_FECHAS":
        session["fechas"] = user_message
        session["state"] = "ESPERANDO_PERSONAS"
        return f"👥 ¡Excelente! Fechas registradas: *{user_message}*.\n\nPor último: *¿Para cuántas personas (adultos y niños) sería tu grupo?*"

    elif current_state == "ESPERANDO_PERSONAS":
        session["personas"] = user_message
        session["state"] = "LISTO_PARA_TRASPASO"
        return DATOS_VILLA["guion_traspaso_humano"]

    elif current_state == "LISTO_PARA_TRASPASO":
