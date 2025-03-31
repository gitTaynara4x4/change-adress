ids = [
   
]

import requests
import time

def getDeals () :
    url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/7a2nuej815yjx5bg/crm.deal.list?filter[>BEGINDATE]=2025-01-01&filter[!UF_CRM_1731588487]=&select[]=UF_CRM_1731588487&select[]=UF_CRM_1700661314351"
    start = 0

    array = []

    while True :
        time.sleep(3)
        res = requests.get(f"{url}&start={start}")
        data = res.json()

        deals = data["result"]

        for deal in deals :
            cep = deal["UF_CRM_1700661314351"]
            city = deal["UF_CRM_1731588487"]


            if cep :
                print(cep)
                cep = cep.replace(",","").replace("-", "")
                time.sleep(10)
                url2 = f"https://viacep.com.br/ws/{cep}/json/"
                res2 = requests.get(url2)
                data2 = res2.json()

                print(data2)

                city_from_api = data2["localidade"].upper()

                if city_from_api != city :
                    print(f"{city} é diferente de {city_from_api}. Adicionando id {deal["ID"]}")
                    array.append(deal["ID"])

        print(start)

        if "next" not in data :
            break

    global ids
    ids = array

getDeals()

for id in ids :
    res = requests.post(f"http://127.0.0.1:5000/cidade_formatada_uf/{id}")
    data = res.json()
    print(data["message"])
