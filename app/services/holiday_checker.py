from datetime import datetime, timedelta

# Lista de días festivos en EE.UU.
US_HOLIDAYS = [
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27",
    "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"
]

def is_weekend(date: datetime) -> bool:
    """Verifica si la fecha es un fin de semana."""
    return date.weekday() >= 5  # Sábado (5) o domingo (6)

def is_holiday(date: datetime) -> bool:
    """Verifica si la fecha es un día festivo en EE.UU."""
    return date.strftime("%Y-%m-%d") in US_HOLIDAYS

def is_first_business_day_of_week() -> bool:
    """Verifica si hoy es el primer día laboral de la semana."""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Hoy no debe ser fin de semana ni feriado
    if is_holiday(today) or is_weekend(today):
        return False

    # Ayer debe haber sido un feriado o fin de semana
    if is_holiday(yesterday) or is_weekend(yesterday):
        return True

    return False

def is_first_business_day_of_month() -> bool:
    """Verifica si hoy es el primer día laboral del mes."""
    today = datetime.now().date()

    # Hoy no debe ser fin de semana ni feriado
    if is_holiday(today) or is_weekend(today):
        return False

    # Busca el primer día laboral del mes
    first_day = today.replace(day=1)
    while is_holiday(first_day) or is_weekend(first_day):
        first_day += timedelta(days=1)

    # Verifica si hoy es ese primer día laboral
    return today == first_day
