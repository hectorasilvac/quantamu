import httpx 
from fastapi import APIRouter, HTTPException, Query
from typing import Literal, Optional
from app.utils.responses import success_response, error_response

from app.services.market_data import fetch_market_data_service, fetch_multiple_market_data_service, fetch_customized_data_service

router = APIRouter()

@router.get("/market", summary="Obtiene una lista de símbolos")
async def get_market_data(
    symbol: str = Query(..., description="Símbolo a buscar"),  # Hacemos 'symbol' obligatorio
    timeframe: Literal["1d", "1wk", "1mo"] = Query(..., description="Intervalo de tiempo para los datos"),
    period1: Optional[int] = Query(None, description="Inicio del periodo en timestamp UNIX (opcional)"),
    period2: Optional[int] = Query(None, description="Fin del periodo en timestamp UNIX (opcional)"),
):
    """
    Endpoint para obtener datos de un símbolo específico.
    """
    # Llamar al servicio
    response = await fetch_market_data_service(symbol=symbol, timeframe=timeframe, period1=period1, period2=period2)
    data = response['data']
    
    # Verificar si el servicio devolvió un error
    if "error" in data:
        return error_response(
            f"Failed to fetch data for symbol {symbol} with timeframe {timeframe}",
            errors=[data["error"]]
        )

    # Devolver respuesta de éxito
    return success_response(data, f"Data retrieved for symbol {symbol} with timeframe {timeframe}")

@router.get("/market/bulk", summary="Obtiene datos de múltiples símbolos")
async def get_multiple_market_data(
    symbols: str = Query(..., description="Lista de símbolos separados por comas")
):
    """
    Endpoint para obtener datos de mercado para múltiples símbolos.
    """
    try:
        # Dividir los símbolos y llamar al servicio
        symbol_list = symbols.split(",")
        final_results = await fetch_multiple_market_data_service(symbol_list)

        # Devolver la respuesta final
        return success_response(
            {"results": final_results},
            "Market data retrieved for multiple symbols"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/market/custom", summary="Obtiene datos personalizados para múltiples símbolos")
async def get_data_customized(
    symbols: str = Query(..., description="Lista de símbolos separados por comas")
):
    """
    Endpoint para obtener datos personalizados para múltiples símbolos.
    """
    try:
        # Dividir los símbolos
        symbol_list = symbols.split(",")

        # Llamar al servicio para procesar los datos personalizados
        customized_results = await fetch_customized_data_service(symbol_list)

        # Devolver la respuesta final con éxito
        return success_response(
            {"results": customized_results},
            "Customized market data retrieved successfully"
        )
    except Exception as e:
        # Devolver error en caso de falla
        return error_response(
            "Failed to fetch customized market data",
            errors=[str(e)]
        )