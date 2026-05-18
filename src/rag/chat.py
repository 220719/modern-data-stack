from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
from src.rag.indexador import get_vectorstore
from src.config import settings

SYSTEM_PROMPT = """Você é um assistente especialista em vigilância epidemiológica de arboviroses no Brasil.
Você tem acesso a dados reais de dengue, chikungunya e zika de 31 municípios brasileiros (2020-2025).

Use APENAS as informações fornecidas no contexto abaixo para responder.
Se não souber a resposta com base no contexto, diga isso claramente.
Responda sempre em português, de forma clara e objetiva.

Contexto dos dados epidemiológicos:
{context}

Pergunta: {question}

Resposta:"""


def buscar_contexto(pergunta: str, k: int = 5) -> str:
    vs = get_vectorstore()
    docs = vs.similarity_search(pergunta, k=k)
    return "\n\n---\n\n".join([d.page_content for d in docs])


def responder(pergunta: str) -> str:
    logger.info(f"Pergunta: {pergunta}")

    contexto = buscar_contexto(pergunta)

    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
    )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain  = prompt | llm | StrOutputParser()

    resposta = chain.invoke({
        "context":  contexto,
        "question": pergunta,
    })

    logger.success(f"Resposta gerada: {len(resposta)} caracteres")
    return resposta


def responder_stream(pergunta: str):
    contexto = buscar_contexto(pergunta)

    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.1,
        streaming=True,
    )

    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain  = prompt | llm | StrOutputParser()

    for chunk in chain.stream({
        "context":  contexto,
        "question": pergunta,
    }):
        yield chunk