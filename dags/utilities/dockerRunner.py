import docker
import os
from utilities.customException import DockerApiException, ArcanImageNotFoundException, ArcanExecutionException, DockerException

def execute_analysis(project: dict):
    cmd = f'analyse -i /projects/{project["id"]} -o /projects/analysis -l {project["language"]} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd)

def execute_parsing(project: dict):
    cmd = f'analyse -i /projects/{project["id"]} -o /projects/dependency-graph -l {project["language"]} --vcs NO_VCS output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd)

def execute_container(cmd: str):
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    try:
        client.containers.run("arcan/arcan-cli:latest", command=cmd, user=50000, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}})
    except docker.errors.APIError as e:
        raise DockerApiException("Docker API Exception:", e)
    except docker.errors.ContainerError as e:
        raise ArcanExecutionException("Arcan Exception:", e)
    except docker.errors.ImageNotFound as e:
        raise ArcanImageNotFoundException("Arcan Image not found:", e)
    except docker.errors.DockerException as e:
        raise DockerException("Generic exception in Docker:", e)