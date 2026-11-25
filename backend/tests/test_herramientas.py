from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.tools.tickets import RegistroTickets
from app.tools.vacaciones import calcular_vacaciones, dias_de_vacaciones


@pytest.mark.parametrize(
    ("anios", "dias"),
    [(0, 0), (1, 12), (2, 14), (5, 20), (6, 22), (10, 22), (11, 24), (16, 26), (31, 32)],
)
def test_dias_de_vacaciones_segun_la_lft(anios: int, dias: int) -> None:
    assert dias_de_vacaciones(anios) == dias


def test_prima_con_el_porcentaje_del_reglamento() -> None:
    resultado = calcular_vacaciones(3, salario_diario=Decimal("500"))

    assert resultado.dias == 16
    assert resultado.monto_prima == Decimal("2400.00")


def test_antiguedad_negativa_es_un_error() -> None:
    with pytest.raises(ValueError, match="negativa"):
        calcular_vacaciones(-1)


@pytest.mark.anyio
async def test_tickets_con_folio_consecutivo(tmp_path: Path) -> None:
    registro = RegistroTickets(tmp_path / "tickets.jsonl")

    primero = await registro.crear("EMP-0042", "Finiquito", "Quiere saber cómo se calcula.", "alta")
    segundo = await registro.crear("EMP-0042", "Permiso", "Quiere un permiso sin goce.", "media")

    assert primero.folio.endswith("-00001")
    assert segundo.folio.endswith("-00002")


@pytest.mark.anyio
async def test_ticket_rechaza_nombres_reales(tmp_path: Path) -> None:
    registro = RegistroTickets(tmp_path / "tickets.jsonl")

    with pytest.raises(ValidationError):
        await registro.crear("Juan Pérez", "Tema", "Un resumen suficientemente largo.", "media")
