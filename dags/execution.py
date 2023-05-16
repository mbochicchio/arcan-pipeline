from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task, task_group
from pendulum import datetime, duration
from typing import List
from utilities import tasksFunctions, constants
import logging

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

    @task(retries= constants.DOCKER_RETRIES, retry_delay= constants.DOCKER_RETRY_DELAY)
    def create_dependency_graph(version: dict):
        return tasksFunctions.create_dependency_graph(version)

    @task(retries=constants.MYSQL_RETRIES, retry_delay=constants.MYSQL_RETRY_DELAY, )
    def save_dependency_graph(dependency_graph: dict):
        return tasksFunctions.save_dependency_graph(dependency_graph=dependency_graph)
    
    save_dependency_graph(dependency_graph=create_dependency_graph(version=version)) 

@task_group()
def analyze_version(version:dict, arcan_version: dict):
    @task(trigger_rule='none_failed_min_one_success', retries= constants.DOCKER_RETRIES, retry_delay= constants.DOCKER_RETRY_DELAY)
    def create_analysis(version:dict, arcan_version:dict):    
        return tasksFunctions.create_analysis(version, arcan_version)

    @task(retries= constants.MYSQL_RETRIES, retry_delay= constants.MYSQL_RETRY_DELAY)
    def save_analysis(analysis:dict):
        tasksFunctions.save_analysis(analysis=analysis)

    save_analysis(analysis=create_analysis(version=version, arcan_version=arcan_version))    

def make_taskgroup(dag: DAG, version_list: List[dict], project: dict, arcan_version: dict) -> TaskGroup:
    group_id=str(project['id'])
    with TaskGroup(group_id=group_id, dag=dag) as paths:
        previous = None
        for version in version_list:
            version_id = version['id']
            with TaskGroup(group_id=f'{group_id}_{version_id}') as path:
                check(version=version) >> [parsing_version(version=version), skip()] >> analyze_version(version=version, arcan_version=arcan_version)
            if previous:
                previous >> path
            previous = path
    return paths

with DAG('execution', 
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
    arcan_version = tasksFunctions.get_arcan_version()
    project_list = tasksFunctions.get_project_list()
    for project in project_list:
        version_list = tasksFunctions.get_version_list(project=project, arcan_version=arcan_version)
        group = make_taskgroup(dag=execution, version_list=version_list, project=project, arcan_version=arcan_version)
        group



