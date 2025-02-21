# SatelliteVisualizer
 

# Description
This is a senior project from CSULA students, we are undergraduate computer scientist students that have been given this task by the Aerospace Corporation. The aim of this project is to take satellite data and provide a solution where the Aerospace Corporation can easily view areas that aren't cover by satallites. This technology can be used in increase gps location tracking. 

# Getting Started

## Operating System Compability 
| O/S | Status |
|-----|--------|
| Windows | ✅ |
| Linux | ✅ |
| macOS | ✅ |


## **Prerequisites**

1. Python
2. InfluxDb 1.8 version
3. Docker

## Installation

#### Linux set up
###### Python Install
In linux python is usually shipped with the distros, so we should first check if its installed.
- run this command on the terminal
```
python --version
```
If you recieve a message with Python 3.12.4 you should be set with python. If not install it running this commands:

```
sudo apt update
sudo apt install python3
```

From here we should compartilize this project to a specific virtual environment for python. The reason we should do this is to seperate different versions of modules. Not all projects run the latest updated modules, we avoid later conflicts where different version modules can create havoc within projects.

[Anaconda](https://www.anaconda.com/download/success) is an application that you should install before progressing, it is not needed though, but the next steps will be done with anaconda.


Virtual Environment with Anaconda
- *conda* is the command to package manager, *create* is a sub command to create new environment, *--name* is to specify the name of environment, and seniorDesign is the name of the environment
```
conda create --name seniorDesign 
```

> [!NOTE]
> For any future dependacies we will pip install/conda install directly within this environment.

To begin working in this environment we run the this command

```
# insert the name of your environment
conda activate "name of your environment"
```
To exit out of environment run this command

```
conda deactivate
```


###### InfluixDB Install

To install Influxdb 1.8 we first need to go to [Influxdb](https://www.influxdata.com/downloads/) Once you are in this page scroll all the way down to [Are you interested in InfluxDB 1.x Open Source?] select your operating system, in my case I will run the Ubuntu & Debian installation.
- run this commands
```
wget https://download.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb
sudo dpkg -i influxdb_1.8.10_amd64.deb
```
That should be all, but make sure to check by running this command

```
influx --version
```
The result should be = InfluxDB shell version: 1.8.10



#### Setting the Environment ready

Run the environment to install python modules. This are the installations we are going to need

1. Flask
2. InlfuxDB
3. FastApi
4. Uvicorn
5. Numpy
6. Scikit-learn



Start the environment
```
conda activate "name of project" 
```

This is the fast method of installing all the needed depedancies

```
 conda install flask fastapi uvicorn numpy 
```
We also need this (f2py normalizer influxdb) modules but conda couldn't find the packages. It turns out that f2py comes within numpy,and normalizer works with scikit-learn module. Since we already installed numpy with the command above we will move on to the other modules. This are the commands: 


```
pip install scikit-learn
```

the last command will be 

```
pip install influxdb

```

At this point in the process you might be asking yourself on why we are installing a module for influxdb when we install the db software on the system. The asnwer is simple,the module will be used to interact with the database using python scripts, the influx software is the database service. 


#### Launching

When launching the app, we need to make sure that influxdb is running, so we fist use this commands in order to get influxdb working. 

In VsCode open a terminal window, we need to enter our virtual environment.

```
conda activate " name of venv"
```

Once enable run this commands.
This is used in order start influxdb

```
sudo systemctl start influxdb
```
Afterwards we need to also make sure the status of the system is working, run this command.
```
sudo systemctl status influxdb
```
OUTPUT SHOULD LOOK SOMETHING LIKE THIS
![Screenshot from 2024-09-23 22-30-50](https://github.com/user-attachments/assets/5c03b765-bf7f-4254-8196-5614e12f4011)


To exit just enter this, its like Vim :)

```
:q
```
If all things go right run this command to get the program running 

```
python -m flask run
```
## PROCESSING SEM ALMANAC DATA WITH SCRIPT

Make sure that you cd into the correct file path, this file path needs to hold the generate_dop_data.py
Once you are here we make sure that the SEM ALMANAC file is also inside the same directory. 

> [!IMPORTANT]
> Check the path to file, in the original code the name for the SEM ALMANAC was different from new downloaded file.

This is the command at the moment to process the data conversion.
```
export TIME_KEY=2024-08-21T15:40:30Z
python generate_dop_data.py
```

## MAKING THE DATABASE (PART 1)

This command is used to start influxdb
```
sudo systemctl start influxdb
```

This checks if the system is running, to exit out afterwards use :q

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


## Queries
 SELECT * FROM dop LIMIT 10;
name: dop
time                GDOP HDOP Latitude Longitude NUM IN VIEW PDOP TDOP VDOP



# GPS Visibility Analysis

Author: Mark Mendiola, The Aerospace Corporation.

## Dependencies

Python 3.11.

### Install

```sh
python -m pip install -r requirements.txt
```

## Configure

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
