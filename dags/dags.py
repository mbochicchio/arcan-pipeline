import pendulum
from airflow.decorators import dag, task
import function
from gateway import MySqlGateway

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def pipeline():

    @task()
    def get_project_list():
        gw = MySqlGateway()
        project_list = gw.get_projects_list()
        return project_list
    
    @task()
    def filter_project_versions(project: dict):
        function.filter_project_versions(project)

    @task()
    def filter_project_versions(project: dict):
        function.filter_project_versions(project)

    project_list = get_project_list()
    filter_project_versions.expand(project=project_list)
    
    

pipeline()
