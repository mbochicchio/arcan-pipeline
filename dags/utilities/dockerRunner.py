import docker
from utilities.customException import DockerApiException, ArcanImageNotFoundException, ArcanExecutionException, DockerException

def execute_analysis(version: int, project_language:str, arcan_image: str, dependency_graph_name: str):
    cmd = f'4h /arcan-cli/arcan.sh analyse-graph --graphFile /projects/dependency-graph/arcanOutput/{version["id"]}/{dependency_graph_name} --versionId {version["id_github"]} -i /projects/{version["id"]} -o /projects/analysis -l {project_language} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version["id"])

def execute_parsing(version_id: int, project_language:str, arcan_image: str):
    cmd = f'4h /arcan-cli/arcan.sh analyse -i /projects/{version_id} -o /projects/dependency-graph -l {project_language} --vcs NO_VCS metrics.componentMetrics="none" metrics.smellCharacteristics="none" metrics.projectMetrics="none" metrics.indexCalculators="none" output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version_id)

def execute_container(cmd: str, arcan_image: str, version_id: int):
    client = docker.from_env()
    try:
        container_name = f'arcan_container_{version_id}'
        client.containers.run(image=arcan_image, command=cmd, user=50000, name=container_name, entrypoint="timeout", volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}}, detach=False, mem_limit='3g', environment=["JAVA_MEMORY=4G"])

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