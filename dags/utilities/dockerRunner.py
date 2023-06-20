import docker
import os
from utilities.customException import DockerApiException, ArcanImageNotFoundException, ArcanExecutionException, DockerException

def execute_analysis(version_id: int, project_language:str, arcan_image: str):
    cmd = f'analyse -i /projects/{version_id} -o /projects/analysis -l {project_language} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image)

def execute_parsing(version_id: int, project_language:str, arcan_image: str):
    cmd = f'analyse -i /projects/{version_id} -o /projects/dependency-graph -l {project_language} --vcs NO_VCS output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image)

def execute_container(cmd: str, arcan_image: str):
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    try:
        output = client.containers.run(image=arcan_image, command=cmd, user=50000, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}}, detach=False, stdout=True, stderr=True)
    except docker.errors.APIError as e:
        raise DockerApiException("Docker API Exception:", e)
    except docker.errors.ContainerError as e:
        raise ArcanExecutionException("Arcan Exception:", e.stderr.decode('utf-8'))
    except docker.errors.ImageNotFound as e:
        raise ArcanImageNotFoundException("Arcan Image not found:", e)
    except docker.errors.DockerException as e:
        raise DockerException("Generic exception in Docker:", e)
    finally:
        print("container: ", output)