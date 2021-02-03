# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function
import os
import io
import json
import time
import logging

from bosdyn.api import data_acquisition_pb2
from bosdyn.api import data_acquisition_store_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.exceptions import ResponseError

from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format

# Logger for all the debug information from the tests.
_LOGGER = logging.getLogger()

def issue_acquire_data_request(data_acq_client, acquisition_requests, group_name,
	                           action_name, metadata=None):
    """Sends the data acquisition request without blocking until the acquisition completes.

    Args:
        data_acq_client: DataAcquisition client for send the acquisition requests.
        acquisition_requests: Acquisition requests to include in request message.
        group_name: Group name for the acquisitions.
        action_name: Action name for the acquisitions.
        metadata: Metadata to include in the request message.

    Returns:
        The request id (int) and the action id (CaptureActionId). A request id set as None
        indicates the AcquireData rpc failed.
    """
    # Create action id for the query for this request.
    action_id = data_acquisition_pb2.CaptureActionId(action_name=action_name,
                                                     group_name=group_name)

    # Send an AcquireData request
    request_id = None
    try:
        request_id = data_acq_client.acquire_data(acquisition_requests=acquisition_requests,
            action_name=action_name, group_name=action_id.group_name, metadata=metadata)
    except ResponseError as err:
        print("Exception raised by issue_acquire_data_request: " + str(err))

    return request_id, action_id

def acquire_and_process_request(data_acquisition_client, acquisition_requests, group_name,
                                action_name, metadata=None, block_until_complete=True):
    """Send acquisition request and optionally block until the acquisition completes.

    If blocking, the GetStatus RPC is used to monitor the status of the acquisition request.

    Args:
        data_acquisition_client (DataAcquisitionClient): The client for send the acquisition requests.
        acquisition_requests(data_acquisition_pb2.AcquisitionRequestList): Acquisition requests
            to include in request message.
        group_name(string): Group name for the acquisitions.
        action_name(string): Action name for the acquisitions.
        metadata(data_acquisition_pb2.Metadata): Metadata to include in the request message.
        block_until_complete(Boolean): If true, don't return until the GetStatus completes.

    Returns:
        Boolean indicating if the acquisition completed successfully or not.
    """
    # Make the acquire data request. This will return our current request id.
    request_id, action_id = issue_acquire_data_request(data_acquisition_client, acquisition_requests,
        group_name, action_name, metadata)

    if not request_id:
        # The AcquireData request failed for some reason. No need to attempt to
        # monitor the status.
        return False

    if not block_until_complete:
        return True

    # Monitor the status of the data acquisition.
    print("Waiting for acquisition (id: %s) to complete." % str(request_id))
    while True:
        get_status_response = None
        try:
            get_status_response = data_acquisition_client.get_status(request_id)
        except ResponseError as err:
            print("Exception: %s" % str(err))
            return False
        print("Current status is: %s" %
            data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_COMPLETE:
            return True
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_TIMEDOUT:
            print("Unrecoverable request timeout: %s" % get_status_response)
            return False
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_DATA_ERROR:
            print("Data error was received: %s" % get_status_response)
            return False
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_REQUEST_ID_DOES_NOT_EXIST:
            print("The acquisition request id %s is unknown: %s" % (request_id, get_status_response))
            return False
        time.sleep(0.2)
    return True

def cancel_acquisition_request(data_acq_client, request_id):
    """Cancels an acquisition request based on the request id

    Args:
        data_acq_client: DataAcquisition client for send the acquisition requests.
        request_id: The id number for the AcquireData request to cancel.

    Returns:
        None.
    """
    if not request_id:
        # The incoming request id is invalid. No need to attempt to cancel the request or
        # monitor the status.
        return

    try:
        is_cancelled_response = data_acq_client.cancel_acquisition(request_id)
        print("Status of the request to cancel the data-acquisition in progress: " +
            data_acquisition_pb2.CancelAcquisitionResponse.Status.Name(is_cancelled_response.status))
    except ResponseError as err:
        print("ResponseError raised when cancelling: "+str(err))
        # Don't attempt to wait for the cancellation success status.
        return

    # Monitor the status of the cancellation to confirm it was successfully cancelled.
    while True:
        get_status_response = None
        try:
            get_status_response = data_acq_client.get_status(request_id)
        except ResponseError as err:
            print("Exception: " + str(err))
            break

        print("Request " + str(request_id) + " status: " +
            data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_ACQUISITION_CANCELLED:
            print("The request is fully cancelled.")
            break

def clean_filename(filename):
    """Removes bad characters in a filename.

    Args:
        filename(string): Original filename to clean.

    Returns:
        Valid filename with removed characters \:\*\?\<\>\|
    """

    return "".join(i for i in filename if i not in ":*?<>|")

def make_time_query_params(start_time_secs, end_time_secs, robot):
    """Create time-based query params for the download request.

    Args:
        start_time_secs(float): The start time for the download data range.
        end_time_secs(float): The end time for the download range.
        robot (Robot): The robot object, used to acquire timesync and convert the
                       times to robot time.
    Returns:
        The query params (data_acquisition_store_pb2.DataQueryParams) for the time-range download.
    """
    from_timestamp = robot.time_sync.robot_timestamp_from_local_secs(start_time_secs)
    to_timestamp = robot.time_sync.robot_timestamp_from_local_secs(end_time_secs)
    print(from_timestamp.ToJsonString(), to_timestamp.ToJsonString())
    query_params = data_acquisition_store_pb2.DataQueryParams(
        time_range=data_acquisition_store_pb2.TimeRangeQuery(from_timestamp=from_timestamp,
            to_timestamp=to_timestamp))
    return query_params

def make_time_query_params_from_group_name(group_name, data_store_client):
    """Create time-based query params for the download request using the group name.

    Args:
        group_name(string): The group name for the data to be downloaded.
        data_store_client(DataAcquisitionStoreClient): The data store client, used to get the
                                                       action ids for the group name.

    Returns:
        The query params (data_acquisition_store_pb2.DataQueryParams) for the time-range download.
    """
    action_id = data_acquisition_pb2.CaptureActionId(group_name=group_name)
    query_params = data_acquisition_store_pb2.DataQueryParams(
        action_ids=data_acquisition_store_pb2.ActionIdQuery(action_ids=[action_id]))
    saved_capture_actions = []
    try:
        saved_capture_actions = data_store_client.list_capture_actions(query_params)
    except Exception as err:
        _LOGGER.error("Failed to list the capture action ids for group_name %s: %s", group_name, err)
        return None

    # Filter all the CaptureActionIds for the start/end time. These end times are already in
    # the robots clock and do not need to be converted using timesync.
    start_time = (None, None)
    end_time = (None, None)
    for action_id in saved_capture_actions:
        timestamp = action_id.timestamp
        time_secs = timestamp.seconds + timestamp.nanos / 1e9
        if time_secs == 0:
            # The plugin captures don't seem to set a timestamp, so ignore them when determining
            # the start/end times for what to download.
            continue
        if start_time[0] is None or time_secs < start_time[0]:
            start_time = (time_secs, timestamp)
        if end_time[0] is None or time_secs > end_time[0]:
            end_time = (time_secs, timestamp)

    if not (start_time and end_time):
        _LOGGER.error("Could not find a start/end time from the list of capture action ids: %s", saved_capture_actions)
        return None

    # Ensure the timestamps are ordered correctly and the
    assert start_time[0] <= end_time[0]

    # Adjust the start/end time by a few seconds each to give buffer room.
    start_time[1].seconds -= 3
    end_time[1].seconds += 3

    _LOGGER.info("Downloading data with a start time  of %s seconds and end time of %s seconds.", start_time[0], end_time[0])

    # Make the download data request with a time query parameter.
    query_params = data_acquisition_store_pb2.DataQueryParams(
        time_range=data_acquisition_store_pb2.TimeRangeQuery(from_timestamp=start_time[1],
                                                                to_timestamp=end_time[1]))
    return query_params

def download_data_REST(query_params, hostname, token, destination_folder='.',
                       additional_params=None):
    """Retrieve all data for a query from the DataBuffer REST API and write it to files.

    Args:
        query_params(bosdyn.api.DataQueryParams): Query parameters to use to retrieve metadata from
            the DataStore service. Must be time-based query parameters only.
        hostname(string): Hostname to specify in URL where the DataBuffer service is running.
        token(string): User token to specify in https GET request for authentication.
        destination_folder(string): Folder where to download the data.
        additional_params(dict): Additional GET parameters to append to the URL.

    Returns:
        Boolean indicating if the data was downloaded successfully or not.
    """
    import requests
    try:
        url = 'https://{}/v1/data-buffer/daq-data/'.format(hostname)
        folder = clean_filename(os.path.join(destination_folder, 'REST'))
        if not os.path.exists(folder):
            os.mkdir(folder)
        headers = {"Authorization": "Bearer {}".format(token)}
        get_params = additional_params or {}
        if query_params.HasField('time_range'):
            get_params.update({'from_nsec': query_params.time_range.from_timestamp.ToNanoseconds(),
                'to_nsec': query_params.time_range.to_timestamp.ToNanoseconds()})
        chunk_size = 10 * (1024 ** 2) # This value is not guaranteed.

        with requests.get(url, verify=False, stream=True, headers=headers,
            params=get_params) as resp:
            print("Download request HTTPS status code: %s" % resp.status_code)
            # This is the default file name used to download data, updated from response.
            if resp.status_code == 204:
                print("No content available for the specified download time range (in seconds): "
                "[%d, %d]"% (query_params.time_range.from_timestamp.ToNanoseconds()/1.0e9,
                query_params.time_range.to_timestamp.ToNanoseconds()/1.0e9))
                return False
            download_file = os.path.join(folder, "download.zip")
            content = resp.headers['Content-Disposition']
            if len(content) < 2:
                print("ERROR: Content-Disposition is not set correctly")
                return False
            else:
                start_ind = content.find('\"')
                if start_ind == -1:
                    print("ERROR: Content-Disposition does not have a \"")
                    return False
                else:
                    start_ind += 1
                    download_file = os.path.join(folder, content[start_ind:-1])

            with open(download_file, 'wb') as fid:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    print('.', end = '', flush=True)
                    fid.write(chunk)
    except requests.exceptions.HTTPError as rest_error:
        print("REST Exception:\n")
        print(rest_error)
        return False
    except IOError as io_error:
        print("IO Exception:\n")
        print(io_error)
        return False

    # Data downloaded and saved to local disc successfully.
    return True
