import pendulum
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.utils.email import send_email
import docker
from utilities import constants
from utilities.customException import DeleteDirException, DockerApiException, BenchmarkImageNotFoundException, BenchmarkExecutionException, DockerException
import subprocess
import os
import requests
import json

ARCAN_EMAIL = Variable.get('arcan_email')


@task()
def create_benchmark():
    datetime=pendulum.now()
    file_name = f'benchmark_{datetime}'
    n_records = 200000
    client = docker.from_env()
    try:
        container_name = 'benchmark_container'
        client.containers.run(image="arcan/arcan-benchmark:snapshot", command=f'/benchmarks/{file_name} {n_records}', user=50000, name=container_name, 
                              volumes={'arcan-pipeline_benchmark_volume': {'bind': '/benchmarks', 'mode': 'rw'}}, detach=False, mem_limit='4g')
        dataset = {
            "name": file_name,
            "path": f"/opt/airflow/benchmarks/{file_name}",
            "date": f"{datetime}",
        }
        return dataset
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

@task(trigger_rule = 'all_success', email_on_failure=True, email=ARCAN_EMAIL)
def compress_benchmark(dataset):
    try:
        if os.path.exists(dataset["path"]):
            cmd = f"gzip {dataset['path']}"
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            compressed_dataset = {
                "name": f"{dataset['name']}.gz",
                "path": f"{dataset['path']}.gz",
                "date": dataset["date"],
            }
            return compressed_dataset
        else:
            raise Exception("Benchmark not found") 
    except subprocess.CalledProcessError as e:
        raise Exception(e.stderr, compressed_dataset["name"])

@task(trigger_rule = 'all_success')
def upload_to_zenodo(dataset):
    access_token = Variable.get('zenodo_access_token')
    print("Creating a new deposition")
    headers = {"Content-Type": "application/json"}
    params = {'access_token': access_token}
    r = requests.post('https://zenodo.org/api/deposit/depositions',
                    params=params,
                    json={},
                    headers=headers)
    print(r.json())
    if(r.status_code == 201):
        print("Deposition created")
        bucket_url = r.json()["links"]["bucket"]
        deposition_id = r.json()["id"]
        print("Uploading file")
        with open(dataset['path'], "rb") as fp:
            r = requests.put(
                "%s/%s" % (bucket_url, dataset['name']),
                data=fp,
                params=params,
            )
        print(r.json())
        if(r.status_code == 201):
            print("File uploaded")
            print("Uploading metadata")
            data = {
                'metadata': {
                    'title': 'Technical Debt Dataset from Arcan Pipeline on %s' % dataset['date'],
                    'upload_type': 'dataset',
                    'description': 'The dataset of the study "A continuous open source data collection platform for architectural technical debt assessment.',
                    'creators': [
                        {'name': 'Darius Sas', 
                            'affiliation': 'Arcan SRL'},
                        {'name': 'Alessandro Gilardi', 
                            'affiliation': 'University of Milano-Bicocca'},
                        {'name': 'Ilaria Pigazzini', 
                            'affiliation': 'Arcan SRL'},
                        {'name': 'Francesca Arcelli Fontana', 
                            'affiliation': 'University of Milano-Bicocca'},
                        ]
                }
            }
            r = requests.put('https://zenodo.org/api/deposit/depositions/%s' % deposition_id,
                            params={'access_token': access_token}, data=json.dumps(data),
                            headers=headers)
            print(r.json())
            if(r.status_code == 200):
                print("Metadata uploaded")
#                print("Publishing")
#                r = requests.post('https://zenodo.org/api/deposit/depositions/%s/actions/publish' % deposition_id,
#                                    params={'access_token': access_token} )
#                print(r.json())
#                if(r.status_code == 202):
#                    print("Dataset published")
#                    dataset["zenodo_id"] = deposition_id
#                    return dataset
#                else:
#                    raise Exception("Dataset not published")
            else:
                raise Exception("Metadata not uploaded", r.json())
        else:
            raise Exception("File not uploaded", r.json())
    else:
        raise Exception("Deposition not created", r.json())    
    return dataset

@task(trigger_rule = 'all_done')
def delete_local_dataset(dataset):
    path = dataset["path"]
    try: 
        if os.path.exists(path):
            rmdir_cmd = f"rm -r {path}"
            subprocess.run(rmdir_cmd, shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise DeleteDirException(e.stderr, path) 

@task(trigger_rule = 'all_success')
def send_successful_email(dataset):
    msg = f"Dataset from Arcan Pipeline at {dataset['date']} uploaded to Zenodo"
    subject = f"Dataset from Arcan Pipeline at {dataset['date']} uploaded to Zenodo"
    send_email(to=ARCAN_EMAIL, subject=subject, html_content=msg)

@task(trigger_rule = 'all_failed')
def send_failed_email():
    msg = "Benchmark pipeline has recently failed. Please check the logs on Airflow and restart the pipeline"
    subject = "Benchmark pipeline failed"
    send_email(to=ARCAN_EMAIL, subject=subject, html_content=msg)


@dag( 
    schedule='0 0 1 */6 *', 
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
    dataset = create_benchmark()
    compress_dataset = compress_benchmark(dataset)
    upload_to_zenodo_task = upload_to_zenodo(compress_dataset)
    delete_dataset_task = delete_local_dataset(dataset)
    delete_compressed_dataset_task = delete_local_dataset(compress_dataset)
    send_successful_email_task = send_successful_email(dataset)
    send_failed_email_task = send_failed_email()
    upload_to_zenodo_task >> delete_compressed_dataset_task
    upload_to_zenodo_task >> delete_dataset_task
    upload_to_zenodo_task >> send_successful_email_task
    upload_to_zenodo_task >> send_failed_email_task
benchmark()
