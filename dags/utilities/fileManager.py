import subprocess
import os

def create_project_dir(version: dict):
    project_dir = f"/opt/airflow/projects/{version['id']}"
    mkdir_cmd = f"mkdir -p {project_dir}"
    subprocess.run(mkdir_cmd, shell=True)

def delete_project_dir(path: str):
    rmdir_cmd = f"rm -r {path}"
    subprocess.run(rmdir_cmd, shell=True)

def delete_output_dir(path: str):
    directory_path = path[:path.rfind('/')]
    rmdir_cmd = f"rm -r {directory_path}"
    subprocess.run(rmdir_cmd, shell=True)    

def find_result_path(version:dict, result_type: str):
    result_path = f"/opt/airflow/projects/{result_type}/arcanOutput/{version['id']}"
    for file_name in os.listdir(result_path):
        if file_name.startswith(result_type):
            result_path += f"/{file_name}"
            break
    else:
        print("Nessun file trovato con il prefisso specificato.")

def clone_and_checkout_repository(version: dict, project_dir: str):
    cmd_clone = f"git clone https://github.com/{version['project']['name']}.git {project_dir} && git --git-dir={project_dir}/.git checkout {version['id_github']}"
    result = subprocess.run(cmd_clone, shell=True, capture_output=True)
    print(result.stdout)
    print(result.stderr)

def get_blob_from_file(path: str):
    with open(path, "rb") as file:
        blob = file.read()
    return blob