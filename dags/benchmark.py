import pendulum
from airflow.decorators import dag, task
import docker
from utilities import constants
from utilities.customException import DockerApiException, BenchmarkImageNotFoundException, BenchmarkExecutionException, DockerException
import subprocess
import os

@task()
def create_benchmark():
    file_name = f'benchmark_{pendulum.now()}'
    n_records = 200000
    client = docker.from_env()
    try:
        container_name = 'benchmark_container'
        client.containers.run(image="arcan/arcan-benchmark:snapshot", command=f'/benchmarks/{file_name} {n_records}', user=50000, name=container_name, 
                              volumes={'arcan-pipeline_benchmark_volume': {'bind': '/benchmarks', 'mode': 'rw'}}, detach=False, mem_limit='4g')
        return f'/opt/airflow/benchmarks/{file_name}'
    except docker.errors.APIError as e:
        raise DockerApiException("Docker API Exception:", e)
    except docker.errors.ContainerError as e:     
        raise BenchmarkExecutionException("Benchmark Internal Error:", e)
    except docker.errors.ImageNotFound as e:
        raise BenchmarkImageNotFoundException("Benchmark Image not found:", e)
    except docker.errors.DockerException as e:
        raise DockerException("Generic exception in Docker:", e)
    finally:
        container = client.containers.get(container_name)
        print("Benchmark container log:")
        logs = container.logs(stream=True)
        for line in logs:
            print(line)
        container.remove()

@task(trigger_rule = 'all_success')
def compress_benchmark(file_name):
    try:
        if os.path.exists(file_name):
            cmd = f"gzip {file_name}"
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        else:
            raise Exception("Benchmark not found") 
    except subprocess.CalledProcessError as e:
        raise Exception(e.stderr, file_name)

@dag( 
    schedule='0 0 2 * *', 
    start_date=pendulum.datetime(2023, 1, 1),
    catchup=False,
    tags=[],
    default_args={
        'owner': constants.DEFAULT_OWNER,
        "retries": constants.DEFAULT_RETRIES,
        "retry_delay": constants.DEFAULT_RETRY_DELAY,
        "retry_exponential_backoff": constants.DEFAULT_RETRY_EXPONENTIAL_BACKOFF,
        "max_retry_delay": constants.DEFAULT_MAX_RETRY_DELAY,
    },
)
def benchmark():
    file_name = create_benchmark()
    compress_benchmark(file_name)

benchmark()