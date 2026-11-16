from datetime import datetime
from airflow import DAG  # type: ignore[reportMissingImports]
from airflow.operators.bash import BashOperator  # type: ignore[reportMissingImports]

with DAG(
    dag_id="dag_turnos_clinica",
    description="Ejecucion diaria del proceso ETL de turnos",
    start_date=datetime(2024, 1, 1),
    schedule="0 2 * * *",
    catchup=False,
    tags=["turnos", "clinica"],
) as dag:

    correr_etl = BashOperator(
        task_id="procesar_turnos",
        bash_command="cd /opt/airflow/proyecto && python pipeline.py",
    )
