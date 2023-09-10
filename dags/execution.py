from airflow.decorators import task, task_group, dag
from pendulum import datetime
from utilities import tasksFunctions, constants
from utilities.customException import ArcanOutputNotFoundException, CloneRepositoryException, CheckoutRepositoryException, ArcanExecutionException, MaximumExecutionTimeExeededException
from airflow.exceptions import AirflowFailException

@task(retries=constants.SETTINGS_RETRIES, retry_delay=constants.SETTINGS_RETRY_DELAY)
def get_version_list(version_range: int, arcan_version: dict):
    return tasksFunctions.get_version_list(version_range=version_range, arcan_version=arcan_version)

@task(retries=constants.SETTINGS_RETRIES, retry_delay=constants.SETTINGS_RETRY_DELAY)
def get_arcan_version():
    return tasksFunctions.get_arcan_version()

@task(retries=constants.SETTINGS_RETRIES, retry_delay=constants.SETTINGS_RETRY_DELAY)
def get_version_range():
    return tasksFunctions.get_version_range()

@task_group()
def execute(version: dict, arcan_version: dict):

    @task(priority_weight=1, retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
    def create_version_directory(version:dict, project:dict, arcan_version: dict):
        try:
            tasksFunctions.create_version_directory(version, project)
        except (CloneRepositoryException, CheckoutRepositoryException) as e:
            tasksFunctions.save_parsing(version=version, status=e.status)
            tasksFunctions.save_analysis(version=version, arcan_version=arcan_version, status=e.status)    
            raise AirflowFailException(e)

    @task(retries=constants.SETTINGS_RETRIES, retry_delay=constants.SETTINGS_RETRY_DELAY)
    def get_project_of_version(project_id):
        return tasksFunctions.get_project_by_id(project_id)

    @task(priority_weight=3, trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
    def delete_version_directory(version:dict):
        tasksFunctions.delete_version_directory(version['id'])

    @task(pool="docker_run_pool", priority_weight=2, retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def get_dependency_graph(version: dict, project:dict, arcan_version: dict):           
        dependency_graph_file = tasksFunctions.get_dependency_graph(version=version)
        if not dependency_graph_file:
            try:
                dependency_graph_file = tasksFunctions.create_dependency_graph(version=version, project=project, arcan_version=arcan_version)
                dependency_graph_id = tasksFunctions.save_dependency_graph(output_file_path=dependency_graph_file)
                tasksFunctions.save_parsing(version=version, dependency_graph=dependency_graph_id)
            except (ArcanExecutionException, ArcanOutputNotFoundException, MaximumExecutionTimeExeededException) as e:
                tasksFunctions.save_parsing(version=version, status=e.status)
                tasksFunctions.save_analysis(version=version, arcan_version=arcan_version, status=e.status)
                raise AirflowFailException(e)
        return dependency_graph_file
 
    @task(pool="docker_run_pool", priority_weight=2, retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_analysis(version:dict, project:dict, arcan_version:dict, dependency_graph_local_path: str):  
        try: 
            analysis_result_file = tasksFunctions.create_analysis(version, project, arcan_version, dependency_graph_local_path)
            analysis_result_id = tasksFunctions.save_analysis_result(output_file_path=analysis_result_file)
            tasksFunctions.save_analysis(version=version, arcan_version=arcan_version, analysis_result=analysis_result_id)
        except (ArcanExecutionException, ArcanOutputNotFoundException, MaximumExecutionTimeExeededException) as e:
            tasksFunctions.save_analysis(version=version, arcan_version=arcan_version, status=e.status)
            raise AirflowFailException(e)
    
    get_project_task = get_project_of_version(version['project'])
    get_dependency_graph_task = get_dependency_graph(version, get_project_task, arcan_version)
    create_analysis_task = create_analysis(version, get_project_task, arcan_version, get_dependency_graph_task)
    get_project_task >> create_version_directory(version, get_project_task, arcan_version) >> get_dependency_graph_task >> create_analysis_task >> delete_version_directory(version)


@dag(
    start_date=datetime(2023, 1, 1),
    schedule="@continuous",
    max_active_runs=1, 
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
def execution():
    version_range = get_version_range()
    arcan_version = get_arcan_version()
    version_list = get_version_list(version_range, arcan_version= arcan_version)
    execute.partial(arcan_version=arcan_version).expand(version=version_list)

execution()