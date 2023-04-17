import pendulum
from airflow.decorators import dag, task, task_group
import function
import logging


@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def pipeline():


    @task()
    def get_project_list():
        project_list = function.get_project_list()
        return project_list
    
    @task()
    def add_project_versions(project: dict):
        function.add_project_versions(project)
        return project

    @task()
    def get_arcan_version():
        arcan_version = function.get_arcan_version()
        return arcan_version
    
    @task_group()
    def parsing_version(version: dict):
        @task()
        def create_dependency_graph(version: dict):
            function.create_dependency_graph(version)

        @task()
        def save_dependency_graph(dependency_graph:dict, version=version):
            #function.save_dependency_graph(version)
            print()

        save_dependency_graph(dependency_graph=create_dependency_graph(version=version))
    
    @task_group()
    def analyze_version(version:dict, arcan_version: dict):
        @task()
        def create_analysis(version:dict, arcan_version=arcan_version):
            function.analyze_version(version, arcan_version)

        @task()
        def save_analysis(analysis:dict, arcan_version=arcan_version):
            #function.save_analysis(version, arcan_version)    
            print()

        save_analysis(analysis=create_analysis(version=version))
            

    @task_group()
    def execute_iteration(version: dict):
        """
        @task()
        def skip():
            print()

        @task.branch()
        def check(version: dict):
            if version['dependency_graph'] is None:
                return "create_dependency_graph"
            return "skip"   
        """
        
        @task()
        def test(version:dict):
            print(version)
        
        test(version=version)
        #check(version=version) >> [parsing_version(version=version), skip()] >> analyze_version(version=version, arcan_version=arcan_version)

    

    @task()
    def get_version_list(project: dict, arcan_version:dict):
        version_list = function.get_version_list(project=project, arcan_version=arcan_version)
        return version_list

    @task_group()
    def execute(project: dict, arcan_version:dict):
        version_list = get_version_list(project=project, arcan_version=arcan_version)
        
        #non si possono usare gli expand in taskgroup
        execute_iteration.partial(arcan_version=arcan_version).expand(version=version_list)



    arcan_version = get_arcan_version() 
    project_list=add_project_versions.expand(project=get_project_list())
    
    #impossibile iterare perchè version_list_expanded è un XComArg e non è iterabile
    #version_list_expanded = get_version_list.partial(arcan_version=arcan_version).expand(project=project_list)        
    #for version_list in version_list_expanded:
    #    execute_iteration.partial(arcan_version=arcan_version).expand(version=version_list)
    
    #non si possono usare gli expand in taskgroup
    execute.partial(arcan_version=arcan_version).expand(project=project_list)

 
pipeline()