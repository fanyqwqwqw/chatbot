import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify
from flasgger import Swagger
from google.cloud import dialogflow
from google.oauth2 import service_account
import json
import os
import requests
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 

# Configuración de Flasgger para documentación Swagger
swagger = Swagger(app, template_file='swagger_doc.yaml')

# Configuración del proyecto Dialogflow
PROJECT_ID = 'chatbot-vkr9'  # ID del proyecto de Dialogflow
SESSION_ID = 'test-session'  # ID de la sesión

# Leer las credenciales de Google desde la variable de entorno
google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if google_credentials:
    if os.path.exists(google_credentials):
        # Si la variable es una ruta a un archivo, la usamos directamente
        credentials = service_account.Credentials.from_service_account_file(google_credentials)
    else:
        try:
            # Intentamos cargar el contenido JSON de las credenciales
            credentials_info = json.loads(google_credentials)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
        except json.JSONDecodeError:
            raise EnvironmentError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no contiene un JSON válido.")
else:
    raise EnvironmentError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está configurada.")

# Inicializar el cliente de Dialogflow con las credenciales
session_client = dialogflow.SessionsClient(credentials=credentials)
session = session_client.session_path(PROJECT_ID, SESSION_ID)

# Función para obtener la respuesta de Dialogflow
def detectar_intento(texto_usuario):
    text_input = dialogflow.TextInput(text=texto_usuario, language_code="es")
    query_input = dialogflow.QueryInput(text=text_input)
    
    response = session_client.detect_intent(session=session, query_input=query_input)
    
    # Solo retornamos la respuesta de Dialogflow
    return response.query_result.fulfillment_text

# Endpoint para solicitudes directas del cliente (Aislado)
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'response': "Por favor, escribe una pregunta válida."}), 400
    
    # Llamamos a Dialogflow para obtener la respuesta
    respuesta = detectar_intento(user_input)

    # Devolvemos la respuesta de Dialogflow
    return jsonify({'response': respuesta})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)