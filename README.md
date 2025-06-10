# Arcan-Pipeline

An Airflow-based pipeline designed for the continuous analysis of GitHub repositories using the Arcan tool.

## Table of Contents

- [Goal](#goal)
- [Implementation](#implementation)
- [Installation](#installation)
- [Usage](#usage)
- [Limitations](#limitations)

## Goal

The primary goal of this pipeline is to regularly conduct software analysis using the Arcan tool on a diverse dataset of GitHub projects. This effort aims to expand the dataset that Arcan uses for project classification. The pipeline is responsible for the following tasks:

1. Detecting changes in the source code of GitHub projects to determine which projects should undergo analysis through the GitHub REST API.
2. Running Arcan to perform reverse engineering on the projects and storing the output in a database.
3. Executing Arcan to analyze the technical debt of the projects and storing the output in a database.

## Implementation

The general workflow can be divided into two separate and independent pipelines, each consisting of a set of well-defined steps.

The first pipeline, Ingestion, is responsible for retrieving new versions for each project from the database, acquiring them from GitHub, and selecting those that need to be analyzed. It then stores these selected versions back into the database. This process ensures that the list of versions available for subsequent analysis remains up-to-date.

The second pipeline, Execution, is responsible for executing the parsing process, when necessary, and analyzing the versions that were selected by the first pipeline.

Both pipelines are dynamically generated based on a subset of projects and versions selected from the database.

The foundation for this implementation is the Docker image of Apache Airflow. The Directed Acyclic Graphs (DAGs) that represent the Ingestion and Execution pipelines have been implemented in Python. The logic for the flow of the pipeline, scheduling settings, and error handling configurations are found in `inception.py` and `execution.py` in the `Dag` directory. These files define the tasks and their dependencies.

The logic for individual tasks is implemented in functions found in the `tasksFunction.py` file within the `Dag/utilities` directory. Modules have been created for interacting with services such as MySQL, the GitHub REST API, Docker Engine, and file system access. These modules are located in the `Dag/utilities` directory. Specifically, `mySqlGateway.py` manages database access operations, `gitHubRepository.py` handles communication with the GitHub REST API, `dockerRunner.py` takes care of Docker container execution, and `fileManager.py` handles file system access.

## Installation

### Prerequisites

Before proceeding with the installation, ensure you have the following prerequisites:

- Docker Community Edition (CE) installed on your workstation.
- Docker Compose version 1.29.1 or newer installed on your workstation.
- An initialized MySQL server.
- The Arcan tool image on your workstation.

### Platform Setup

1. Clone this GitHub repository to a directory on your computer.
2. Create a `.env` file based on the provided `.env.example` file, entering the necessary data.
3. Run `docker compose build` in your terminal.
4. Execute `docker compose up airflow-init` in your terminal.
5. Start the platform by running `docker compose up`.
Default: <http://localhost:5001/>

Note: Depending on your OS, you may need to configure Docker to use at least 4.00 GB of memory for the Airflow containers to run properly.

### Airflow Configuration

To configure Airflow:

1. Access the Airflow web interface.
2. Create a new connection with the ID 'mysql' in the [connection management](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html) by entering the relevant MySQL server details. You need to define a database for the pipeline. In the `init` folder, you will find the SQL instructions required to initialize the database. When connecting to the local MySQL database, make sure to provide all mandatory information, including the reference schema (i.e., the name of the database to use). Note that the host name should correspond to the application running inside a Docker container, not to a local instance.
3. Create variables 'git_token' and 'git_username' in the [variable management](https://airflow.apache.org/docs/apache-airflow/stable/howto/variable.html) and populate them with the appropriate data.
4. Create the 'docker_run_pool' in the [pool management](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html) by specifying the maximum number of Docker containers that can run in parallel.

### Restarting the Platform

To restart the platform:

1. Execute `docker compose down` in the terminal.
2. Restart the platform by running `docker compose up`.

## Usage

The Ingestion pipeline runs daily on a subset of repositories, while the Execution pipeline runs continuously on a subset of versions. For details on using the Airflow web interface, please refer to the [official documentation](https://airflow.apache.org/docs/apache-airflow/stable/ui.html).

## Limitations

Please be aware of the following limitations:

- The Execution pipeline is designed for execution on a single machine and relies on an external shared volume for the source code of the project and the results of Arcan execution. This design limits scalability. To enhance scalability, it's necessary to clone the project from the GitHub repository within both the parsing and analysis tasks.
- There's a limitation of 1024 concurrent tasks in Airflow, with a maximum of 5 Docker containers running simultaneously.
- In the Ingestion pipeline, the rate limit of the GitHub REST API can affect the pipeline's responsiveness. Consider using GitHub WebHooks for real-time notifications.
- In the Execution pipeline, the analysis and parsing tasks are limited to 4 hours, and some tasks may fail due to resource constraints.
