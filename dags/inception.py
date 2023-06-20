from pendulum import datetime
from airflow.decorators import dag, task
from utilities import tasksFunctions, constants
from airflow.exceptions import AirflowFailException
from utilities.customException import GitRestApiProjectNotFoundException, GitRestApiValidationFailedException

@task(retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def get_project_list(project_range: dict):
    return tasksFunctions.get_project_list(project_range)

@task(retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def get_project_range():
    return tasksFunctions.get_project_range()

@task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY, multiple_outputs=True)
def get_last_version(project: dict):
    return {'project': project, 'last_version_analyzed':tasksFunctions.get_last_version(project=project)}

@task(trigger_rule='all_done', retries=constants.GIT_REST_API_RETRIES, retry_delay=constants.GIT_REST_API_RETRY_DELAY)
def get_new_version_list(arg: dict):
    project = arg['project']
    last_version_analyzed = arg['last_version_analyzed']
    try:
        return tasksFunctions.get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
    except (GitRestApiProjectNotFoundException, GitRestApiValidationFailedException) as e:
        raise AirflowFailException(e)

@task(trigger_rule='all_done', retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def save_new_project_versions(version_list: dict):
    tasksFunctions.save_new_project_versions(version_list=version_list)

@task(trigger_rule='all_done', retries=constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
def update_project_range(project_range: dict, project_list: int):
    number_of_projects_considered = len(project_list)
    tasksFunctions.update_project_range(project_range=project_range, number_of_projects_considered = number_of_projects_considered)

@dag( 
    schedule="@daily", 
    start_date=datetime(2023, 1, 1),
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
    last_version_analyzed = get_last_version.expand(project=project_list)
    version_list = get_new_version_list.expand(arg=last_version_analyzed)
    save_new_project_versions.expand(version_list=version_list) >> update_project_range(project_range=project_range, project_list = project_list)

inception()