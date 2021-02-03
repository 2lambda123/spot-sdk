<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# bosdyn-core

<p align="center">
<img src="https://www.bostondynamics.com/sites/default/files/2020-05/spot.png" style="max-width:50%;">
</p>

The bosdyn-core wheel contains core helper functions for the Boston Dynamics Spot API. The classes 
defined in this wheel are used by the clients in 
[bosdyn-client](https://pypi.org/project/bosdyn-client/) and 
[bosdyn-mission](https://pypi.org/project/bosdyn-mission/) wheels to communicate with the services 
running on the Spot robots. The wheel contains two classes:
* **Geometry**: Helper functions to convert between quaternions and Euler XYZ orientations.
* **Util**: Common utility functions for API Python code.
