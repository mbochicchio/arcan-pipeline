import pendulum
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.decorators import task
from utilities import tasksFunctions


@task
def get_last_version(project: dict):
    return tasksFunctions.get_last_version(project=project)
            
@task
def get_new_version_list(project: dict, last_version_analyzed: dict):
    return tasksFunctions.get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)

@task()
def save_new_project_versions(version_list: dict):
    tasksFunctions.save_new_project_versions(version_list=version_list)
        

def make_taskgroup(dag: DAG, project: dict) -> TaskGroup:
    group_id=str(project['id'])
    with TaskGroup(group_id=group_id, dag=dag) as paths:
        last_version_analyzed = get_last_version(project=project)
        version_list = get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
        save_new_project_versions(version_list=version_list)
    return paths

with DAG('inception', 
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
) as inception:
    
    project_list = tasksFunctions.get_project_list()

    for project in project_list:
        group = make_taskgroup(dag=inception, project=project)
        group