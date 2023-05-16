import docker
import os

def execute_analysis(version: dict):
    cmd = f'analyse -i /projects/{version["id"]} -o /projects/analysis -l {version["project"]["language"]} --vcs NO_VCS --all output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    client.containers.run("arcan/arcan-cli:latest", cmd, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}})

def execute_parsing(version: dict):
    cmd = f'analyse -i /projects/{version["id"]} -o /projects/dependency-graph -l {version["project"]["language"]} --vcs NO_VCS output.writeDependencyGraph=true output.writeSmellCharacteristics=false output.writeComponentMetrics=false output.writeAffected=false output.writeProjectMetrics=false'
    os.environ['DOCKER_HOST'] = 'tcp://host.docker.internal:2375'
    client = docker.from_env()
    client.containers.run("arcan/arcan-cli:latest", cmd, remove=True, volumes={'arcan-pipeline_shared-volume': {'bind': '/projects', 'mode': 'rw'}})
