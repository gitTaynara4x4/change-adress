# 🏙️ Preenchimento Automático de Endereço via CEP no Bitrix24 🇧🇷  
(Scroll down for English version 🇺🇸)

Este projeto automatiza o preenchimento de campos de endereço em negócios (deals) no Bitrix24 com base no CEP informado, consultando automaticamente múltiplas APIs públicas para obter cidade, bairro, rua, estado e montando o endereço completo.

## ✅ O que ele faz?
- Recebe o CEP e o ID do negócio.
- Consulta automaticamente 3 fontes (BrasilAPI, ViaCEP, OpenCEP).
- Preenche os campos personalizados no Bitrix24: cidade, estado, bairro, rua e campo de endereço completo.
- Marca "CEP INVÁLIDO" caso nenhuma das APIs retorne resultado.
- Pode ser integrado a automações externas ou acionado manualmente via POST.

## 🔧 Como funciona?
- API Flask com três rotas principais:
  - `/adress_full/<deal_id>/<cep>`: preenche todos os campos, incluindo endereço completo.
  - `/atualizar_cidade_uf/<deal_id>/<cep>`: atualiza cidade, estado, rua e bairro.
  - `/cidade_formatada_uf/<deal_id>`: busca o CEP no negócio e atualiza apenas cidade e UF.
- Utiliza variáveis de ambiente (`.env`) para segurança da URL de Webhook.
- Integra-se diretamente com a API oficial do Bitrix24.

## 🛡️ Segurança
- Autenticação via Webhook protegido por `.env`.
- Logs de erros e respostas de API para auditoria.
- Timeout e tratamento de falhas nas consultas.

## 📈 Benefícios
- Redução de erros de digitação e retrabalho.
- Endereços padronizados automaticamente.
- Atualização rápida e confiável de registros no Bitrix24.
- Integração com bots, sistemas externos e formulários públicos.

> Deseja automatizar o preenchimento de endereços na sua operação Bitrix24? Fale com a gente. 😉

---

# 🏙️ Automatic Address Autofill via ZIP in Bitrix24 🇺🇸

This project automates the filling of address fields in Bitrix24 deals using the provided ZIP/CEP code. It queries multiple public APIs to retrieve the city, state, street, and neighborhood, and assembles the full address.

## ✅ What does it do?
- Receives a ZIP code and deal ID.
- Automatically queries 3 APIs (BrasilAPI, ViaCEP, OpenCEP).
- Fills in Bitrix24 custom fields: city, state, neighborhood, street, and full address.
- Sets a “CEP INVÁLIDO” (Invalid ZIP) flag if no valid data is returned.
- Can be triggered via external automations or manually with POST.

## 🔧 How does it work?
- Flask API with three main endpoints:
  - `/adress_full/<deal_id>/<cep>`: fills all address fields including full formatted address.
  - `/atualizar_cidade_uf/<deal_id>/<cep>`: updates city, state, street, and neighborhood.
  - `/cidade_formatada_uf/<deal_id>`: fetches ZIP from the deal and updates only city and state.
- Uses environment variables (`.env`) for webhook security.
- Fully integrated with Bitrix24 official API.

## 🛡️ Security
- Auth via secure Webhook URL stored in `.env`.
- Logging and error tracking included.
- API requests include timeout and fallback mechanisms.

## 📈 Benefits
- Avoid manual entry errors and rework.
- Ensure consistent and standardized address formats.
- Real-time updates in Bitrix24 with minimal effort.
- Can be connected to bots, external CRMs, or public forms.

> Want to automate address completion in your Bitrix24 deals? Let's talk! 😉
