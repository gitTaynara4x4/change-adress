import requests
import time

def change_url(n, c):
    if n==0 or n==1:
        return f"https://brasilapi.com.br/api/cep/v2/{c}"
    else:
        return f"https://opencep.com/v1/{c}.json"

def get_city_from_api(k, link, c):
    w=0
    data =requests.get(link).json()
    while 1:
        if k==0 or k==1:
            try:
                return data["city"].upper()
            except:
                w+=1
                if w>1:
                    return None
                link2 =change_url(k, c)
                data =requests.get(link2).json()
        else:
            try:
                return data["localidade"].upper()
            except:
                w+=1
                if w>1:
                    return None
                link2 =change_url(k, c)
                data =requests.get(link2).json()

def get_deals () :
    url = f"https://marketingsolucoes.bitrix24.com.br/rest/35002/7a2nuej815yjx5bg/crm.deal.list?filter[>BEGINDATE]=2025-01-01&filter[!UF_CRM_1731588487]=&select[]=UF_CRM_1731588487&select[]=UF_CRM_1700661314351"
    start = 0
    i=0
    n=1
    t=0

    while True :
        time.sleep(3)
        res = requests.get(f"{url}&start={start}")
        data = res.json()
        deals = data["result"]

        for deal in deals :
            cep = deal["UF_CRM_1700661314351"]
            city = deal["UF_CRM_1731588487"]

            if cep and int(deal["ID"])>205606:
                print(deal["ID"], cep, city, n,"/",data["total"]//(start+50))
                cep = cep.replace(",","").replace("-", "").replace(".", "")
                time.sleep(20)
                if i==0:
                    url2 = f"https://viacep.com.br/ws/{cep}/json/"  
                elif i==1:
                    url2 = f"https://opencep.com/v1/{cep}.json"
                elif i==2:
                    url2 = f"https://brasilapi.com.br/api/cep/v2/{cep}"
                
                city_from_api = get_city_from_api(i, url2, cep)

                if city_from_api is None:
                    print(f"{deal["ID"]} CEP Incorreto")
                elif city_from_api != city:
                    res = requests.post(f"http://127.0.0.1:1474/cidade_formatada_uf/{deal["ID"]}")
                    print(f"{deal["ID"]} Antigo nome: {city}, Novo nome: {city_from_api}")

                i+=1
                if i>2:
                    i=0
        
                
        if "next" not in data:
            break
        else:
            n+=1
            start=data["next"]


get_deals()

