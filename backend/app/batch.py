"""CU032 – ejecución manual o desde el programador de tareas del SO (cron / Programador de tareas):

    python -m app.batch
"""
from .entidades import models  # noqa: F401  (registra las tablas)
from .gestores.proceso_batch import ProcesoBatchFinalizacionCuestionarios

if __name__ == "__main__":
    resultado = ProcesoBatchFinalizacionCuestionarios().ejecutar()
    print(f"Cuestionarios pasados a Incompleto: {resultado['incompletos']} | a Sin Contestar: {resultado['sin_contestar']}")
