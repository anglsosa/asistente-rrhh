from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel

PRIMA_PORCENTAJE = 30  # Reglamento interior, Artículo 24
FUNDAMENTO = (
    "Reglamento interior, Artículo 21",
    "Reglamento interior, Artículo 24",
    "LFT, Artículo 76",
)

"""
Las cuentas las hace el código, nunca el modelo
"""


class ResultadoVacaciones(BaseModel):
    """
    Días de vacaciones y prima vacacional, con su fundamento para citarlo
    """

    anios_antiguedad: int
    dias: int
    prima_porcentaje: int
    monto_prima: Decimal | None
    fundamento: list[str]
    nota: str | None


def dias_de_vacaciones(anios: int) -> int:
    """
    Días que corresponden por antigüedad, según el artículo 76 de la LFT
    """
    if anios < 1:
        return 0
    if anios <= 5:
        return 12 + 2 * (anios - 1)
    return 20 + 2 * ((anios - 6) // 5 + 1)


def calcular_vacaciones(
    anios_antiguedad: int, salario_diario: Decimal | None = None
) -> ResultadoVacaciones:
    """
    Calcula días de vacaciones y, si hay salario, el monto de la prima vacacional
    """
    if anios_antiguedad < 0:
        raise ValueError("La antigüedad no puede ser negativa")
    dias = dias_de_vacaciones(anios_antiguedad)
    monto = None
    if salario_diario is not None:
        bruto = salario_diario * dias * PRIMA_PORCENTAJE / 100
        monto = bruto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    nota = "Aún no cumple un año de servicio: todavía no tiene vacaciones." if dias == 0 else None
    return ResultadoVacaciones(
        anios_antiguedad=anios_antiguedad,
        dias=dias,
        prima_porcentaje=PRIMA_PORCENTAJE,
        monto_prima=monto,
        fundamento=list(FUNDAMENTO),
        nota=nota,
    )
