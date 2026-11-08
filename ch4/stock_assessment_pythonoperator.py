from urllib import request
import airflow
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator


USER_AGENT="airflow-study/1.0 (learning project; contact@example.com)"

dag=DAG(
    dag_id="stocksense",
    start_date=airflow.utils.dates.days_ago(1),
    schedule_interval="@hourly",
    template_searchpath="/tmp",  # write_to_postgres 가 읽는 SQL 파일의 위치
)

def _get_data(year,month,day,hour,output_path,**_):
    url=(
        "https://dumps.wikimedia.org/other/pageviews/"
        f"{year}/{year}-{month:0>2}/"
        f"pageviews-{year}{month:0>2}{day:0>2}-{hour:0>2}0000.gz"
    )
    # 위키미디어는 기본 User-Agent(Python-urllib)를 403으로 차단하므로 식별 가능한 헤더를 붙인다
    req=request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req) as resp, open(output_path, "wb") as f:
        f.write(resp.read())

get_data=PythonOperator(
    task_id="get_data",
    python_callable=_get_data,
    op_kwargs={
        "year": "{{execution_date.year}}",
        "month": "{{execution_date.month}}",
        "day": "{{execution_date.day}}",
        "hour": "{{execution_date.hour}}",
        "output_path": "/tmp/wikipageviews-{{execution_date.year}}{{execution_date.month}}{{execution_date.day}}{{execution_date.hour}}0000.gz"
    },
    dag=dag
)

extract_gz=BashOperator(
    task_id="extract_gz",
    bash_command="gunzip --force /tmp/wikipageviews-{{execution_date.year}}{{execution_date.month}}{{execution_date.day}}{{execution_date.hour}}0000.gz",
    dag=dag,
)

def _fetch_pageviews(filename,pagenames,execution_date,**_):
    result=dict.fromkeys(pagenames,0)
    with open(filename,"r") as f:
        for line in f:
            domain_code,page_title,view_counts,_=line.split(" ")
            if domain_code == "en" and page_title in pagenames:
                result[page_title]=int(view_counts)

    # 결과를 INSERT 문으로 변환해 SQL 파일로 저장한다. 실제 적재는 다음 task(write_to_postgres)가 수행한다.
    # id 가 PRIMARY KEY(자동 증가)이므로 매시간 실행마다 페이지별 행이 이력으로 쌓인다.
    # datetime 에는 DB 기본값(적재 시각) 대신 데이터가 속한 시간인 execution_date 를 명시한다.
    with open("/tmp/postgres_query.sql","w") as f:
        for pagename,pageviewcount in result.items():
            f.write(
                "INSERT INTO dag_data.pageview_counts (pagename, pageviewcount, datetime) "
                f"VALUES ('{pagename}', {pageviewcount}, '{execution_date}');\n"
            )

fetch_pageviews=PythonOperator(
    task_id="fetch_pageviews",
    python_callable=_fetch_pageviews,
    op_kwargs={
        "filename" : "/tmp/wikipageviews-{{execution_date.year}}{{execution_date.month}}{{execution_date.day}}{{execution_date.hour}}0000",
        "pagenames": {
            "Google",
            "Amazon",
            "Apple",
            "Microsoft",
            "Meta",
        },
        "execution_date": "{{ execution_date }}",
    },
    dag=dag,
)

write_to_postgres=SQLExecuteQueryOperator(
    task_id="write_to_postgres",
    conn_id="my_postgres",
    sql="postgres_query.sql",
    dag=dag,
)

get_data >> extract_gz >> fetch_pageviews >> write_to_postgres
