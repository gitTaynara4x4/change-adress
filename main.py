import requests
import os
from dotenv import load_dotenv
import time
from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

load_dotenv()
WEBHOOK_BITRIX = os.getenv('WEBHOOK_BITRIX')
WEBHOOK_URL = f"{WEBHOOK_BITRIX}"

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_city_and_uf(cep, deal_id=None):
    logging.info(f"Consultando o CEP: {cep}")
    cep = cep.strip().replace("-", "")

    apis = [brasil_api, via_cep, open_cep]

    for api_func in apis:
        try:
            ceptrue, cidade, rua, bairro, uf = api_func(cep)
            if cidade and uf:
                logging.info(f"Consulta bem-sucedida: {ceptrue}, {cidade}, {rua}, {bairro}, {uf}")
                return ceptrue, cidade, rua, bairro, uf
        except Exception as e:
            logging.error(f"Erro na função {api_func.__name__}: {e}")

    logging.error("Todas as consultas falharam.")

    # Atualiza o campo do CEP com "CEP INVÁLIDO"
    if deal_id:
        try:
            url = f"{WEBHOOK_URL}crm.deal.update.json"
            payload = {
                'ID': deal_id,
                'FIELDS': {
                    'UF_CRM_1700661314351': 'CEP INVÁLIDO'
                }
            }
            response = requests.post(url, json=payload, timeout=5)
            logging.info(f"CEP INVÁLIDO enviado ao Bitrix24: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Erro ao atualizar o CEP como inválido no Bitrix24: {e}")

    return None, None, None, None, None

def via_cep(cep):
    logging.info(f"➡️  Tentando consulta na ViaCEP: {cep}")
    time.sleep(1)
    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
    if response.status_code == 200 and "erro" not in response.json():
        data = response.json()
        return data.get("cep", "").replace("-", ""), data.get("localidade", ""), data.get("logradouro", ""), data.get("bairro", ""), data.get("uf", "")
    return None, None, None, None, None

def open_cep(cep):
    logging.info(f"➡️  Tentando consulta na OpenCEP: {cep}")
    time.sleep(1)
    response = requests.get(f"https://opencep.com/v1/{cep}.json", timeout=5)
    if response.status_code == 200:
        data = response.json()
        return data.get("cep", "").replace("-", ""), data.get("cidade", ""), data.get("logradouro", ""), data.get("bairro", ""), data.get("uf", "")
    return None, None, None, None, None

def brasil_api(cep):
    logging.info(f"➡️  Tentando consulta na BrasilAPI: {cep}")
    time.sleep(1)
    response = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep}", timeout=5)
    if response.status_code == 200:
        data = response.json()
        return data.get("cep", "").replace("-", ""), data.get("city", ""), data.get("street", ""), data.get("neighborhood", ""), data.get("state", "")
    return None, None, None, None, None


def update_bitrix24_record(deal_id, cidade, rua, bairro, uf):
    url = f"{WEBHOOK_URL}crm.deal.update.json"
    payload = {
        'ID': deal_id,
        'FIELDS': {
            'UF_CRM_1700661287551': bairro.upper() if bairro else '',
            'UF_CRM_1698688252221': rua.upper() if rua else '',
            'UF_CRM_1731588487': cidade.upper(),
            'UF_CRM_1731589190': uf.upper(),
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        logging.info(f"Atualização Bitrix: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Erro ao atualizar Bitrix24: {e}")

def get_number_from_bitrix(deal_id):
    url = f"{WEBHOOK_URL}crm.deal.get.json"
    params = {"ID": deal_id}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["result"].get("UF_CRM_1700661252544", None)
    except Exception as e:
        logging.error(f"Erro ao buscar negócio {deal_id}: {e}")
        return None
#rua, numero, bairro, cidade - estado, cep
def update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, ceptrue, number):
    endereco = f"{rua}, {number}, {bairro}, {cidade} - {uf}, {ceptrue}".upper()
    url = f"{WEBHOOK_URL}crm.deal.update.json"
    payload = {
        'ID': deal_id,
        'FIELDS': {
            'UF_CRM_1732711183': endereco
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        logging.info(f"Atualizado campo endereço: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Erro ao atualizar endereço: {e}")

@app.route('/adress_full/<int:deal_id>/<string:cep>', methods=['POST'])
def adress_full(deal_id, cep):
    try:
        if not deal_id or not cep:
            return jsonify({"erro": "Parâmetros obrigatórios não fornecidos"}), 400

        number = get_number_from_bitrix(deal_id)
        if not number:
            return jsonify({"erro": "O número do endereço deve ser preenchido antes de continuar"}), 400

        ceptrue, cidade, rua, bairro, uf = get_city_and_uf(cep, deal_id=deal_id)
        if not (cidade and uf):
            return jsonify({"erro": "Não foi possível obter dados para o CEP"}), 400

        update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, ceptrue, number)
        return jsonify({
            "sucesso": f"Registro {deal_id} atualizado com sucesso!",
            "formatted_address": f"{rua}, {number}, {bairro}, {cidade} - {uf}, {ceptrue}".upper()
        }), 200
#rua, numero, bairro, cidade - estado, cep

    except Exception as e:
        logging.error(f"Erro: {e}")
        return jsonify({"erro": "Erro interno"}), 500

@app.route('/atualizar_cidade_uf/<int:deal_id>/<string:cep>', methods=['POST'])
def atualizar_cidade_uf(deal_id, cep):
    cep = cep.strip()
    try:
        number = get_number_from_bitrix(deal_id)
        ceptrue, cidade, rua, bairro, uf = get_city_and_uf(cep, deal_id=deal_id)
        if cidade and uf:
            update_bitrix24_record(deal_id, cidade, rua, bairro, uf)
            update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, ceptrue, number)
            return jsonify({"sucesso": f"Registro {deal_id} atualizado com sucesso!"}), 200
        else:
            return jsonify({"erro": "Não foi possível obter dados para o CEP"}), 400
    except Exception as e:
        logging.error(f"Erro: {e}")
        return jsonify({"erro": "Erro interno"}), 500

@app.route('/cidade_formatada_uf/<int:deal_id>', methods=['POST'])
def cidade_formatada_uf(deal_id):
    res = requests.get(f"{WEBHOOK_URL}crm.deal.get?ID={deal_id}")
    card_cep = res.json()["result"]["UF_CRM_1700661314351"].replace(",", "")
    data = requests.get(f"https://viacep.com.br/ws/{card_cep}/json/")
    localidade = data.json()["localidade"]
    uf = data.json()["uf"]
    url_update = f"{WEBHOOK_URL}crm.deal.update?ID={deal_id}&FIELDS[UF_CRM_1731588487]={localidade.upper()}&FIELDS[UF_CRM_1731589190]={uf.upper()}"
    requests.post(url_update)
    return {"message": f"Card de id {deal_id} atualizado!"}, 200


            
#rua, numero, bairro, cidade - estado, cep


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1474)
