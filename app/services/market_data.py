import asyncio
import httpx
from asyncio import Semaphore
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.holiday_checker import is_holiday, is_weekend
from app.services.transformers import transform_yahoo_data
from app.utils.analyzers import determine_unusual_volume, determine_seasonality

# Crear un semáforo global para limitar solicitudes concurrentes
semaphore = Semaphore(10)

async def fetch_market_data_service(symbol: str, timeframe: str, period1: int = None, period2: int = None):
    """
    Obtiene datos de un stock desde Yahoo Finance API, basados en el símbolo y granularidad.
    """
    try:
        # Lógica para calcular periodos por defecto
        if not period1:
            period1 = int((datetime.now() - timedelta(days=90)).timestamp())
        if not period2:
            period2 = int(datetime.now().timestamp())

        url = f"{settings.market_data_api_url}/{symbol}"
        query_params = {
            "events": "capitalGain|div|split",
            "formatted": "true",
            "includeAdjustedClose": "true",
            "interval": timeframe,
            "period1": period1,
            "period2": period2,
            "region": "US",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=query_params)
            response.raise_for_status()

        raw_data = response.json()
        transformed_data = transform_yahoo_data(raw_data, timeframe)

        return transformed_data  # Devolver solo los datos transformados

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error while fetching data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

async def fetch_market_data_service_limited(symbol: str, timeframe: str, period1: int = None, period2: int = None) -> dict:
    """
    Realiza solicitudes con límite de concurrencia usando un semáforo.
    """
    async with semaphore:  # Bloquea el acceso si ya hay 10 solicitudes activas
        return await fetch_market_data_service(symbol, timeframe, period1, period2)

def calculate_periods(timeframe: str) -> tuple[int, int]:
    """
    Calcula los valores de period1 y period2 basados en la granularidad.
    :param timeframe: '1d', '1wk', '1mo'
    :return: Tuple con period1 (inicio) y period2 (fin) en formato timestamp UNIX.
    """
    now = datetime.now()
    start = now

    if timeframe == "1d":
        # Retrocede hasta encontrar los últimos 10 días hábiles
        business_days = 0
        while business_days < 11:
            start -= timedelta(days=1)
            if not is_weekend(start) and not is_holiday(start):
                business_days += 1

    elif timeframe == "1wk":
        # Retrocede 4 semanas hábiles (4 semanas completas)
        start -= timedelta(weeks=4)

    elif timeframe == "1mo":
        # Retrocede 4 meses (primer día del mes hace 4 meses)
        start = now.replace(day=1) - timedelta(days=1)  # Último día del mes anterior
        for _ in range(3):  # Retrocede 4 meses iterativamente
            start = start.replace(day=1) - timedelta(days=1)

    period1 = int(start.timestamp())
    period2 = int(now.timestamp())
    return period1, period2

async def fetch_symbol_data(symbol: str) -> dict:
    """
    Realiza tres consultas para un símbolo con temporalidades '1d', '1wk', y '1mo'.
    :param symbol: Símbolo a consultar.
    :return: Resultados para las tres consultas.
    """
    timeframes = ["1d", "1wk", "1mo"]
    tasks = []

    # Crear tareas para cada temporalidad
    for tiemframe in timeframes:
        period1, period2 = calculate_periods(tiemframe)
        tasks.append(fetch_market_data_service_limited(symbol, tiemframe, period1, period2))

    # Ejecutar todas las tareas de forma concurrente
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Formatear los resultados
    formatted_results = {
        tiemframe: result if not isinstance(result, Exception) else {"error": str(result)}
        for tiemframe, result in zip(timeframes, results)
    }

    return {"symbol": symbol, "data": formatted_results}

async def fetch_multiple_market_data_service(symbols: list[str]) -> list[dict]:
    """
    Obtiene datos para múltiples símbolos concurrentemente, con tres consultas por símbolo.
    :param symbols: Lista de símbolos a consultar.
    :return: Resultados combinados y formateados para todos los símbolos.
    """
    # Crear tareas asíncronas para cada símbolo
    tasks = [fetch_symbol_data(symbol) for symbol in symbols]

    # Ejecutar todas las tareas de forma concurrente
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Formatear los resultados
    formatted_results = []
    for result in raw_results:
        if isinstance(result, Exception):
            continue  # Saltar errores en este nivel, manejar en el endpoint si es necesario
        
        # Formatear cada resultado al formato esperado
        symbol_data = {
            "symbol": result["symbol"],
            "temporalities": {
                "day": result["data"].get("1d", {}).get("data", {}).get("bulk", []),
                "week": result["data"].get("1wk", {}).get("data", {}).get("bulk", []),
                "month": result["data"].get("1mo", {}).get("data", {}).get("bulk", []),
            }
        }
        formatted_results.append(symbol_data)
    
    return formatted_results

async def fetch_customized_data_service(symbols: list[str]) -> list[dict]:
    """
    Servicio para obtener y manipular datos personalizados de mercado.
    :param symbols: Lista de símbolos a procesar.
    :return: Lista de resultados personalizados por símbolo.
    """
    # Obtener datos base para todos los símbolos
    raw_results = await fetch_multiple_market_data_service(symbols)

    customized_results = []

    for result in raw_results:
        symbol = result["symbol"]
        day_data = result["temporalities"]["day"]

        # Calcular si el volumen es inusual
        unusual_volume = determine_unusual_volume({"bulk": day_data})

        # Determinar la estacionalidad
        seasonality = await determine_seasonality(symbol)

        # Agregar solo los datos relevantes
        customized_results.append({
            "symbol": symbol,
            "customized_data": {
                "unusual_volume": unusual_volume,
                "seasonality": seasonality
            }
        })

    return customized_results
