from typing import List
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task, task_group
from utilitis import function

@task()
def get_parsing(version:dict):
    return function.get_dependency_graph(version)

@task.branch()
def check(version: dict):
    if version['dependency_graph'] is None:
        return str(version['id_project']) + "."+ str(version['id_project']) + "_" + str(version['id']) + ".parsing_version.create_dependency_graph"
    return str(version['id_project']) + "."+ str(version['id_project']) + "_" + str(version['id']) + ".get_parsing"   

@task_group()
def parsing_version(version: dict):
    @task()
    def create_dependency_graph(version: dict):
        return function.create_dependency_graph(version)

    @task()
    def save_dependency_graph(dependency_graph: dict):
        return function.save_dependency_graph(dependency_graph=dependency_graph)

    save_dependency_graph(dependency_graph=create_dependency_graph(version=version))
    
@task_group()
def analyze_version(version:dict, arcan_version: dict, dependency_graph:dict):
    @task(trigger_rule="none_failed_min_one_success")
    def create_analysis(version:dict, arcan_version=arcan_version):
        return function.create_analysis(version, arcan_version)

    @task()
    def save_analysis(analysis:dict):
        function.save_analysis(analysis=analysis)

    save_analysis(analysis=create_analysis(version=version))

def make_taskgroup(dag: DAG, version_list: List[dict], project: dict, arcan_version: dict) -> TaskGroup:
    group_id=str(project['id'])
    with TaskGroup(group_id=group_id, dag=dag) as paths:
        previous = None
        for version in version_list:
            version_id = version['id']
            with TaskGroup(group_id=f'{group_id}_{version_id}') as path:
                check(version=version) >> [parsing_version(version=version), get_parsing(version=version)] >> analyze_version(version=version, arcan_version=arcan_version, dependency_graph=None)
                
                #check(version=version) >> [parsing_version(version=version), get_parsing(version=version)] >> analyze_version(version=version, arcan_version=arcan_version, dependency_graph=None)
            if previous:
                previous >> path
            previous = path
    return paths

