from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task, task_group
from pendulum import datetime, duration
from typing import List
from utilities import tasksFunctions, constants
from utilities.customException import ArcanOutputNotFoundException, CloneRepositoryException, CheckoutRepositoryException, ArcanImageNotFoundException, ArcanExecutionException
from airflow.exceptions import AirflowFailException


import logging

@task(retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def create_project_directory(project:dict):
    try:
        tasksFunctions.create_project_directory(project)
    except CloneRepositoryException as e:
        raise AirflowFailException()

@task(trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def delete_project_directory(project:dict):
    return tasksFunctions.delete_project_directory(project)

@task(trigger_rule='all_done', retries=constants.FILE_MANAGER_RETRIES, retry_delay=constants.FILE_MANAGER_RETRY_DELAY)
def clean_output_directory(project: dict):
    return tasksFunctions.delete_output_directory(project['id'])

@task()
def skip():
    logging.info("Dependency Graph already created")

@task.branch()
def check(version: dict):
    id_project = version['project']['id']
    if version['dependency_graph'] is None:
        return f'{id_project}.{id_project}_{version["id"]}.parsing_version.create_dependency_graph'
    return f'{id_project}.{id_project}_{version["id"]}.skip'

@task_group()
def parsing_version(version: dict):

    @task(retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_dependency_graph(version: dict):
        try:
            return tasksFunctions.create_dependency_graph(version)
        except (CheckoutRepositoryException, ArcanImageNotFoundException, ArcanExecutionException) as e:
            raise AirflowFailException(e)

    @task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
    def save_dependency_graph(dependency_graph: dict):
        try:
            return tasksFunctions.save_dependency_graph(dependency_graph=dependency_graph)
        except ArcanOutputNotFoundException as e:
            raise AirflowFailException(e)
        
    save_dependency_graph(dependency_graph=create_dependency_graph(version=version)) 

@task_group()
def analyze_version(version:dict, arcan_version: dict):
    @task(trigger_rule='none_failed_min_one_success', retries=constants.DOCKER_RETRIES, retry_delay=constants.DOCKER_RETRY_DELAY)
    def create_analysis(version:dict, arcan_version:dict):  
        try:  
            return tasksFunctions.create_analysis(version, arcan_version)
        except (CheckoutRepositoryException, ArcanImageNotFoundException, ArcanExecutionException) as e:
            raise AirflowFailException(e)

    @task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY)
    def save_analysis(analysis:dict):
        try:
            tasksFunctions.save_analysis(analysis=analysis)
        except ArcanOutputNotFoundException as e:
            raise AirflowFailException(e)

    save_analysis(analysis=create_analysis(version=version, arcan_version=arcan_version))    

def make_taskgroup(dag: DAG, version_list: List[dict], project: dict, arcan_version: dict, priority_weight: int) -> TaskGroup:
    group_id=str(project['id'])
    with TaskGroup(group_id=group_id, dag=dag, default_args={'priority_weight': priority_weight}) as paths:
        previous = None
        for version in version_list:
            version_id = version['id']
            with TaskGroup(group_id=f'{group_id}_{version_id}') as path:
                check(version=version) >> [parsing_version(version=version), skip()] >> analyze_version(version=version, arcan_version=arcan_version) >> clean_output_directory(project=version['project']) 
            if previous:
                previous >> path
            previous = path
    return paths

with DAG(
    dag_id = constants.EXECUTION_DAG_ID, 
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
) as execution:
    arguments = tasksFunctions.get_cross_dag_arguments()
    if arguments:
        arcan_version = arguments[constants.ARCAN_VERSION]
        project_list = arguments[constants.PROJECT_LIST]
        for index in range(len(project_list)):
            project = project_list[index][constants.PROJECT]
            version_list = project_list[index][constants.VERSION_LIST]
            if version_list:
                task_group = make_taskgroup(dag=execution, version_list=version_list, project=project, arcan_version=arcan_version, priority_weight=index)
                create_project_directory(project) >> task_group >> delete_project_directory(project)



