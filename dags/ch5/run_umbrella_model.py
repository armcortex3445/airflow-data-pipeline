import airflow
import pendulum
import uuid
from airflow import DAG
from airflow.operators import DummyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.exceptions import AirflowSkipException
from airflow.decorators import task

ERP_CHANGE_DATE = airflow.utils.dates.days_ago(1)

def _pick_erp_system(**context):
    if(context["execution_date"] < ERP_CHANGE_DATE):
        return "fetch_sales_old"
    else :
        return "fetch_sales_new"

def _fetch_sales_old(**context):
    print("Fetching sales data (OLD)...")


def _fetch_sales_new(**context):
    print("Fetching sales data (NEW)...")


def _clean_sales_old(**context):
    print("Preprocessing sales data (OLD)...")


def _clean_sales_new(**context):
    print("Preprocessing sales data (NEW)...")

def _join_datasets(**context):
    print("Processing join data sets")

def _latest_only(**context):
    left_window=context["dag"].following_schedule(context["execution_date"])
    right_window=context["dag"].following_schedule(left_window);

    now=pendulum.now("UTC")
    if not left_window < now <= right_window:
        raise AirflowSkipException("Not the most recent run!")

with DAG(
    dag_id="run_umbrella_model"
) as dag :
    start_task = DummyOperator(task_id="start_task")

    pick_erp_system =BranchPythonOperator(
        task_id="pick_erp_system",
        python_callable=_pick_erp_system,
    )

    fetch_sales_old = PythonOperator(
        task_id="fetch_sales_old", python_callable=_fetch_sales_old
    )
    clean_sales_old = PythonOperator(
        task_id="clean_sales_old", python_callable=_clean_sales_old
    )

    fetch_sales_new = PythonOperator(
        task_id="fetch_sales_new", python_callable=_fetch_sales_new
    )
    clean_sales_new = PythonOperator(
        task_id="clean_sales_new", python_callable=_clean_sales_new
    )
    join_erp_branch=DummyOperator(
        task_id="join_erp_branch",
        trigger_rule="none_failed",
    )

    join_datasets = PythonOperator(
        task_id="join_datasets", python_callable=_join_datasets,)

    latest_only=PythonOperator(
        task_id="latests_only",
        python_callable=_latest_only,
    )

    @task
    def train_model():
        model_id=str(uuid.uuid4())
        return model_id
    

    @task
    def deploy_model(model_id : str):
        print(f"Deploying model {model_id}")
    
    
    fetch_weather = DummyOperator(task_id="fetch_weather")
    clean_weather = DummyOperator(task_id="clean_weather")

    model_id=train_model()
    deploy_model(model_id)
    

    start_task >> [pick_erp_system, fetch_weather]
    pick_erp_system >> [fetch_sales_old, fetch_sales_new]
    fetch_sales_old >> clean_sales_old
    fetch_sales_new >> clean_sales_new
    fetch_weather >> clean_weather
    [clean_sales_old, clean_sales_new] >> join_erp_branch
    [join_erp_branch, clean_weather] >> join_datasets
    join_datasets >> train_model
    latest_only >> deploy_model

