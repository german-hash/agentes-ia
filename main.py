import os
import yfinance as yf
from datetime import date
from fastapi import FastAPI, Header, HTTPException
from anthropic import Anthropic
from tavily import TavilyClient

app = FastAPI()
client = Anthropic()
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# =====================
# CONFIGURACION ACCIONES
# =====================
ACCIONES_EEUU = [
    "AAPL", "MSFT", "GOOGL", "META","BRK-B", "JNJ", "JPM", "XOM",
    "PG", "V", "UNH", "HD", "CVX", "MRK", "ABBV", "PEP", "KO" ,"BAC"
]
ACCIONES_EUROPA = [
    "ASML.AS", "NESN.SW", "NOVN.SW", "ROG.SW", "SAP.DE", "SIE.DE",
    "TTE.PA", "LVMH.PA", "OR.PA", "AZN.L", "HSBA.L", "BP.L"
]
ACCIONES_CHINA = [
    "BABA", "TCEHY", "JD", "BIDU", "NIO", "PDD", "NTES", "VIPS"
]

# =====================
# TOOLS NOTICIAS QSR
# =====================
tools_noticias_qsr = [
    {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes de QSR en internet",
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

# =====================
# AGENTE NOTICIAS QSR
# =====================
def ejecutar_agente_noticias_qsr():
    hoy = date.today().strftime("%d/%m/%Y")
    hoy_query = date.today().strftime("%d %B %Y")

    system_prompt = f"""Eres un agente especializado en noticias de QSR.
    Cuando el usuario te pida noticias, usás la tool buscar_noticias para buscar 
    información actualizada.
    IMPORTANTE: 
    - Solo mostrás noticias del día de hoy ({hoy})
    - Presentás entre 5 y 8 noticias, entre 2 y 3 del mundo y entre 5 y 8 de de latam
    - El texto debe estar escrito para ser LEÍDO EN VOZ ALTA, sin markdown
    - No uses símbolos como #, *, **, ---, emojis ni caracteres especiales
    - Escribí en texto plano corrido, como un locutor de radio
    - Cada noticia debe tener: título, resumen de 2 líneas y fuente
    - Separás cada noticia con un punto y aparte
    - El texto total no debe superar los 3500 caracteres
    - Prioizar noticias de digitalizacion e ecommerce
    - Priorizas noticias de cadenas globales como McDonald's, Starbucks, Burger King, KFC, Subway, Pizza Hut, Domino's, y cadenas relevantes en latinoamerica
    - Respondés siempre en español"""

    messages = [{"role": "user", "content": f"¿Cuáles son las noticias de QSR del día de hoy {hoy_query}?"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system_prompt,
            tools=tools_noticias_qsr,
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

# =====================
# TOOLS NOTICIAS FIN
# =====================
tools_noticias_fin = [
    {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes de finanzas y global macro en internet",
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

# =====================
# AGENTE NOTICIAS FIN
# =====================
def ejecutar_agente_noticias_fin():
    hoy = date.today().strftime("%d/%m/%Y")
    hoy_query = date.today().strftime("%d %B %Y")

    system_prompt = f"""Eres un agente especializado en noticias de finanzas y macro global.
    Cuando el usuario te pida noticias, usas la tool buscar_noticias para buscar 
    informacion actualizada.
    IMPORTANTE: 
    - Solo mostras noticias del dia de hoy ({hoy})
    - Presentas entre 5 y 8 noticias con foco en Latinoamerica y global macro
    - El texto debe estar escrito para ser LEIDO EN VOZ ALTA, sin markdown
    - No uses simbolos como #, *, **, ---, emojis ni caracteres especiales
    - Escribi en texto plano corrido, como un locutor de radio
    - Cada noticia debe tener: titulo, resumen de 2 lineas y fuente
    - Separa cada noticia con un punto y aparte
    - El texto total no debe superar los 3500 caracteres
    - Temas prioritarios: tasas de interes, inflacion, mercados de valores, politica economica, commodities
    - Respondés siempre en español"""

    messages = [{"role": "user", "content": f"¿Cuáles son las noticias de finanzas y macro global del día de hoy {hoy_query}?"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system_prompt,
            tools=tools_noticias_fin,
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

# =====================
# TOOLS NOTICIAS
# =====================
tools_noticias = [
    {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes de tecnología en internet",
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

# =====================
# AGENTE NOTICIAS
# =====================
def ejecutar_agente_noticias():
    hoy = date.today().strftime("%d/%m/%Y")
    hoy_query = date.today().strftime("%d %B %Y")

    system_prompt = f"""Eres un agente especializado en noticias de tecnología.
    Cuando el usuario te pida noticias, usás la tool buscar_noticias para buscar 
    información actualizada.
    IMPORTANTE: 
    - Solo mostrás noticias del día de hoy ({hoy})
    - Presentás entre 5 y 8 noticias
    - El texto debe estar escrito para ser LEÍDO EN VOZ ALTA, sin markdown
    - No uses símbolos como #, *, **, ---, emojis ni caracteres especiales
    - Escribí en texto plano corrido, como un locutor de radio
    - Cada noticia debe tener: título, resumen de 2 líneas y fuente
    - Separás cada noticia con un punto y aparte
    - El texto total no debe superar los 3500 caracteres
    - Respondés siempre en español"""

    messages = [{"role": "user", "content": f"¿Cuáles son las noticias de tecnología del día de hoy {hoy_query}?"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system_prompt,
            tools=tools_noticias,
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

# =====================
# AGENTE ACCIONES
# =====================
def obtener_datos_accion(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        cashflow = ticker.cashflow
        fcf_actual = 0
        fcf_anterior = 0
        if cashflow is not None and not cashflow.empty:
            if "Free Cash Flow" in cashflow.index:
                fcf_values = cashflow.loc["Free Cash Flow"].dropna()
                if len(fcf_values) >= 1:
                    fcf_actual = float(fcf_values.iloc[0])
                if len(fcf_values) >= 2:
                    fcf_anterior = float(fcf_values.iloc[1])
        return {
            "symbol": symbol,
            "nombre": info.get("longName", symbol),
            "precio": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "pe": info.get("trailingPE", None),
            "market_cap": info.get("marketCap", 0),
            "fcf_actual": fcf_actual,
            "fcf_anterior": fcf_anterior,
            "pais": info.get("country", "N/A")
        }
    except Exception as e:
        return None

def ejecutar_agente_acciones():
    hoy = date.today().strftime("%d/%m/%Y")
    todas = ACCIONES_EEUU + ACCIONES_EUROPA + ACCIONES_CHINA

    candidatas = []
    for symbol in todas:
        datos = obtener_datos_accion(symbol)
        if datos is None:
            continue
        market_cap = datos["market_cap"] or 0
        pe = datos["pe"]
        fcf_actual = datos["fcf_actual"]
        fcf_anterior = datos["fcf_anterior"]
        try:
            pe_valor = float(pe) if pe is not None else None
        except (ValueError, TypeError):
            pe_valor = None
        es_large_cap = market_cap > 10_000_000_000
        pe_bajo = pe_valor is not None and 0 < pe_valor < 25
        fcf_bueno = fcf_actual > 0 and fcf_actual >= fcf_anterior
        if es_large_cap and pe_bajo and fcf_bueno:
            candidatas.append(datos)

    resumen = f"Fecha: {hoy}\n\nAcciones candidatas:\n\n"
    for a in candidatas:
        resumen += f"- {a['symbol']} ({a['nombre']}) [{a['pais']}]: "
        resumen += f"Precio: ${a['precio']:.2f}, "
        try:
            resumen += f"PE: {float(a['pe']):.1f}, " if a['pe'] else "PE: N/A, "
        except:
            resumen += "PE: N/A, "
        resumen += f"Market Cap: ${a['market_cap']/1e9:.1f}B, "
        resumen += f"FCF actual: ${a['fcf_actual']/1e9:.2f}B, "
        resumen += f"FCF anterior: ${a['fcf_anterior']/1e9:.2f}B\n"

    if not candidatas:
        return "No se encontraron acciones que cumplan los criterios hoy."

    system_prompt = """Eres un analista financiero experto.
    Con los datos proporcionados, seleccionas las TOP 10 acciones del dia.
    Criterios: Large Cap, PE bajo, Free Cash Flow positivo y creciente.
    Para cada accion presentas: nombre, simbolo, precio, PE, Market Cap y una linea explicando por que la elegiste.
    El formato debe ser claro y conciso, ideal para leer en Telegram.
    Respondés siempre en español."""

    messages = [{"role": "user", "content": f"Analizá estas acciones y seleccioná el TOP 10:\n\n{resumen}"}]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )

    return response.content[0].text

# =====================
# ENDPOINTS
# =====================
@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/noticias")
def obtener_noticias(x_api_key: str = Header(None)):
    if x_api_key != os.environ["API_SECRET_KEY"]:
        raise HTTPException(status_code=401, detail="No autorizado")
    resultado = ejecutar_agente_noticias()
    return {"noticias": resultado}

@app.get("/noticias_fin")
def obtener_noticias_fin(x_api_key: str = Header(None)):
    if x_api_key != os.environ["API_SECRET_KEY"]:
        raise HTTPException(status_code=401, detail="No autorizado")
    resultado = ejecutar_agente_noticias_fin()
    return {"noticias_fin": resultado}

@app.get("/noticias_qsr")
def obtener_noticias_qsr(x_api_key: str = Header(None)):
    if x_api_key != os.environ["API_SECRET_KEY"]:
        raise HTTPException(status_code=401, detail="No autorizado")
    resultado = ejecutar_agente_noticias_qsr()
    return {"noticias_qsr": resultado}

@app.get("/acciones")
def obtener_acciones(x_api_key: str = Header(None)):
    if x_api_key != os.environ["API_SECRET_KEY"]:
        raise HTTPException(status_code=401, detail="No autorizado")
    resultado = ejecutar_agente_acciones()
    return {"acciones": resultado}