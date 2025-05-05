import requests
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
import logging
from functools import lru_cache

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)

# Configura o webhook do Bitrix24 a partir do .env
WEBHOOK_URL = os.getenv('WEBHOOK_BITRIX')

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def brasil_api(cep):
    response = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep}", timeout=5)
    response.raise_for_status()
    data = response.json()
    return data['cep'], data['city'], data['street'], data['neighborhood'], data['state']

def via_cep(cep):
    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
    response.raise_for_status()
    data = response.json()
    if "erro" in data:
        raise ValueError("CEP não encontrado no ViaCEP")
    return data['cep'], data['localidade'], data['logradouro'], data['bairro'], data['uf']

def open_cep(cep):
    response = requests.get(f"https://opencep.com/v1/{cep}.json", timeout=5)
    response.raise_for_status()
    data = response.json()
    return data['cep'], data['cidade'], data['logradouro'], data['bairro'], data['estado']

@lru_cache(maxsize=100)
def get_city_and_uf(cep):
    logging.info(f"Consultando o CEP: {cep}")
    cep = cep.strip().replace("-", "")

    for funcao in [brasil_api, via_cep, open_cep]:
        try:
            ceptrue, cidade, rua, bairro, uf = funcao(cep)
            if cidade and uf:
                logging.info(f"Consulta bem-sucedida: {ceptrue}, {cidade}, {rua}, {bairro}, {uf}")
                return ceptrue, cidade, rua, bairro, uf
        except Exception as e:
            logging.warning(f"Erro com {funcao.__name__}: {e}")

    logging.error("Todas as APIs falharam ao consultar o CEP.")
    return None, None, None, None, None

def marcar_cep_invalido(deal_id):
    url = f"{WEBHOOK_URL}crm.deal.update.json"
    payload = {
        'ID': deal_id,
        'FIELDS': {
            'UF_CRM_1700661314351': "CEP INVÁLIDO"
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        logging.info(f"CEP inválido registrado para o negócio {deal_id}: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Erro ao marcar CEP inválido no Bitrix24: {e}")

@app.route('/adress_full/<int:deal_id>/<cep>', methods=['GET'])
def atualizar_endereco(deal_id, cep):
    ceptrue, cidade, rua, bairro, uf = get_city_and_uf(cep)

    if not (cidade and uf):
        marcar_cep_invalido(deal_id)
        return jsonify({"erro": "CEP INVÁLIDO"}), 400

    url = f"{WEBHOOK_URL}crm.deal.update.json"
    payload = {
        'ID': deal_id,
        'FIELDS': {
            'UF_CRM_1700661314351': ceptrue,
            'UF_CRM_1700661327489': cidade,
            'UF_CRM_1700661337157': rua,
            'UF_CRM_1700661348273': bairro,
            'UF_CRM_1700661357570': uf
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return jsonify({"mensagem": "Dados atualizados com sucesso!"})
        else:
            return jsonify({"erro": "Erro ao atualizar negócio"}), 500
    except Exception as e:
        logging.error(f"Erro na requisição para o Bitrix24: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1474)
