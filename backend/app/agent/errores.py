class ErrorDelAgente(Exception):
    """Base de los errores del agente, sin importar el proveedor"""


class LimiteDeConsultas(ErrorDelAgente):
    """El proveedor rechazó la petición por exceso de consultas"""


class ProveedorNoDisponible(ErrorDelAgente):
    """El proveedor del modelo falló o no respondió correctamente"""
