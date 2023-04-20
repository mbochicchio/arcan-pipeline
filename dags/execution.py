from utilitis.factory_task_group import make_taskgroup
from utilitis.function import get_arcan_version, get_project_list, get_version_list
from airflow import DAG
import pendulum

with DAG('execution', 
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
) as execution:
    
    arcan_version = get_arcan_version()
    project_list = get_project_list()

    for project in project_list:
        version_list = get_version_list(project=project, arcan_version=arcan_version)
        group = make_taskgroup(dag=execution, version_list=version_list, project=project, arcan_version=arcan_version)
        group