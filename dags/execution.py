from airflow.decorators import task, task_group, dag
from pendulum import datetime
from utilities import tasksFunctions, constants
from utilities.customException import ArcanOutputNotFoundException, CloneRepositoryException, CheckoutRepositoryException, ArcanImageNotFoundException, ArcanExecutionException, DependencyGraphNotFoundException
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
    def create_version_directory(version:dict):
        try:
            tasksFunctions.create_version_directory(version)
        except (CloneRepositoryException, CheckoutRepositoryException) as e:
            raise AirflowFailException()

    @task(priority_weight=3, trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
    def delete_version_directory(version:dict):
        tasksFunctions.delete_version_directory(version['id'])

    @task(pool="docker_run_pool", priority_weight=2, retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def get_dependency_graph(version: dict, arcan_version: dict):
            if version['dependency_graph'] is None:
                try:
                    dependency_graph_file_name = tasksFunctions.create_dependency_graph(version=version, arcan_version=arcan_version)
                    tasksFunctions.save_dependency_graph(output_file_name=dependency_graph_file_name, version=version)
                    return dependency_graph_file_name
                except (ArcanImageNotFoundException, ArcanExecutionException, ArcanOutputNotFoundException) as e:
                    tasksFunctions.save_failed_analysis(version=version, arcan_version=arcan_version)
                    raise AirflowFailException(e)
            else:
                try:
                    dependency_graph_file_name = tasksFunctions.load_dependency_graph(version=version)
                    return dependency_graph_file_name
                except DependencyGraphNotFoundException as e:
                    tasksFunctions.save_failed_analysis(version=version, arcan_version=arcan_version)
                    raise AirflowFailException(e)                

    @task(pool="docker_run_pool", priority_weight=2, retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_analysis(version:dict, arcan_version:dict, dependency_graph_name: str):  
            try:  
                analysis_path = tasksFunctions.create_analysis(version, arcan_version, dependency_graph_name)
            except (ArcanImageNotFoundException, ArcanExecutionException, ArcanOutputNotFoundException) as e:
                tasksFunctions.save_failed_analysis(version=version, arcan_version=arcan_version)
                raise AirflowFailException(e)
            try:
                tasksFunctions.save_analysis(output_file_path=analysis_path, version=version, arcan_version=arcan_version)
            except Exception as e:
                tasksFunctions.save_failed_analysis(version=version, arcan_version=arcan_version)
                raise AirflowFailException(e)
    
    create_version_directory(version) >> create_analysis(version, arcan_version, get_dependency_graph(version, arcan_version)) >> delete_version_directory(version)


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