from utilities.mySqlGateway import MySqlGateway
from datetime import datetime
import math
from utilities import model, fileManager, dockerRunner, gitHubRepository
import subprocess
import logging
import docker
import os


def get_project_list():
    gw = MySqlGateway()
    project_list = gw.get_projects_list()
    return project_list

#funzioni per inception

def get_last_version(project: dict):
    gw = MySqlGateway()
    return gw.get_last_version(project['id'])

def get_new_version_list(project:dict, last_version_analyzed:dict):
    version_list = gitHubRepository.get_version_list(project, last_version_analyzed)
    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            return [last_commit]
    else:
        number_of_version = len(version_list)
        if last_version_analyzed and (last_version_analyzed['id_github'] == version_list[number_of_version-1]['id_github']):
            version_list.pop()
        if (number_of_version != 0):
            max_number_of_version_to_consider = math.floor(6*math.log10(number_of_version+1))
            if max_number_of_version_to_consider < number_of_version:
                indices = [int(i * (number_of_version-1) / (max_number_of_version_to_consider-1)) for i in range(max_number_of_version_to_consider)]
                version_list = [version_list[i] for i in indices]
            return version_list

def save_new_project_versions(version_list: list):
    gw = MySqlGateway()
    for version in reversed(version_list):
        gw.add_version(version)

#funzioni per execution

def get_arcan_version():
    gw = MySqlGateway()
    arcan_version = gw.get_arcan_version()
    return arcan_version

def get_version_list(project: dict, arcan_version:dict):
    gw = MySqlGateway()
    version_list = gw.get_versions_list(project=project, arcan_version=arcan_version) 
    return version_list

def create_dependency_graph(version:dict):
    #clone del repository e checkout    
    project_dir = fileManager.create_project_dir(version=version)

    fileManager.clone_and_checkout_repository(version=version, project_dir=project_dir)
    
    #esecuzione creazione dependency_graph
    dockerRunner.execute_parsing(version=version)

    #salvataggio dependency_graph
    result_path = fileManager.find_result_path(version=version, result_type="dependency-graph")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, result_path, version['id'])

    fileManager.delete_project_dir(project_dir)

    return dependency_graph

def create_analysis(version:dict, arcan_version:dict):
    project_dir = fileManager.create_project_dir(version=version)

    fileManager.clone_and_checkout_repository(version=version, project_dir=project_dir)

    dockerRunner.execute_analysis(version=version)

    result_path = fileManager.find_result_path(version=version, result_type="analysis")
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    analysis = model.analysis(None, now, result_path, version['id'], arcan_version['id'])

    fileManager.delete_project_dir(project_dir)

    return analysis

def save_dependency_graph(dependency_graph:dict):
    file_result_path = dependency_graph['file_result']
    with open(file_result_path, "rb") as file:
        dependency_graph['file_result'] = file.read()
    gw = MySqlGateway()
    gw.add_dependency_graph(dependency_graph)
    fileManager.delete_output_dir(path=file_result_path)

def save_analysis(analysis:dict):
    #recupero file
    file_result_path = analysis['file_result']
    with open(file_result_path, "rb") as file:
        analysis['file_result'] = file.read()
    #salvataggio nel database
    gw = MySqlGateway()
    gw.add_analysis(analysis)
    #rimozione cartella
    fileManager.delete_output_dir(path=file_result_path)
  
