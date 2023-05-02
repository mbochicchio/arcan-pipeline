from utilities.gateway import MySqlGateway
from utilities import gitHubRepository
from datetime import datetime
import math
from utilities import model
import subprocess
import logging

def get_project_list():
    gw = MySqlGateway()
    project_list = gw.get_projects_list()
    return project_list

def get_arcan_version():
    gw = MySqlGateway()
    arcan_version = gw.get_arcan_version()
    return arcan_version

def add_project_versions(project: dict):
    gw = MySqlGateway()
    last_version_analyzed = gw.get_last_version(project['id'])
    version_list = gitHubRepository.get_version_list(project)

    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            gw.add_version(last_commit)
    else:
        if last_version_analyzed:
            index = 0
            if (last_version_analyzed['id_github'] != str(version_list[0]['id_github'])):
                find = False
                len_version_list = len(version_list)
                while index < len_version_list and not find:
                    if str(version_list[index]['id_github']) == last_version_analyzed['id_github']:
                        find = True
                    else:
                        index += 1
            version_list = version_list[:index]
        
        number_of_version = len(version_list)
        if (number_of_version != 0):
            max_number_of_version_to_consider = math.floor(6*math.log10(number_of_version+1))
            step = math.ceil(number_of_version / max_number_of_version_to_consider)
            version_list = version_list[::step]
            version_list.reverse()
            for item in version_list:
                gw.add_version(item)

def get_version_list(project: dict, arcan_version:dict):
    gw = MySqlGateway()
    version_list = gw.get_versions_list(project=project, arcan_version=arcan_version) 
    return version_list

def create_dependency_graph(version:dict):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, None, version['id'])

    return dependency_graph

def create_analysis(version:dict, arcan_version:dict):
    gw = MySqlGateway()
    """project = gw.get_project(id_project=version['project_id'])
    url = f"https://github.com/{project['name']}/tree/{version['id_github']}"""
    

    project_dir = str(version['id'])
    url = "https://github.com/vinta/awesome-python.git"
    cmd = f'docker run --rm -it -v .:/data arcan/arcan-cli:latest analyse -i /data/{project_dir} --remote {url} -o /data -l JAVA output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    
    print(f'Error: {error}')
    print(f'Output: {output}')
    print(f'Return code: {process.returncode}')

    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    analyzis = model.analysis(None, now, None, version['id'], arcan_version['id'])
    return analyzis

def save_dependency_graph(dependency_graph:dict):
    gw = MySqlGateway()
    gw.add_dependency_graph(dependency_graph)

def save_analysis(analysis:dict):
    gw = MySqlGateway()
    gw.add_analysis(analysis)

def get_dependency_graph(version:dict):
    gw= MySqlGateway()
    dependency_graph = gw.get_dependency_graph(version=version)
    return dependency_graph


