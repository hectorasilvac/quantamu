def determine_unusual_volume(day_data: dict) -> bool:
    """
    Determina si el volumen reciente o del día anterior es inusual (muy alto o muy bajo)
    en comparación con los 9 días anteriores.
    :param day_data: Datos diarios (debería incluir un campo 'bulk' con volúmenes).
    :return: True si el volumen reciente o el del día anterior es inusual, False de lo contrario.
    """
    bulk_data = day_data.get("bulk", [])

    if len(bulk_data) < 10:
        # Si no hay suficientes datos, no se puede determinar un volumen inusual
        return False

    # Volúmenes más recientes
    recent_volume = bulk_data[0]["volume"]
    previous_volume = bulk_data[1]["volume"]

    # Verificar condiciones de volumen reciente
    is_recent_unusual_low = is_unusual_in_range(recent_volume, bulk_data, start=1, end=10, check="low")
    is_recent_unusual_high = is_unusual_in_range(recent_volume, bulk_data, start=0, end=10, check="high")

    # Verificar condiciones de volumen del día anterior
    is_previous_unusual_low = is_unusual_in_range(previous_volume, bulk_data, start=2, end=10, check="low")
    is_previous_unusual_high = is_unusual_in_range(previous_volume, bulk_data, start=1, end=10, check="high")

    # Si alguna condición se cumple, el volumen es inusual
    return (
        is_recent_unusual_low or is_recent_unusual_high or
        is_previous_unusual_low or is_previous_unusual_high
    )

def is_unusual_in_range(volume: int, bulk_data: list[dict], start: int, end: int, check: str) -> bool:
    """
    Verifica si un volumen es el más bajo o más alto dentro de un rango de días.
    :param volume: Volumen a comparar.
    :param bulk_data: Lista de datos históricos.
    :param start: Índice inicial del rango.
    :param end: Índice final del rango (exclusivo).
    :param check: "low" para verificar si es el menor, "high" para verificar si es el mayor.
    :return: True si el volumen cumple la condición, False de lo contrario.
    """
    volumes_in_range = [entry["volume"] for entry in bulk_data[start:end] if "volume" in entry]

    if not volumes_in_range:
        return False

    if check == "low":
        return volume < min(volumes_in_range)
    elif check == "high":
        return volume > max(volumes_in_range)
    else:
        raise ValueError("El parámetro 'check' debe ser 'low' o 'high'")

import httpx
from datetime import datetime

import httpx
from datetime import datetime

async def determine_seasonality(symbol: str) -> str:
    """
    Determina la estacionalidad para el mes actual de un símbolo basado en datos de una API externa.
    :param symbol: Símbolo para el cual calcular la estacionalidad.
    :return: "up", "down" o "neutral" según la tendencia promedio del cambio.
    """
    url = f"https://phx.unusualwhales.com/api/seasonality/{symbol}/year-month"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    try:
        # Hacer la solicitud HTTP con encabezados
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        # Verificar si la solicitud fue exitosa
        response.raise_for_status()

        # Decodificar la respuesta JSON y extraer los datos
        json_response = response.json()
        data = json_response.get("data", [])

        # Verificar si hay datos
        if not isinstance(data, list) or not data:
            return "unknow"

        # Obtener el mes actual
        current_month = datetime.now().month

        # Filtrar los datos para el mes actual
        filtered_data = [
            item for item in data
            if isinstance(item, dict) and item.get("month") == current_month
        ]

        if not filtered_data:
            return "unknow"

        # Calcular el promedio del cambio
        average_change = sum(float(item.get("change", 0)) for item in filtered_data) / len(filtered_data)

        # Determinar tendencia como string
        return "up" if average_change > 0 else "down" if average_change < 0 else "unknow"

    except httpx.HTTPError:
        return "unknow"

    except Exception:
        return "unknow"
