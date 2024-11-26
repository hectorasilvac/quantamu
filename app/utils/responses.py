def success_response(data, message):
    """Estructura una respuesta JSON de éxito"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": []
    }

def error_response(message, errors=None):
    """Estructura una respuesta JSON de error"""
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors or []
    }
