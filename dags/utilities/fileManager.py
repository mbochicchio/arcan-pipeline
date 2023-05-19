import subprocess
import os
import json
from utilities.customException import ArcanOutputNotFoundException, MakeDirException, DeleteDirException, CloneRepositoryException, CheckoutRepositoryException

def get_project_path(project_id: str):
    return f"/opt/airflow/projects/{project_id}"

def get_output_path(output_type: str, project_id: str):
    return f"/opt/airflow/projects/{output_type}/arcanOutput/{project_id}"

def create_dir(path: str):
    try:
        if os.path.exists(path):
            delete_dir(path)
        mkdir_cmd = f"mkdir -p {path}"
        subprocess.run(mkdir_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MakeDirException(e)

def delete_dir(path: str):
    try: 
        if os.path.exists(path):
            rmdir_cmd = f"rm -r {path}"
            subprocess.run(rmdir_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise DeleteDirException(e)       
        
def get_output_file_path(output_type: str, project_id:dict):
    result_path = get_output_path(output_type=output_type, project_id=project_id)
    for file_name in os.listdir(result_path):
        if file_name.startswith("dependency-graph-"):
            result_path += f"/{file_name}"
            return result_path
    else:
        raise ArcanOutputNotFoundException(f"{output_type} file not found")

def clone_repository(project_name: str, project_path: str):
    try:
        cmd_clone = f"git clone https://github.com/{project_name}.git {project_path}"
        subprocess.run(cmd_clone, shell=True, check=True)
    except subprocess.CalledProcessError() as e:
        raise CloneRepositoryException(e)

def checkout_repository(version: str, project_dir: str):
    try: 
        cmd_clone = f"git --git-dir={project_dir}/.git checkout -q {version}"
        subprocess.run(cmd_clone, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise CheckoutRepositoryException(e)  

def get_blob_from_file(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            blob = file.read()
        return blob
    else: 
        raise ArcanOutputNotFoundException("Arcan Output file not found")
    
def create_cross_dag_arguments_file(argument: dict):
    with open('/opt/airflow/dags/utilities/crossDagArguments.json', 'w') as file:
        json.dump(argument , file)

def read_cross_dag_arguments_file():
    try:
        with open('/opt/airflow/dags/utilities/crossDagArguments.json', 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return None