import docker
import os
from utilities.customException import DockerApiException, ArcanImageNotFoundException, ArcanExecutionException, DockerException

def execute_analysis(version_id: int, project_language:str, arcan_image: str):
    cmd = f'analyse -i /projects/{version_id} -o /projects/analysis -l {project_language} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version_id)

def execute_parsing(version_id: int, project_language:str, arcan_image: str):
    cmd = f'analyse -i /projects/{version_id} -o /projects/dependency-graph -l {project_language} --vcs NO_VCS output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version_id)

def execute_container(cmd: str, arcan_image: str, version_id: int):
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    try:
        container_name = f'arcan_container_{version_id}'
        client.containers.run(image=arcan_image, command=cmd, user=50000, name=container_name, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}}, detach=False)

    except docker.errors.APIError as e:
        raise DockerApiException("Docker API Exception:", e)
    except docker.errors.ContainerError as e:
        raise ArcanExecutionException("Arcan Exception:", e)
    except docker.errors.ImageNotFound as e:
        raise ArcanImageNotFoundException("Arcan Image not found:", e)
    except docker.errors.DockerException as e:
        raise DockerException("Generic exception in Docker:", e)
    finally:
        container = client.containers.get(container_name)
        print("Arcan container log:")
        logs = container.logs(stream=True)
        for line in logs:
            print(line)
        container.remove()