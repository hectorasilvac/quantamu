from datetime import datetime, timezone
from app.services.holiday_checker import is_first_business_day_of_week, is_first_business_day_of_month

def transform_yahoo_data(raw_data: dict, timeframe: str) -> dict:
    """
    Transforma los datos de la API de Yahoo Finance al formato deseado.
    :param raw_data: Diccionario crudo recibido de Yahoo Finance.
    :param timeframe: Granularidad de los datos (por ejemplo, '1mo', '1wk').
    :return: Datos transformados en el formato esperado.
    """
    try:
        # Extraer la parte relevante del raw_data
        result = raw_data.get("chart", {}).get("result", [])[0]

        if not result:
            raise ValueError("No se encontraron datos en la respuesta.")

        # Extraer información meta
        meta = result["meta"]
        timestamps = result["timestamp"]
        indicators = result["indicators"]["quote"][0]

        # Calcular fechas de inicio y fin usando timezone-aware datetime
        date_start = datetime.fromtimestamp(timestamps[0], timezone.utc).strftime("%Y-%m-%d")
        date_end = datetime.fromtimestamp(timestamps[-1], timezone.utc).strftime("%Y-%m-%d")

        # Generar lista de datos bulk
        bulk_data = []
        for idx, timestamp in enumerate(timestamps):
            bulk_data.append({
                "date": datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d"),
                "open": indicators["open"][idx],
                "high": indicators["high"][idx],
                "low": indicators["low"][idx],
                "close": indicators["close"][idx],
                "volume": indicators["volume"][idx]
            })
        
        # Filtrar registros futuros
        bulk_data = filter_future_dates(bulk_data)
        
        # Ordenar bulk_data por fecha descendente
        bulk_data = sorted(bulk_data, key=lambda x: x["date"], reverse=True)
        
        # Verificar y eliminar el primer registro si corresponde
        if timeframe == "1wk" and not is_first_business_day_of_week():
            bulk_data.pop(0)
        elif timeframe == "1mo" and not is_first_business_day_of_month():
            bulk_data.pop(0)

        # Transformar al formato esperado
        transformed_data = {
            "data": {
                "symbol": meta["symbol"],
                "timeFrame": timeframe,
                "dateStart": date_start,
                "dateEnd": date_end,
                "bulk": bulk_data
            },
            "error": None
        }

        return transformed_data

    except Exception as e:
        # Retornar un error si ocurre algún problema
        return {
            "data": None,
            "error": str(e)
        }

def filter_future_dates(bulk_data: list) -> list:
    """
    Filtra registros con fechas posteriores al día actual.
    :param bulk_data: Lista de datos de mercado con fechas.
    :return: Lista filtrada sin registros futuros.
    """
    # Obtener la fecha actual del sistema en formato "YYYY-MM-DD"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Filtrar registros cuya fecha sea igual o anterior a la fecha actual
    filtered_data = [record for record in bulk_data if record["date"] <= today]
    
    return filtered_data
