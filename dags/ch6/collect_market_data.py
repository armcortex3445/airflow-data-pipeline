from pathlib import Path
from airflow import DAG
from pendulum import datetime
from airflow.sensors.python import PythonSensor
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.empty import EmptyOperator


def _wait_for_supermarket(supermarket_id) :
    supermarket_path=Path("/data/"+supermarket_id)
    data_files=supermarket_path.glob("data-*.csv")
    success_file=supermarket_path / "_SUCCESS"

    return data_files and success_file.exists();

dag1 = DAG(
    dag_id="listing_6_04_dag01",
    start_date=datetime(
        2026,11,11
    ),
    schedule_interval="0 16 * * *"

)

for supermarket_id in range(1,5):

    wait_task = PythonSensor(
        task_id=f"wait_for_supermarket_{supermarket_id}",
        python_callable=_wait_for_supermarket,
        op_kwargs={"supermarket_id" : f"supermarket{supermarket_id}"},
        dag=dag1
    )
    copy = EmptyOperator(task_id=f"copy_to_raw_supermarket_{supermarket_id}", dag=dag1)
    process = EmptyOperator(task_id=f"process_supermarket_{supermarket_id}", dag=dag1)

    trigger_create_metrics_dag=TriggerDagRunOperator(
        task_id=f"trigger_create_metrics_dag_supermarket_${supermarket_id}",
        trigger_dag_id="create_metrics",
        dag=dag1,
    )
    wait_task >> copy >> process >> trigger_create_metrics_dag # pyright: ignore[reportUnusedExpression]


dag2=DAG(
    dag_id="create_metrics",
    start_date=datetime(2026,11,11),
    schedule_interval=None
)

compute_differences = EmptyOperator(task_id="compute_differences", dag=dag2)
update_dashboard = EmptyOperator(task_id="update_dashboard", dag=dag2)
notify_new_data = EmptyOperator(task_id="notify_new_data", dag=dag2)
compute_differences >> update_dashboard # pyright: ignore[reportUnusedExpression]
