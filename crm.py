
import gspread
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2.service_account import Credentials
import re
import os

# ==========================
# OPENAI
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_openai = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==========================
# FUNÇÕES
# ==========================

def normalizar_numero(numero):
    numero = re.sub(r"\D", "", str(numero))

    # já vem com código do país (ex: 55, 1, 351 etc.)
    if len(numero) >= 12:
        return "+" + numero

    # caso BR sem DDI
    if len(numero) == 11:
        return "+55" + numero

    # fallback genérico
    return "+" + numero


def mensagem_sem_cadastro():

    return """
Olá! 👋

No momento não localizei seus dados em nossa lista de atendimento.

Nós organizamos os contatos através das respostas do formulário de interesse, por isso respondemos seguindo essa lista para garantir um atendimento mais rápido e organizado.

Você chegou a preencher nosso formulário recentemente?

Caso ainda não tenha preenchido, me avise que envio para você. 😊
"""


def pode_atender(lead):

    if lead["Status"] == "✅ Matriculado":
        return False

    return True


def prioridade(lead):

    if lead["Tipo de Lead"] == "🔥 HOT":
        return 1

    if lead["Tipo de Lead"] == "🌤️ MORNO":
        return 2

    return 3


def criar_contexto(lead):

    return f"""
Você é Juan, atendente da CEPF.

Informações do lead:

Nome: {lead['Nome']}
WhatsApp: {lead['WhatsApp']}
Curso de interesse: {lead['Curso Inicial']}
Curso atual: {lead['Curso Atual']}
CNH: {lead['CNH']}
Tipo de lead: {lead['Tipo de Lead']}
Status: {lead['Status']}
Ponto crucial: {lead['Ponto Crucial']}
Observações: {lead['Observações']}

Informações da CEPF:

- Cursos com teoria online e prática presencial.
- A prática acontece em ambiente real.
- O objetivo é preparar o aluno para o mercado.
- Responda como um atendente humano.
- Seja objetivo.
- Não invente informações.
- Foque em ajudar e converter a matrícula.
- Utilize sempre as informações do CRM.
"""

# ==========================
# GOOGLE SHEETS
# ==========================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

import json

creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

creds = Credentials.from_service_account_info(
    creds_json,
    scopes=SCOPES
)

client = gspread.authorize(creds)

PLANILHA_KEY = os.getenv("PLANILHA_KEY")

spreadsheet = client.open_by_key(PLANILHA_KEY)

aba = spreadsheet.worksheet("CRM")

dados = aba.get_all_records()

# ==========================
# RESUMO CRM
# ==========================

quentes = [x for x in dados if x["Tipo de Lead"] == "🔥 HOT"]
mornos = [x for x in dados if x["Tipo de Lead"] == "🌤️ MORNO"]
frios = [x for x in dados if x["Tipo de Lead"] == "❄️ FRIO"]

print("\n=== RESUMO CRM ===")
print(f"Total de leads: {len(dados)}")
print(f"🔥 Quentes: {len(quentes)}")
print(f"🌤️ Mornos: {len(mornos)}")
print(f"❄️ Frios: {len(frios)}")

# ==========================
# BUSCAR LEAD
# ==========================

def buscar_lead(numero_recebido):

    numero_recebido = normalizar_numero(numero_recebido)

    for lead in dados:

        numero_planilha = normalizar_numero(
            lead["WhatsApp"]
        )

        if numero_planilha == numero_recebido:
            return lead

    return None

# ==========================
# TESTE DE ATENDIMENTO
# ==========================

numero = input("\nDigite o WhatsApp: ")

lead_encontrado = buscar_lead(numero)

if not lead_encontrado:

    print(mensagem_sem_cadastro())

else:

    print("\n=== LEAD ENCONTRADO ===")

    print("Nome:", lead_encontrado["Nome"])
    print("Curso:", lead_encontrado["Curso Inicial"])
    print("CNH:", lead_encontrado["CNH"])
    print("Tipo:", lead_encontrado["Tipo de Lead"])
    print("Status:", lead_encontrado["Status"])

    mensagem_cliente = input(
        "\nMensagem do cliente: "
    )

    prompt = f"""
{criar_contexto(lead_encontrado)}

Mensagem do cliente:

{mensagem_cliente}
"""

    resposta = client_openai.responses.create(
        model="gpt-5",
        input=prompt
    )

    print("\n=== RESPOSTA IA ===\n")

    print(resposta.output_text)

# ==========================
# GERAR RESUMO CRM
# ==========================

def gerar_resumo_crm(lead, historico):

    prompt = f"""
Você é um assistente de CRM da CEPF.

Analise a conversa abaixo e gere um resumo profissional.

Regras:
- Máximo 5 linhas.
- Foque apenas em informações importantes para vendas.
- Não invente nada.
- Cite interesse, curso, CNH, objeções, prazo e próximos passos.
- Escreva em português.

Dados do lead:

Nome: {lead['Nome']}
Curso: {lead['Curso Inicial']}
CNH: {lead['CNH']}

Conversa:

{historico}
"""

    resposta = client_openai.responses.create(
        model="gpt-5",
        input=prompt
    )

    return resposta.output_text


# ==========================
# LOCALIZAR LINHA DO LEAD
# ==========================

def encontrar_linha(numero_recebido):

    numero_recebido = normalizar_numero(numero_recebido)

    linhas = aba.get_all_records()

    for indice, lead in enumerate(linhas, start=2):

        numero_planilha = normalizar_numero(
            lead["WhatsApp"]
        )

        if numero_planilha == numero_recebido:
            return indice

    return None


# ==========================
# SALVAR OBSERVAÇÃO
# ==========================

def salvar_observacao(numero_recebido, resumo):

    linha = encontrar_linha(numero_recebido)

    if not linha:
        print("Lead não encontrado para atualização.")
        return

    cabecalho = aba.row_values(1)

    coluna_observacoes = (
        cabecalho.index("Observações") + 1
    )

    observacao_antiga = aba.cell(
        linha,
        coluna_observacoes
    ).value

    nova_observacao = f"""
{observacao_antiga}

----------------------
{resumo}
""".strip()

    aba.update_cell(
        linha,
        coluna_observacoes,
        nova_observacao
    )

    print("Resumo salvo no CRM com sucesso.")
