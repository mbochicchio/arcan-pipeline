from airflow.decorators import task, task_group, dag
from pendulum import datetime
from utilities import tasksFunctions, constants
from utilities.customException import ArcanOutputNotFoundException, CloneRepositoryException, CheckoutRepositoryException, ArcanImageNotFoundException, ArcanExecutionException
from airflow.exceptions import AirflowFailException
import logging

@task
def get_version_list(version_range: int, arcan_version: dict):
    return tasksFunctions.get_version_list(version_range=version_range, arcan_version=arcan_version)

@task
def get_arcan_version():
    return tasksFunctions.get_arcan_version()

@task
def get_version_range():
    return tasksFunctions.get_version_range()

@task(retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def create_version_directory(version:dict):
    try:
        tasksFunctions.create_version_directory(version)
    except (CloneRepositoryException, CheckoutRepositoryException) as e:
        raise AirflowFailException()

@task(trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def delete_version_directory(version:dict):
    return tasksFunctions.delete_version_directory(version)

@task(trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def clean_output_directory(version: dict):
    return tasksFunctions.delete_output_directory(version['id'])

@task()
def skip():
    logging.info("Dependency Graph already created")

@task_group()
def execute(version: dict, arcan_version: dict):

    @task.branch()
    def check(version: dict):
        if version['dependency_graph'] is None:
            return 'execute.create_dependency_graph'
        return 'execute.skip' 

    @task(retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_dependency_graph(version: dict):
            try:
                return tasksFunctions.create_dependency_graph(version)
            except (ArcanImageNotFoundException, ArcanExecutionException) as e:
                raise AirflowFailException(e)

    @task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
    def save_dependency_graph(dependency_graph: dict):
            try:
                return tasksFunctions.save_dependency_graph(dependency_graph=dependency_graph)
            except ArcanOutputNotFoundException as e:
                raise AirflowFailException(e)
            
    @task(trigger_rule='none_failed_min_one_success', retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_analysis(version:dict, arcan_version:dict):  
            try:  
                return tasksFunctions.create_analysis(version, arcan_version)
            except (ArcanImageNotFoundException, ArcanExecutionException) as e:
                raise AirflowFailException(e)

    @task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
    def save_analysis(analysis:dict):
            try:
                tasksFunctions.save_analysis(analysis=analysis)
            except ArcanOutputNotFoundException as e:
                raise AirflowFailException(e)

    check = check(version=version)
    parsing =  create_dependency_graph(version=version)
    save_parsing_task = save_dependency_graph(dependency_graph=parsing)
    analysis = create_analysis(version=version, arcan_version=arcan_version)
    save_analysis_task = save_analysis(analysis = analysis)
    clean_output_directory_task = clean_output_directory(version=version)
    delete_version_directory_task = delete_version_directory(version)
    skip_task = skip()
    create_version_directory(version) >> check
    check >> parsing >> save_parsing_task >> analysis >> save_analysis_task >> clean_output_directory_task >> delete_version_directory_task
    check >> skip_task >> analysis >> save_analysis_task >> clean_output_directory_task >> delete_version_directory_task

@dag(
    schedule=None,
    start_date=datetime(2021, 1, 1, tz="UTC"),
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