<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot Detect and Follow

The Spot Detect and Follow example collects images from the two front Spot cameras and performs object detection on a specified class. This detection uses Tensorflow via the tensorflow_object_detector from the Spot Tensorflow Detector example. It accepts any Tensorflow model, and it allows the user to specify a subset of detection classes included in the model. It performs this set of operations for a predefined number of iterations, blocking for a predefined amount of time between each iteration. The example then determines the location of the highest confidence detection of the specified class and walks towards the object. The walking has a built-in buffer of about 3 meters.

IF USING THIS EXAMPLE TO FOLLOW A PERSON, FOLLOW ALL SAFETY PROTOCOLS. KEEP AWAY FROM ALL STAIRCASES.

The program is organized as three sets of Python processes communicating with the Spot robot. The process diagram is shown below. The main process communicates with the Spot robot over GRPC and constantly receives images. These images are pushed into the RAW_IMAGES_QUEUE and read by the Tensorflow processes. Those processes detect objects in the images and pushes the location onto PROCESSED_BOXES_QUEUE. The main thread then determines the location of the object and issues commands to the robot to walk towards the object.

<img src="documentation/Detect_and_Follow.png" alt="Process Diagram" width="800"/>

## User Guide
### Installation (Only if you want to run without Docker)
To install this example on Ubuntu 18.04, follow these instructions:
- Install python3: `sudo apt-get install python3.6`
- Install pip3: `sudo apt-get install python3-pip`
- Install virtualenv: `python3 -m pip install virtualenv`
- Change into example directory: `cd spot_detect_and_follow`
- Create virtual environment (one time operation): `virtualenv -p {PATH_TO_PYTHON3_EXECUTABLE} venv`. The path to the executable is the output of `which python3` command, usually set to `/usr/bin/python3`.
- Start virtual environment: `source venv/bin/activate`
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Add the tensorflow detector module to your PYTHONPATH: `export PYTHONPATH=/path/to/examples/spot_tensorflow_detector:$PYTHONPATH`
- Run `python3 -m pip install -r requirements.txt` within the `spot_tensorflow_detector` directory
- Run the example using instructions in the next section
- To exit the virtual environment, run `deactivate`

### Execution
Prior to running the example, you will need to acquire estop access from another source such as from a connected laptop or tablet. This allows you to to emergency stop the robot since this application does not have a GUI.
This example follows the common pattern for expected arguments. It needs the common arguments used to configure the SDK and connect to a Spot:
- --username 
- --password 
- hostname passed as the last argument

On top of those arguments, it also needs the following arguments:
- --model-path (required) argument that specifies the path of the Tensorflow model (a file in .pb format)
- --detection-class (required) argument that specifies the detection class from the Tensorflow model to follow (a list of class codes can be found in COCO_CLASS_DICT in `spot_detect_and_follow.py`)
- --detection-threshold (optional) argument that specifies the confidence threshold (0-1) to use to consider the Tensorflow detections as real detections. Lower values increase false positives. Higher values may lower detection rate; defaults to 0.7
- --number-tensorflow-processes (optional) argument that specifies the number of Tensorflow processes to start. When running with the GPU, 1 process is enough since the GPU takes care of parallelization; defaults to 1
- --sleep-between-capture (optional) argument that specifies the amount to sleep in seconds between each image capture iteration. Increasing the value of this argument reduces the size of the queues, but also reduces the rate of command updates at the end of the pipeline; defaults to 1.0.
- --max-processing-delay (optional) argument that specifies max delay in seconds allowed for each image before being processed; images with greater latency will not be processed; defaults to 7.0.

```
python3 spot_detect_and_follow.py --username USER --password PASSWORD --model-path <path_to_pb> --detection-class <integer cladd id> ROBOT_IP
```

#### Running in Docker
Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on SpotCORE as docker containers.

This example provides a Dockerfile for running in a container. This requires installing Nvidia Docker.
You can follow the instructions at https://github.com/NVIDIA/nvidia-docker to install Nvidia Docker.
Nvidia Docker is preinstalled on the Spot CORE AI.

To build the image, you'll need to first copy over the tensorflow detector file first:
```sh
cp /path/to/examples/spot_tensorflow_detector/tensorflow_object_detector.py .
sudo docker build -t spot_detect_and_follow .
```

To run a container:
```sh
sudo docker run --gpus all -it \
--network=host \
-v <absolute_path_to_pb>:/model.pb \
-v <absolute_path_to_classes>:/classes.json \
spot_detect_and_follow \
--model-path /model.pb \
--detection-class 1
<typical other arguments after "python spot_detect_and_follow.py">
ROBOT_HOSTNAME
```

As an example, the `faster_rcnn_inception_v2_coco` Tensorflow model pre-trained on COCO dataset can be obtained [here](http://download.tensorflow.org/models/object_detection/faster_rcnn_inception_v2_coco_2018_01_28.tar.gz). Run the example with `--model-path` pointing to the `pb` file in that model and with `--detection-classes` argument set to `1` to detect people in the camera images. That model is not supported on Windows or MacOS.
The pre-trained models may not be good at detecting some classes when using the robot's cameras, as the fisheye distortion, low resolution, and black and white images affect image quality. For example, pre-trained models may not perform well at detecting "sports balls" due to the lack of color. The [ssd_mobilenet_v2_coco](http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz) and [faster_rcnn_inception_v2_coco](http://download.tensorflow.org/models/object_detection/faster_rcnn_inception_v2_coco_2018_01_28.tar.gz) have been tested to work well at detecting humans.