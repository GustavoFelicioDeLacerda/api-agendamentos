from datetime import datetime, timedelta, timezone
from .models import Agendamento
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


HORARIOS_DISPONIVEIS = [
    "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
]


def is_feriado(data):
    url = f"{settings.BRASILAPI_URL}/api/feriados/v1/{data.year}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        feriados = response.json()
        data_str = data.strftime("%Y-%m-%d")
        return any(f["date"] == data_str for f in feriados)
    except Exception:
        logger.error("Erro ao consultar feriados na BrasilAPI")
        return False


def get_horarios_disponiveis(data, prestador):
    if is_feriado(data):
        return []

    tz = timezone(timedelta(hours=-3))

    agendamentos_do_dia = Agendamento.objects.filter(
        prestador=prestador,
        data_horario__date=data,
        estado__in=[Agendamento.Estado.NAO_CONFIRMADO, Agendamento.Estado.CONFIRMADO]
    )

    horarios_ocupados = set()
    for agendamento in agendamentos_do_dia:
        horario = agendamento.data_horario.astimezone(tz).strftime("%H:%M")
        horarios_ocupados.add(horario)

    return [h for h in HORARIOS_DISPONIVEIS if h not in horarios_ocupados]