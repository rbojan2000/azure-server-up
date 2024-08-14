<a name="readme-top"></a>
<br/>
<div align="center">
  <h3 align="center">Azure Server Up</h3>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-application">About The Application</a>
    </li>
    <li>
      <a href="#architecture">Architecture</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#application-setup">Application setup</a></li>
        <li><a href="#local-run">Running deployment</a></li>
      </ul>
    </li>
  </ol>
</details>


# About The Application
This application automates infrastructure provisioning on Azure Cloud, including the configuration of virtual machines, server application startup, and running the application inside a Docker container.
It consists of the following scripts in the infrastructure package:

* **infrastructure_setup** is responsible for provisioning the necessary infrastructure. 
* **start_task** handles the configuration of the virtual machine and the startup of the server.

The configuration is defined in `config/settings.toml` file and invoked with `Dynaconf` library.


# Architecture
## Architecture
- <i> Diagram 1.1 </i> illustrates the overall structure of the infrastructure provisioned by the **infrastructure_setup** script.

<br>

<div align="center">
  <img src="/docs/architecture.png" alt="Diagram 1.1" style="width: 50%; height: auto;" />
  <p > <i>Diagram 1.1</i></p>
</div>

# Getting Started

## Prerequisites

Requirements for running applications:

* Poetry
* Python 3.10
* Python virtueal environment (pyenv, virtualenv)

## Application Setup
This section provides detailed instructions for setting up the environment to run the scripts.

1. Activate virtual environment
    ```sh
    $ source venv/bin/activate
    ```
2. Install all python libraries
   ```sh
   $ poetry install
   ```

## Running deployment
To run the scripts, ensure you have `azure-cli` installed. The application uses `DefaultAzureCredential`, which searches for credentials in the following order, with local credentials as the last option.

Specify the Docker Container Registry and make sure the server Docker Image is properly registered.

> **_NOTE:_**: The settings.toml file contains all necessary configuration parameters for the infrastructure, including credentials and Docker image details. Ensure it is correctly set up before running the scripts.


Deploy infrastructure:
```sh
$ python -m src.infrastructure_setup
```

Start VM and Run Server in Docker Container:
```sh
$ python -m src.start_task
```

<br/>

🚀 **Your server application should be accessible at <i> http://<nic_public_ip_address>:80/</i>. 
Replace <i><nic_public_ip_address></i> with the actual IP address of your virtual machine.**

<p align="right">(<a href="#readme-top">back to top</a>)</p>
