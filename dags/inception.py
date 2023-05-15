import pendulum
from airflow.decorators import dag, task, task_group
from utilities import function

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def inception():

    @task()
    def get_project_list():
        project_list = function.get_project_list()
        return project_list
    
    @task_group()
    def select_new_version(project: dict):

        @task
        def get_last_version(project: dict):
            return function.get_last_version(project=project)
        
        @task
        def get_new_version_list(project: dict, last_version_analyzed: dict):
            return function.get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)

        @task()
        def save_new_project_versions(version_list: dict):
            function.save_new_project_versions(version_list=version_list)
        
        last_version_analyzed = get_last_version(project=project)
        version_list = get_new_version_list(project=project, last_version_analyzed=last_version_analyzed)
        save_new_project_versions(version_list=version_list)

    project_list=get_project_list()
    select_new_version.expand(project=project_list)
 
inception()
