from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'arboviroses',
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'email_on_failure': False,
}

def treinar_modelos():
    from src.ml.treinar import treinar_todos
    df = treinar_todos()
    print(f"✅ {len(df)} modelos treinados")
    print(df[['municipio', 'doenca', 'r2', 'mae']].to_string())

def detectar_alertas():
    from src.storage.database import query
    df = query("""
        SELECT municipio, doenca, casos_estimados, nivel_alerta, media_movel_4s
        FROM mart_arboviroses
        WHERE (municipio, doenca, semana_epidemiologica) IN (
            SELECT municipio, doenca, MAX(semana_epidemiologica)
            FROM mart_arboviroses GROUP BY municipio, doenca
        )
        AND nivel_alerta >= 3
        ORDER BY nivel_alerta DESC, casos_estimados DESC
    """)
    if df.empty:
        print("✅ Nenhum município em alerta elevado")
    else:
        print(f"⚠️ {len(df)} situações de alerta detectadas:")
        print(df.to_string())

with DAG(
    dag_id="dag_ml_semanal",
    description="Retrain semanal dos modelos ML + detecção de alertas",
    default_args=default_args,
    schedule_interval="0 8 * * 1",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["arboviroses", "ml"],
) as dag:

    t1 = PythonOperator(
        task_id="treinar_modelos",
        python_callable=treinar_modelos,
    )

    t2 = PythonOperator(
        task_id="detectar_alertas",
        python_callable=detectar_alertas,
    )

    t1 >> t2