
import os
from datetime import date
from anthropic import Anthropic
from tavily import TavilyClient

# Clientes
client = Anthropic()
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Definición de la tool de búsqueda
tools = [
    {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes de tecnología en internet",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "El término de búsqueda, ej: 'últimas noticias tecnología 2026'"
                }
            },
            "required": ["query"]
        }
    }
]

# System prompt del agente
hoy = date.today().strftime("%d/%m/%Y")

system_prompt = f"""Eres un agente especializado en noticias de tecnología.
Cuando el usuario te pida noticias, usás la tool buscar_noticias para buscar 
información actualizada.
IMPORTANTE: 
- Solo mostrás noticias del día de hoy ({hoy})
- Presentás MÍNIMO 5 noticias, idealmente 8 o más
- Cada noticia debe tener: titular, resumen de 2-3 líneas y fuente
- Organizalas por categorías: IA, Gadgets, Startups, Software, etc.
- Respondés siempre en español."""

# Loop agentico
def ejecutar_agente(pregunta_usuario):
    messages = [{"role": "user", "content": pregunta_usuario}]
    
    print(f"\n🤖 Agente procesando: {pregunta_usuario}\n")
    
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
            
            # Procesamos TODAS las tool calls que mandó el agente
            for block in response.content:
                if block.type == "tool_use":
                    print(f"🔍 Buscando: {block.input['query']}")
                    
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
                    
                    # Agregamos resultado por CADA tool call
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": noticias_texto
                    })
            
            # Mandamos TODOS los resultados juntos
            messages.append({"role": "user", "content": tool_results})
        
        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print("📰 Respuesta del agente:\n")
                    print(block.text)
            break

# Ejecutar
if __name__ == "__main__":
    hoy = date.today().strftime("%d %B %Y")
    ejecutar_agente(f"¿Cuáles son las noticias de tecnología del día de hoy {hoy}?")