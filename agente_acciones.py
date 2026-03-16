import os
import yfinance as yf
from datetime import date
from anthropic import Anthropic

client = Anthropic()

# Lista de acciones candidatas por mercado
ACCIONES_EEUU = [
    "AAPL", "MSFT", "GOOGL", "META", "BRK-B", "JNJ", "JPM", "XOM", 
    "PG", "V", "UNH", "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "BAC"
]

ACCIONES_EUROPA = [
    "ASML.AS", "NESN.SW", "NOVN.SW", "ROG.SW", "SAP.DE", "SIE.DE",
    "TTE.PA", "LVMH.PA", "OR.PA", "AZN.L", "HSBA.L", "BP.L"
]

ACCIONES_CHINA = [
    "BABA", "TCEHY", "JD", "BIDU", "NIO", "PDD", "NTES", "VIPS"
]

def obtener_datos_accion(symbol):
    """Obtiene fundamentos de una accion via yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Free Cash Flow
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
        print(f"Error obteniendo {symbol}: {e}")
        return None

def ejecutar_agente():
    hoy = date.today().strftime("%d/%m/%Y")
    
    todas_las_acciones = ACCIONES_EEUU + ACCIONES_EUROPA + ACCIONES_CHINA
    
    print(f"Analizando {len(todas_las_acciones)} acciones...")
    
    candidatas = []
    for symbol in todas_las_acciones:
        print(f"  Obteniendo {symbol}...")
        datos = obtener_datos_accion(symbol)
        if datos is None:
            continue
        
        # Filtros: Large Cap + PE bajo + FCF positivo y creciente
        market_cap = datos["market_cap"] or 0
        pe = datos["pe"]
        fcf_actual = datos["fcf_actual"]
        fcf_anterior = datos["fcf_anterior"]
        
        es_large_cap = market_cap > 10_000_000_000  # +10B
        try:
            pe_valor = float(pe) if pe is not None else None
        except (ValueError, TypeError):
            pe_valor = None
        pe_bajo = pe_valor is not None and 0 < pe_valor < 25
        fcf_bueno = fcf_actual > 0 and fcf_actual >= fcf_anterior
        
        if es_large_cap and pe_bajo and fcf_bueno:
            candidatas.append(datos)
            print(f"  ✅ {symbol} cumple los criterios")
    
    print(f"\nTotal candidatas: {len(candidatas)}")
    
    # Preparamos resumen para Claude
    resumen = f"Fecha: {hoy}\n\nAcciones que cumplen Large Cap + PE < 25 + FCF positivo creciente:\n\n"
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
        return "No se encontraron acciones que cumplan todos los criterios hoy."
    
    # Claude analiza y selecciona el top 10
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

if __name__ == "__main__":
    resultado = ejecutar_agente()
    print("\n📈 TOP 10 Acciones del día:\n")
    print(resultado)