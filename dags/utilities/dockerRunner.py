import docker # type: ignore
import datetime
import time
from utilities.customException import DockerApiException, ArcanImageNotFoundException, ArcanExecutionException, DockerException, MaximumExecutionTimeExeededException

def execute_analysis(version: int, project_language:str, arcan_image: str, dependency_graph: str):
    cmd = f'analyse-graph --graphFile {dependency_graph} --versionId {version["id_github"]} -i /projects/{version["id"]} -o /projects/analysis -l {project_language} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version["id"])

def execute_parsing(version_id: int, project_language:str, arcan_image: str):
    cmd = f'analyse -i /projects/{version_id} -o /projects/dependency-graph -l {project_language} --vcs NO_VCS metrics.componentMetrics="none" metrics.smellCharacteristics="none" metrics.projectMetrics="none" metrics.indexCalculators="none" output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    execute_container(cmd, arcan_image, version_id)

def execute_container(cmd: str, arcan_image: str, version_id: int):
    start_time=datetime.datetime.now()
    client = docker.from_env()
    try:
        container_name = f'arcan_container_{version_id}'
        container = client.containers.run(
            image=arcan_image,
            command=cmd,
            user=50000,
            name=container_name,
            volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}},
            detach=True,
            mem_limit='4g',
            environment=["JAVA_MEMORY=4G"]
        )

        # Monitor container execution
        while container.status != 'exited':
            time.sleep(1)
            container.reload()
            if time.time() - start_time.timestamp() > 14400:  # 4 hours timeout
                container.kill()
                raise MaximumExecutionTimeExeededException("Arcan Analysis Maximum Execution Time Exceeded")
            
    except docker.errors.APIError as e:
        raise DockerApiException("Docker API Exception:", e)
    except docker.errors.ContainerError as e:
        finish_time=datetime.datetime.now()
        execution_time = (finish_time - start_time ).seconds
        if execution_time >= 14400:
            raise MaximumExecutionTimeExeededException("Maximum Execution Time Exeeded:", e)
        else:
            raise ArcanExecutionException("Arcan Internal Error:", e)
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