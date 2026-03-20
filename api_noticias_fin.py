import os
from datetime import date
from fastapi import FastAPI
from anthropic import Anthropic
from tavily import TavilyClient

app = FastAPI()
client = Anthropic()
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

tools = [
    {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes del rubro finanzas y global macro en internet",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "El término de búsqueda"
                }
            },
            "required": ["query"]
        }
    }
]

def ejecutar_agente():
    hoy = date.today().strftime("%d/%m/%Y")
    hoy_query = date.today().strftime("%d %B %Y")

    system_prompt = f"""Eres un agente especializado en noticias de finanzas y global macro.
    Cuando el usuario te pida noticias, usás la tool buscar_noticias para buscar 
    información actualizada.
    IMPORTANTE: 
      - Solo mostrás noticias del día de hoy ({hoy})
      - Presentás entre 5 y 8 noticias, entre 2 y 3 del mundo y entre 5 y 8 de de latam
      - Cada noticia debe tener: titular, resumen de 2-3 líneas y fuente
      - Organizalas por categorías: economicas, politicas, mercados de valores, etc.
      - Respondés siempre en español."""


    messages = [{"role": "user", "content": f"¿Cuáles son las noticias de QSR del día de hoy {hoy_query}?"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    resultado = tavily.search(
                        query=block.input["query"],
                        search_depth="advanced",
                        max_results=5,
                        include_raw_content=False,
                        days=1
                    )

                    noticias_texto = ""
                    for r in resultado["results"]:
                        noticias_texto += f"- Título: {r['title']}\n  Resumen: {r['content'][:300]}\n  Fuente: {r['url']}\n\n"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": noticias_texto
                    })

            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            break

@app.get("/noticiasFin")
def obtener_noticias():
    resultado = ejecutar_agente()
    return {"noticias": resultado}