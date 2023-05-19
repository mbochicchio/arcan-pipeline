import pendulum
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task
from utilities import tasksFunctions, constants
from airflow.exceptions import AirflowFailException
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from utilities.customException import GitRestApiProjectNotFoundException

@task(trigger_rule='all_done')
def create_cross_dag_arguments(project_list):
    tasksFunctions.create_cross_dag_arguments(project_list)

@task()
def wait():
    tasksFunctions.wait()

@task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
def get_last_version(project: dict):
    return tasksFunctions.get_last_version(project=project)

@task(pool=constants.GIT_REST_API_POOL, retries=constants.GIT_REST_API_RETRIES, retry_delay=constants.GIT_REST_API_RETRY_DELAY, max_retry_delay=constants.GIT_REST_API_MAX_RETRY_DELAY)
def get_new_version_list(project: dict, last_version_analyzed: dict):
    try:
        return tasksFunctions.get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
    except GitRestApiProjectNotFoundException as e:
        raise AirflowFailException(e)

@task(retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def save_new_project_versions(version_list: dict):
    tasksFunctions.save_new_project_versions(version_list=version_list)

def trigger_dagrun_dag():
    return TriggerDagRunOperator(
        task_id="trigger_dependent_dag",
        trigger_dag_id=constants.EXECUTION_DAG_ID,
        wait_for_completion=False,
    )

with DAG('inception', 
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
    default_args={
        'owner': constants.DEFAULT_OWNER,
        "retries": constants.DEFAULT_RETRIES,
        "retry_delay": constants.DEFAULT_RETRY_DELAY,
        "retry_exponential_backoff": constants.DEFAULT_RETRY_EXPONENTIAL_BACKOFF,
        "max_retry_delay": constants.DEFAULT_MAX_RETRY_DELAY,
    },
) as inception:
    project_list = tasksFunctions.get_project_list()
    create_cross_dag_arguments = create_cross_dag_arguments(project_list)
    wait = wait()
    trigger_dagrun_dag = trigger_dagrun_dag()
    for project in project_list:
        group_id=str(project['id'])
        with TaskGroup(group_id=group_id, dag=inception) as paths:
            last_version_analyzed = get_last_version(project=project)
            version_list = get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
            save_new_project_versions(version_list=version_list) >> create_cross_dag_arguments >> wait >> trigger_dagrun_dag
    