from pathlib import Path
from airflow import DAG
from pendulum import datetime
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor


dag1 = DAG(
    dag_id="listing_6_04_dag01",
    start_date=datetime(
        2026,11,11
    ),
    schedule_interval="0 16 * * *"

)
dag2=DAG(
    dag_id="report_results",
    start_date=datetime(2026,11,11),
    schedule_interval="0 20 * * *"
)

report = EmptyOperator(task_id="report", dag=dag2)

for supermarket_id in range(1,5):

    copy_task_id = f"copy_to_raw_supermarket_{supermarket_id}"
    process_task_id = f"process_supermarket_{supermarket_id}"
    
    copy = EmptyOperator(task_id=copy_task_id, dag=dag1)
    process = EmptyOperator(task_id=process_task_id, dag=dag1)

    copy >> process # pyright: ignore[reportUnusedExpression]

    wait = ExternalTaskSensor(
    task_id="wait_for_process_supermarket",
    external_dag_id="listing_6_04_dag01",
    external_link_id=process_task_id,
    execution_delta=datetime.timedelta(hours=4)
    dag=dag2
    )
    wait >> report # pyright: ignore[reportUnusedExpression]
