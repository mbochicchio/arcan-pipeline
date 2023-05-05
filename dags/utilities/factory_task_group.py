from typing import List
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task, task_group
from utilities import function
import logging


@task()
def skip():
    logging.info("Dependency Graph already created")

@task.branch()
def check(version: dict):
    if version['dependency_graph'] is None:
        return str(version['id_project']) + "."+ str(version['id_project']) + "_" + str(version['id']) + ".parsing_version"
    return str(version['id_project']) + "."+ str(version['id_project']) + "_" + str(version['id']) + ".skip"   

@task()
def parsing_version(version: dict):
    return function.create_dependency_graph(version)
    
@task(trigger_rule='none_failed_min_one_success')
def analyze_version(version:dict, arcan_version: dict):
    return function.create_analysis(version, arcan_version)

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

