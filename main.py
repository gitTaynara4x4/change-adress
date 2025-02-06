import requests
import os
from dotenv import load_dotenv
import time
import random
from flask import Flask, jsonify, request
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)


load_dotenv()


WEBHOOK_URL = f"https://marketingsolucoes.bitrix24.com.br/rest/5332/zlxwmf2uqcix6f7u/"


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  
)


@lru_cache(maxsize=100)
def get_city_and_uf(cep):
    logging.info(f"Consultando o CEP: {cep}")
    cep = cep.strip().replace("-", "")  

    
    apis = [
        {"nome": "ViaCEP", "url": f"https://viacep.com.br/ws/{cep}/json/", "funcao": via_cep},
        {"nome": "OpenCEP", "url": f"https://opencep.com/v1/{cep}.json", "funcao": open_cep},
        {"nome": "BrasilAPI", "url": f"https://brasilapi.com.br/api/cep/v2/{cep}", "funcao": brasil_api}
    ]

    
    random.shuffle(apis)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(api["funcao"], cep) for api in apis]
        for future in as_completed(futures):
            try:
                cep, cidade, rua, bairro, uf = future.result()
                if cidade and uf:  
                    logging.info(f"Consulta bem-sucedida com os dados: CEP: {cep}, Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
                    
                    return cep, cidade, rua, bairro, uf
            except Exception as e:
                logging.error(f"Erro ao processar a consulta: {e}")

    
    logging.error(f"Erro ao consultar o CEP nas APIs.")
    return None, None, None, None, None


def via_cep(cep):
    time.sleep(4)
    response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
    if response.status_code == 200 and "erro" not in response.json():
        data = response.json()
        ceptrue = data.get("cep", "").replace("-", "")
        cidade = data.get("localidade", "")
        rua = data.get("logradouro", "")
        bairro = data.get("bairro", "")
        uf = data.get("uf", "")
        logging.info(f"ViaCEP utilizado - CEP: {cep}, Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
        return ceptrue, cidade, rua, bairro, uf
    return None, None, None, None, None

def open_cep(cep):
    time.sleep(4)
    response = requests.get(f"https://opencep.com/v1/{cep}.json", timeout=5)
    if response.status_code == 200:
        data = response.json()
        ceptrue = data.get("cep", "").replace("-", "")
        cidade = data.get("cidade", "")
        rua = data.get("logradouro", "")
        bairro = data.get("bairro", "")
        uf = data.get("uf", "")
        logging.info(f"OpenCEP utilizado - CEP: {cep}, Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
        if not rua and not bairro:
            logging.info(f"OpenCEP retornou apenas Cidade: {cidade}, UF: {uf}")
        return ceptrue, cidade, rua, bairro, uf
    return None, None, None, None, None

def brasil_api(cep):
    time.sleep(4)
    response = requests.get(f"https://brasilapi.com.br/api/cep/v2/{cep}", timeout=5)
    if response.status_code == 200:
        data = response.json()
        ceptrue = data.get("cep", "").replace("-", "")
        cidade = data.get("city", "")
        rua = data.get("street", "")
        bairro = data.get("neighborhood", "")
        uf = data.get("state", "")
        logging.info(f"BrasilAPI utilizado - CEP: {cep}, Cidade: {cidade}, Rua: {rua}, Bairro: {bairro}, UF: {uf}")
        if not rua and not bairro:
            logging.info(f"BrasilAPI retornou apenas Cidade: {cidade}, UF: {uf}")
        return ceptrue, cidade, rua, bairro, uf
    return None, None, None, None, None


def update_bitrix24_record(deal_id, cidade, rua, bairro, uf):
    logging.info(f"Atualizando o Bitrix24 com Cidade: {cidade}, Rua: {rua}, Bairro: {bairro} UF: {uf} para o registro {deal_id}...")
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
        logging.info(f"Resposta da API Bitrix24: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logging.info(f"Registro {deal_id} atualizado com sucesso!")
        else:
            logging.error(f"Erro ao atualizar o registro no Bitrix24: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Erro ao conectar ao Bitrix24: {e}")

def get_number_from_bitrix(deal_id):
    url = f"{WEBHOOK_URL}crm.deal.get.json"
    params = {"ID": deal_id}

    try: 
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "result" in data and data["result"]:
            number = data["result"].get("UF_CRM_1700661252544", None)
            if number:
                logging.info(f"Campo UF_CRM_1700661252544 encontrado: {number}")
                return number
            else:
                logging.error(f"Campo UF_CRM_1700661252544 não encontrado no negócio {deal_id}")
                return None
        else:
            logging.error(f"Negócio {deal_id} não encontrado no Bitrix24")
            return None

    except requests.RequestException as e:
        logging.error(f"Erro ao buscar negócio {deal_id} no Bitrix24: {e}")
        return None
    

def update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, ceptrue, number):
    formatted_address = f"{rua}, {ceptrue}, {bairro}, {cidade} - {uf}, {number}"
    formatted_address = formatted_address.upper()
    logging.info(f"Atualizando o campo EnederoUtiliza(API): CEP: {ceptrue}, com Cidade: {cidade}, Rua: {rua}, Bairro: {bairro} UF: {uf} para o registro {deal_id}...")
    url = f"{WEBHOOK_URL}crm.deal.update.json"

    payload = {
        'ID': deal_id,
        'FIELDS': {
           'UF_CRM_1732711183': formatted_address
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        logging.info(f"Resposta da API Bitrix24: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logging.info(f"Registro {deal_id} atualizado com sucesso!")
        else:
            logging.error(f"Erro ao atualizar o registro no Bitrix24: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Erro ao conectar ao Bitrix24: {e}")


@app.route('/adress_full/<int:deal_id>/<string:cep>', methods=['POST'])
def adress_full(deal_id, cep):
    try:
        if not deal_id or not cep:
            logging.error(f"Parâmetros inválidos: deal_id={deal_id}, cep={cep}")
            return jsonify({"erro": "Parâmetros obrigatórios não fornecidos"}), 400
        
        # Obtém o número do Bitrix24
        number = get_number_from_bitrix(deal_id)

        if not number:
            logging.error(f"O campo 'number' não está preenchido para o negócio {deal_id}")
            return jsonify({"erro": "O número do endereço deve ser preenchido antes de continuar"}), 400

        # Consulta os dados do CEP
        ceptrue, cidade, rua, bairro, uf = get_city_and_uf(cep)

        if not (cidade and uf):
            logging.error("Erro ao obter cidade e UF para o CEP!")
            return jsonify({"erro": "Não foi possível obter dados para o CEP"}), 400

        # Formata o endereço com o número obtido
        formatted_address = f"{rua}, {ceptrue}, {bairro}, {cidade} - {uf}, {number}".upper()
        logging.info(f"Endereço formatado: {formatted_address}")

        # Atualiza o campo de endereço no Bitrix24
        update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, number, ceptrue)

        logging.info(f"Registro {deal_id} atualizado com o endereço formatado: {formatted_address}")
        return jsonify({"sucesso": f"Registro {deal_id} atualizado com sucesso!", "formatted_address": formatted_address}), 200

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"erro": f"Erro interno no servidor: {str(e)}"}), 500


@app.route('/atualizar_cidade_uf/<int:deal_id>/<string:cep>', methods=['POST'])
def atualizar_cidade_uf(deal_id, cep):
    try:
        if not deal_id or not cep:
            logging.error(f"Parâmetros inválidos: deal_id={deal_id}, cep={cep}")
            return jsonify({"erro": "Parâmetros obrigatórios não fornecidos"}), 400
        
        number = get_number_from_bitrix(deal_id)

        if not number:
            logging.error(f"Não foi possível obter o campo UF_CRM_1700661252544 para o negócio {deal_id}")


        ceptrue, cidade, rua, bairro, uf = get_city_and_uf(cep)

        if cidade and uf:
            update_bitrix24_record(deal_id, cidade, rua, bairro, uf)
            update_enderecoutilizado(deal_id, cidade, rua, bairro, uf, number, ceptrue)
            
            return jsonify({"sucesso": f"Registro {deal_id} atualizado com sucesso!"}), 200
        else:
            logging.error("Erro ao obter cidade e UF para o CEP!")
            return jsonify({"erro": "Não foi possível obter dados para o CEP"}), 400

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"erro": f"Erro interno no servidor: {str(e)}"}), 500

#rua, numero, bairro, cidade - estado, cep
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=35)
