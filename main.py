from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# Load environment variables
load_dotenv()
CODIGO_BITRIX = os.getenv('CODIGO_BITRIX')
CODIGO_BITRIX_STR = os.getenv('CODIGO_BITRIX_STR')
PROFILE = os.getenv('PROFILE')
BASE_URL_API_BITRIX = os.getenv('BASE_URL_API_BITRIX')

# Define the webhook URL
BITRIX_WEBHOOK_URL = f"{BASE_URL_API_BITRIX}/{PROFILE}/{CODIGO_BITRIX}/bizproc.workflow.start"

def update_card_bitrix(card_id, name_of_field, value):
    url = f"{BASE_URL_API_BITRIX}/{PROFILE}/{CODIGO_BITRIX}/crm.deal.update"
    data = {
        'id': card_id,
        'fields': {
            name_of_field: value
        }
    }
    if value == None:
        print('⚠ A varivel value é nula ⚠')
        return -1

    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"Field '{name_of_field}' updated successfully.")
    else:
        print("Failed to update field.")
        print(response.text)

def convert_for_gmt_minus_3(date_from_bitrix):
    hour_obj = datetime.fromisoformat(date_from_bitrix)
    hour_sub = hour_obj - timedelta(hours=6)
    new_hour_formated = hour_sub.isoformat()
    return new_hour_formated
    
WORKFLOW_IDS = {
    "workflow1": "1196", #primeiro boleto(1.1)
    "workflow2": "1200", #primeiro boleto(1.2)
    "workflow3": "1204", #segundo boleto(1.1)
    "workflow4": "1206", #segundo boleto(1.2)
    "workflow5": "1208", #terceiro boleto(1.1)
    "workflow6": "1210", #terceiro boleto(1.2)
    "workflow7": "1212", #quarto boleto(1.1)
    "workflow8": "1214", #quarto boleto(1.2)
    "workflow9": "1216", #quinto boleto(1.1)
    "workflow10": "1218", #quinto boleto(1.2)
    "workflow11": "1314", #workflow para o site
    "workflow12": "1294", #workflow para a fila de ativos
    "workflow13": "1390", #workflow para campo sem fuso horario ser atualizado. 
    "workflow14": "1426", #workflow que muda o campo de Relatorio data. 
    "workflow15": "1428" #workflow que muda o campo de Relatorio data/hora. 
}

@app.route('/webhook/<workflow_name>', methods=['POST'])
def start_workflow(workflow_name):
    print("Webhook acionado!")  # Log to check if the endpoint is called
    deal_id = request.args.get('deal_id')

    if not deal_id:
        return jsonify({"error": "deal_id não fornecido"}), 400

    # Get the workflow ID from the dictionary
    workflow_id = WORKFLOW_IDS.get(workflow_name)
    if not workflow_id:
        return jsonify({"error": "Workflow não encontrado"}), 404

    array = ["crm", "CCrmDocumentDeal", f"DEAL_{deal_id}"]
    data = {
        "TEMPLATE_ID": workflow_id,
        "DOCUMENT_ID": array
    }

    time.sleep(10)  # Consider removing or reducing this in production
    try:
        response = requests.post(BITRIX_WEBHOOK_URL, json=data)
        response.raise_for_status()  # Raise an error for bad responses
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Error calling Bitrix API: {e}")
        return jsonify({"error": "Failed to start workflow", "details": str(e)}), 500


@app.route('/date-time-brazil-in-bitrix', methods=['POST'])
def update_new_date():
    deal_id = request.args.get('ID')
    date_create = request.args.get('DATE_CREATE')
    try:
        formated_date = convert_for_gmt_minus_3(date_create)
        update_card_bitrix(deal_id, 'UF_CRM_1731416690056', formated_date)
    except requests.exceptions.RequestException as e:
        print(f"Error update date field: {e}")
        return jsonify({"error": f"Failed to update datetime in Bitrix for card: {deal_id}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7963)
