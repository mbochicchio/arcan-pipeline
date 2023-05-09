from utilities.gateway import MySqlGateway
from utilities import gitHubRepository
from datetime import datetime
import math
from utilities import model
import subprocess
import logging
import docker
import os


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
    version_list = gitHubRepository.get_version_list(project, last_version_analyzed)

    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            gw.add_version(last_commit)
    else:
        number_of_version = len(version_list)
        if last_version_analyzed and (last_version_analyzed['id_github'] == version_list[number_of_version-1]['id_github']):
            version_list.pop()
        if (number_of_version != 0):
            max_number_of_version_to_consider = math.floor(6*math.log10(number_of_version+1))
            if max_number_of_version_to_consider < number_of_version:
                indices = [int(i * (number_of_version-1) / (max_number_of_version_to_consider-1)) for i in range(max_number_of_version_to_consider)]
                version_list = [version_list[i] for i in indices]
            for version in reversed(version_list):
                gw.add_version(version)

def get_version_list(project: dict, arcan_version:dict):
    gw = MySqlGateway()
    version_list = gw.get_versions_list(project=project, arcan_version=arcan_version) 
    return version_list

def create_dependency_graph(version:dict):
    gw = MySqlGateway()
    project = gw.get_project(id_project=version['id_project'])

    #clone del repository e checkout    
    project_dir = f"/opt/airflow/projects/{version['id']}"
    mkdir_cmd = f"mkdir -p {project_dir}"
    subprocess.run(mkdir_cmd, shell=True)

    cmd_clone = f"git clone https://github.com/{project['name']}.git {project_dir} && git --git-dir={project_dir}/.git checkout {version['id_github']}"
    result = subprocess.run(cmd_clone, shell=True, capture_output=True)
    print(result.stdout)
    print(result.stderr)
    
    #esecuzione creazione dependency_graph
    cmd = f'analyse -i /projects/{version["id"]} -o /projects -l {project["language"]} output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    client.containers.run("arcan/arcan-cli:latest", cmd, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}})

    #salvataggio dependency_graph
    #with open("nome_file", "rb") as file:
    #    file_result = file.read()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, None, version['id'])
    save_dependency_graph(dependency_graph=dependency_graph)

    #rimozione cartella
    rmdir_cmd = f"rm -r {project_dir}"
    subprocess.run(rmdir_cmd, shell=True)

    return dependency_graph

def create_analysis(version:dict, arcan_version:dict):
    gw = MySqlGateway()
    project = gw.get_project(id_project=version['id_project'])

    #clone del repository e checkout    
    project_dir = f"/opt/airflow/projects/{version['id']}"
    mkdir_cmd = f"mkdir -p {project_dir}"
    subprocess.run(mkdir_cmd, shell=True)

    cmd_clone = f"git clone https://github.com/{project['name']}.git {project_dir} && git --git-dir={project_dir}/.git checkout {version['id_github']}"
    result = subprocess.run(cmd_clone, shell=True, capture_output=True)
    print(result.stdout)
    print(result.stderr)
    
    #esecuzione analisi
    cmd = f'analyse -i /projects/{version["id"]} -o /projects -l {project["language"]} --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    client.containers.run("arcan/arcan-cli:latest", cmd, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}})

    #salvataggio analisi
    #with open("nome_file", "rb") as file:
    #    file_result = file.read()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    analysis = model.analysis(None, now, None, version['id'], arcan_version['id'])
    save_analysis(analysis=analysis)

    #rimozione cartella
    rmdir_cmd = f"rm -r {project_dir}"
    subprocess.run(rmdir_cmd, shell=True)

    return analysis

def save_dependency_graph(dependency_graph:dict):
    gw = MySqlGateway()
    gw.add_dependency_graph(dependency_graph)

def save_analysis(analysis:dict):
    gw = MySqlGateway()
    gw.add_analysis(analysis)



