from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'arboviroses',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

def coletar_casos():
    from src.ingestion.infodengue import coletar_todos
    from src.storage.database import inicializar_banco, inserir_casos
    inicializar_banco()
    casos = coletar_todos(ano_start=2025, ano_end=2025)
    inserir_casos(casos)
    print(f"✅ {len(casos)} registros de casos coletados")

def coletar_clima():
    from src.ingestion.openmeteo import coletar_clima_todos
    from src.storage.database import inserir_clima
    from datetime import datetime
    clima = coletar_clima_todos(
        data_inicio="2025-01-01",
        data_fim=datetime.now().strftime("%Y-%m-%d"),
    )
    inserir_clima(clima)
    print(f"✅ {len(clima)} registros de clima coletados")

def rodar_dbt():
    import subprocess
    result = subprocess.run(
        ["dbt", "run", "--project-dir", "/opt/airflow/infra/dbt",
         "--profiles-dir", "/opt/airflow/infra/dbt"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt falhou: {result.stderr}")
    print("✅ dbt run concluído")

with DAG(
    dag_id="dag_coleta_semanal",
    description="Coleta semanal de casos e clima + transformações dbt",
    default_args=default_args,
    schedule_interval="0 6 * * 1",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["arboviroses", "ingestão"],
) as dag:

    t1 = PythonOperator(
        task_id="coletar_casos",
        python_callable=coletar_casos,
    )

    t2 = PythonOperator(
        task_id="coletar_clima",
        python_callable=coletar_clima,
    )

    t3 = PythonOperator(
        task_id="rodar_dbt",
        python_callable=rodar_dbt,
    )

    [t1, t2] >> t3