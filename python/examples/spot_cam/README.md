<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot CAM Services

These examples demonstrate how to interact with the Spot CAM.

## Setup Dependencies
These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.
```
python3 -m pip install -r requirements.txt
```

Older versions of pip may have trouble installing all of the requirements.  If you run into a problem, upgrade pip by running
```
python3 -m pip install --upgrade pip
```

## Running the Example
To run the examples:
```
USERNAME=<username>
PASSWORD=<password>
ROBOT_IP=<ip-address>

# Version Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP version software

# Audio Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio set_volume 1
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio get_volume
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio load autonomous_robot_en autonomous_robot_en.wav
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio list
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio play autonomous_robot_en
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio delete autonomous_robot_en
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP audio list

# Compositor Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor list
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor get
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor set mech
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor visible
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor get_colormap
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP compositor set_colormap color jet

# Lighting Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP lighting set 0.1 0.2 0.3 0.4
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP lighting get

# Media Log Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log list_cameras
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log store pano
# The UUID is given by the 'store' command
IMAGE_UUID=f0e835c2-54d4-11ea-9365-00044be03a91
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log status $IMAGE_UUID
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log retrieve $IMAGE_UUID
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log delete $IMAGE_UUID

# You should not see the UUID in the list of logpoints
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log list_logpoints

# You should see 10 stitched jpeg images
seq 10 | xargs -I{} python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP media_log store_retrieve pano

# Ptz Service
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP ptz list
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP ptz set_position mech 0 0 1
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP ptz get_position mech

# You should see a ptz jpeg image
python -m command_line --username=$USERNAME --password=$PASSWORD -$ROBOT_IP media_log store_retrieve ptz

# WebRTC Service
# Save images to .jpg files
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP webrtc save
# Save 10 seconds of video (no audio)
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP webrtc record --time 10
# Save 10 seconds of audio
python -m command_line --username=$USERNAME --password=$PASSWORD $ROBOT_IP webrtc record audio --time 10
```
