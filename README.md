<a id="readme-top"></a>

<h3 align="center">dop_generation</h3>

  <p align="center">
    Python scripts for generating Dilution of Precision (DOP) data and storing it in an InfluxDB database. It includes tools for processing SEM almanac files, computing DOP metrics, and writing results to InfluxDB
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#dependencies">Dependencies</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#creating-the-database">Creating the Database</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

The scripts in this repository were provided by The Aerospace Corporation and are used for processing satellite navigation data. They generate Dilution of Precision (DOP) values from SEM almanac files and store the results in an InfluxDB database. This repository serves to document the setup, dependencies, and usage of these scripts.

| O/S | Status |
|-----|--------|
| Windows | ✅ |
| Linux | ✅ |
| macOS | ✅ |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites
1. Python
   * Run this command on the terminal to check Python is already installed on your device
    ```sh
    python --version
    ```
    * If you recieve a message with Python 3.12.4 you should be set. If not install it running this commands:
    ```sh
    sudo apt update
    sudo apt install python3
    ```
2. InfluxDb 1.8 version
   * To install Influxdb 1.8 visit [https://www.influxdata.com/downloads](https://www.influxdata.com/downloads/) <br> Once you are in this page scroll all the way down to [Are you interested in InfluxDB 1.x Open Source?] and select your operating         system.
   #### Linux set up
   * Run this command 
    ```sh
    wget https://download.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb
    sudo dpkg -i influxdb_1.8.10_amd64.deb
    ```
   #### Mac set up
   * Run this command 
    ```sh
    brew update
    brew install influxdb@1.11.8
    ```
   #### Windows set up

   

   * Run this command to confirm the installation
   ```sh
    influx --version
   ```

3. Clone the repository from GitHub

    * Choose where you want to clone the repository locally:

      ```
      cd /path/to/your_directory
      ```
    * Clone the repository:

      ```
      git clone https://github.com/Josephc0/DOP-Generation
      ```
    <p align="right">(<a href="#readme-top">back to top</a>)</p>

### Dependencies
```dop_generations``` requires the following **dependencies**:

| Package | Version | Description |
|---------|---------|-------------|
| **numpy** | 1.25.2 | A library for working with large arrays and math operations.|
| **matplotlib** | 3.7.2 | A library for creating graphs and visualizations in Python. |
| **plotly** | 5.16.1 | A library for making interactive charts and plots. |
| **influxdb** | 5.3.2 | A Python client for working with InfluxDB, a database for time series data. |
<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Installation
1. Navigate to where you cloned the repository locally

    ```
    cd /path/to/your_directory/dop_generation
    ```

2. Install dependencies
    ```
    python -m pip install -r requirements.txt
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Creating the Database 

This command is used to start influxdb
```
sudo systemctl start influxdb
```

This checks if the system is running

```
sudo systemctl status influxdb
```

To make the database run this commands

```
influx
```
creating a basic database is created by running this command.
```
CREATE DATABASE "name of data base"
```
Now lets see the data base, this command will return the databasses that are stored

```
SHOW DATABASES
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### The DOP Script

Configure the following environment variables to run the `generate_dop_data.py` script.

| env var name | default | description |
| --- | --- | --- |
| `TIME_KEY` | None | Required. The timestamp used to compute the DOP in RFC3339 format. YYYY-mm-DDT-HH-MM-SSZ (e.g. 2024-08-21T15:40:30Z) |
| `SEM_ALM_FILE` | `current_sem_week.txt` | The file path to the SEM almanac file. |
| `DOP_OUTPUT_FILE` | `dop_output.txt` | The output file for the DOP metrics. |

### InfluxDB V1

Configure the following environment variables to run the `write_to_influxdb.py` script.

| env var name | default | description |
| --- | --- | --- |
| `TIME_KEY` | None | Required. The timestamp used to compute the DOP in RFC3339 format. YYYY-mm-DDT-HH-MM-SSZ (e.g. 2024-08-21T15:40:30Z) |
| `DOP_OUTPUT_FILE` | `dop_output.txt` | The data file from the DOP data generation script. |
| `INFLUXDB_WRITE_HOST_V1` | `None` | The InfluxDB host for the V1 write client. |
| `INFLUXDB_WRITE_DB` | `None` | The InfluxDB database to write for the V1 client. |
| `INFLUXDB_WRITE_USER` | `None` | The user credential for the V1 write client. |
| `INFLUXDB_WRITE_PASS` | `None` | The password credential for the V1 write client. |
| `INFLUXDB_WRITE_MEAS_V1` | `dop` | The InfluxDB measurement used to store the data. |

## Step 1 - Run the DOP Script

The `generate_dop_data.py` script contains a DOP data generation algorithm that outputs a data file which can then be read and input into InfluxDB V1.

> It takes a few minutes for the script to complete.

```sh
export TIME_KEY=2024-08-21T15:40:30Z
python generate_dop_data.py
```

By default, it outputs a data file called `dop_output.txt` that contains the new DOP data.

## Step 2 - Write the DOP Metrics to InfluxDB

The `write_to_influxdb.py` script reads the data from the  to store the DOP metrics onto InfluxDB version 1.8. 

```sh
export TIME_KEY=2024-08-21T15:40:30Z
export host INFLUXDB_WRITE_HOST_V1=localhost
export database INFLUXDB_WRITE_DB=mydopdb
export username INFLUXDB_WRITE_USER=myuser
export password INFLUXDB_WRITE_PASS=mypass
python write_to_influxdb.py
```

The website will query InfluxDB for this DOP data for this particular time step.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

This project was developed by Cal State LA Computer Science students as part of our Senior Design Project, in collaboration with The Aerospace Corporation.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
