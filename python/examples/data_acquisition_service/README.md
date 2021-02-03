<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Data Acquisition Plugin Services

The example programs demonstrate how to create a data acquisition plugin service and run the service such that it can communicate with the data acquisition service on-robot. A data acquisition plugin service is used to communicate with external payloads and hardware, retrieve the data from these sensors, and save the data in the data acquisition store service.

The DataAcquisitionPluginService base class (defined in `data_acquisition_plugin_service.py`) can be used to create the data acquisition plugin services. The example directory contains multiple different example plugins, each contained in their own folder, which use these helper functions to create plugin services which can collect data from various sensors (including a Piksi GPS or a point-cloud producing service, such as a Velodyne), or save json-formatted metadata relating to a sensor (`gps_metadata_plugin_service.py`).

## Setup Dependencies
Each example plugin requires the Spot SDK to be installed, and must be run using python3. Within the example plugin's directory and using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

Note, this command must be run from within the directory containing the specific plugin service file that will be run.

## Running the Data Acquisition Example Plugin Services

Each data acquisition plugin example will run the service locally and register it with the robot's directory service using a directory keep alive. After running the plugin service, the data acquisition service on the robot will detect the registration and adopt the plugin capabilities. This will allow your data acquisition plugin's capabilities to be available in the tablet or other applications communicating with the data acquisition service.

To run a plugin service from this example directory, issue the command:

```
python3 {PLUGIN_FILE_NAME} --guid {GUID} --secret {SECRET} --host-ip {IP_WHERE_PLUGIN_WILL_RUN} --port {PORT_THE_PLUGIN_WILL_MONITOR} {ROBOT_IP}
```
Note: The pointcloud plugin will require you to pass the registered service name. You can find this by running `python -m bosdyn.client --username {USER} --password {PASSWORD} {ROBOT_IP} dir list`

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the data acquisition plugin service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the plugin service:
```
python3 -m bosdyn.client --username {USER} --password {PASSWORD} {ROBOT_IP} self-ip
```
The other IP address is the traditional robot hostname ("ROBOT_IP") argument, which describes the IP address of the robot hosting the directory service.

Since the example is created to run off of a payload computer, it requires the input arguments `--guid` (uniquely generated payload specifier) and `--secret` (private string associated with a payload) for the registered payload computer that will be running the example plugins. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.

For the Spot CORE, this information by default will be located in the file `/opt/payload_credentials/payload_guid_and_secret`.

Note, you can run the example plugins locally on your PC by registering it as a weightless payload using [the payloads example](../payloads/README.md) and creating a GUID and secret for your computer.

Lastly, port numbers for the example plugin services can be specified using the `--port` ("PORT_THE_PLUGIN_WILL_MONITOR") argument. It is possible to bypass the port argument and allow a random port number to be selected, but it is discouraged since restarts may result in unexpected changes to a services listening port. The port numbers will be used with the `--host-ip` ("IP_WHERE_PLUGIN_WILL_RUN") to fully specify where the two services are running on the payload computer. The port numbers of different plugins cannot be the same, they must be open, and they must not be blocked by a local firewall, otherwise the service will be unreachable from the robot and other applications.

The network ports used by the services can be opened by running this command on the host computer (Linux):
```
sudo ufw allow {PORT_NUMBER}
```

## Testing the Data Acquisition Plugin

There is a [plugin tester script](../tester_programs/README.md) that can be used while developing a new data acquisition plugin service to help ensure that the service can be communicated with and behaves as expected. The script runs through a series of tests checking the networking and the functionality of each of the plugin's RPCs.

## Communicating with the Data Acquisition Service

The data acquisition example shows a program which communicates with the data acquisition service on robot and runs through the different data acquisition service RPCs. The data acquisition service will aggregate responses from each plugin service and will direct communication and requests to the specific plugins.

Run the example that communicates with the data acquisition service:
```
python3 data_acquisition_example.py --username {USER} --password {PASSWORD} {ROBOT_IP}
```

## Downloading from the Data Acquisition Store

The data acquisition download script allows users to download data from the DataAcquisitionStore service using REST calls. The script supports only time-based queries for filtering which data is downloaded and saved locally. The following command is an example of a time-based query and download. The timestamps are specified in RFC 3339 date string format (YYYY-MM-DDTHH:MM::SS.SZ, Y:year, M:month, D:day, H:hours, M:minutes, S:seconds as double, Z:zulu timezone)
```
python3 data_acquisition_download.py --username {USER} --password {PASSWORD} {ROBOT_IP} --query-from-timestamp 2020-09-01T00:00:00.0Z --query-to-timestamp 2020-09-04T00:00:00.0Z
```

Note, by default, the download script will save the data to the current directory, however the `--destination-folder` argument can be used to change where the downloaded data is saved.

## Run a Data Acquisition Plugin Service using Docker
Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on computation payloads as docker containers.

With docker installed and setup, any of the data acquisition plugin services can be created into a docker container, saved as a tar file, and then run on the Spot CORE using Portainer. There are Dockerfiles for each plugin service within the plugin's specific directory. These files will create a docker container with all necessary dependencies installed, and will start the plugin service.

Follow the instructions on how to build and use the docker image from [this section](../../../docs/payload/docker_containers.md#build-docker-images) on. The application arguments needed to run the plugins included in this example are `--host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET ROBOT_IP`.