import pendulum
from airflow.decorators import dag, task, task_group
from utilities import tasksFunctions, constants
from airflow.exceptions import AirflowFailException
from utilities.customException import GitRestApiProjectNotFoundException

@task(retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def get_project_list(project_range: dict):
    return tasksFunctions.get_project_list(project_range)

@task(retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def get_project_range():
    return tasksFunctions.get_project_range()

@task(priority_weight=1, retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
def get_last_version(project: dict):
    return tasksFunctions.get_last_version(project=project)

@task(priority_weight=2, retries=constants.GIT_REST_API_RETRIES, retry_delay=constants.GIT_REST_API_RETRY_DELAY, max_retry_delay=constants.GIT_REST_API_MAX_RETRY_DELAY)
def get_new_version_list(project: dict, last_version_analyzed: dict):
    try:
        return tasksFunctions.get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
    except GitRestApiProjectNotFoundException as e:
        raise AirflowFailException(e)

@task(priority_weight=3, retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def save_new_project_versions(version_list: dict):
    tasksFunctions.save_new_project_versions(version_list=version_list)

@task(trigger_rule='all_done', retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def update_project_range(project_range: dict, project_list: int):
    number_of_projects_considered = len(project_list)
    tasksFunctions.update_project_range(project_range=project_range, number_of_projects_considered = number_of_projects_considered)

@task_group()
def create_version_list(project: dict):
    last_version_analyzed = get_last_version(project=project)
    version_list = get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
    save_new_project_versions(version_list=version_list)

@dag( 
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
)
def inception():
    project_range = get_project_range()
    project_list = get_project_list(project_range)
    create_version_list.expand(project=project_list) >> update_project_range(project_range=project_range, project_list = project_list)

inception()