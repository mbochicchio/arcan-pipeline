import subprocess
import os
from utilities.customException import ArcanOutputNotFoundException, MakeDirException, DeleteDirException, CloneRepositoryException, CheckoutRepositoryException

def get_version_path(version_id: str):
    return f"/opt/airflow/projects/{version_id}"

def get_output_path(output_type: str, version_id: str):
    return f"/opt/airflow/projects/{output_type}/arcanOutput/{version_id}"

def create_dir(path: str):
    try:
        if os.path.exists(path):
            delete_dir(path)
        mkdir_cmd = f"mkdir -p {path}"
        subprocess.run(mkdir_cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise MakeDirException(e.stderr, path)


def delete_dir(path: str):
    try: 
        if os.path.exists(path):
            rmdir_cmd = f"rm -r {path}"
            subprocess.run(rmdir_cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise DeleteDirException(e.stderr, path)       

def get_output_file_path(output_type: str, version_id:dict):
    result_path = get_output_path(output_type=output_type, version_id=version_id)
    for file_name in os.listdir(result_path):
        if file_name.startswith("dependency-graph-"):
            result_path += f"/{file_name}"
            return result_path
    raise ArcanOutputNotFoundException(f"Arcan Output file not found: {result_path}")

def get_output_file_name(output_type: str, version_id:dict):
    result_path = get_output_path(output_type=output_type, version_id=version_id)
    for file_name in os.listdir(result_path):
        if file_name.startswith("dependency-graph-"):
            return file_name
    raise ArcanOutputNotFoundException(f"Arcan Output file not found: {result_path}")

def clone_repository(project_name: str, project_path: str):
    try:
        cmd_clone = f"git clone https://github.com/{project_name}.git {project_path}"
        subprocess.run(cmd_clone, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise CloneRepositoryException(e.stderr)


def checkout_repository(version: str, project_dir: str):
    try: 
        cmd_clone = f"git -C {project_dir} checkout -q -f {version}"
        subprocess.run(cmd_clone, shell=True, check=True,capture_output=True)
    except subprocess.CalledProcessError as e:
        raise CheckoutRepositoryException(e.stderr)
    

def get_blob_from_file(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            blob = file.read()
        return blob
    else: 
        raise ArcanOutputNotFoundException(f"Arcan Output file not found: {file_path}")

def write_file(data, path):
    file_path = f"{path}/dependency-graph-loaded.graphml"
    with open(file_path, 'wb') as file:
        file.write(data)