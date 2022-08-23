# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the world object service"""
from __future__ import print_function

from bosdyn.api import geometry_pb2 as geom
from bosdyn.api import world_object_pb2, world_object_service_pb2
from bosdyn.api import world_object_service_pb2_grpc as world_object_service
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client.frame_helpers import *
from bosdyn.client.robot_command import NoTimeSyncError, _TimeConverter
from bosdyn.util import now_timestamp


class WorldObjectClient(BaseClient):
    """Client for World Object service."""
    default_service_name = 'world-objects'
    service_type = 'bosdyn.api.WorldObjectService'

    def __init__(self):
        super(WorldObjectClient, self).__init__(world_object_service.WorldObjectServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(WorldObjectClient, self).update_from(other)
        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    @property
    def timesync_endpoint(self):
        """Accessor for timesync-endpoint that is grabbed via 'update_from()'.

        Raises:
            bosdyn.client.robot_command.NoTimeSyncError: Could not find the timesync endpoint for
                the robot.
        """
        if not self._timesync_endpoint:
            raise NoTimeSyncError("[world object service] No timesync endpoint set for the robot")
        return self._timesync_endpoint

    def list_world_objects(self, object_type=None, time_start_point=None, **kwargs):
        """Get a list of World Objects.

        Args:
            object_type (list of bosdyn.api.WorldObjectType): Specific types to include in the
                                                              response, all other types will be
                                                              filtered out.
            time_start_point (float): A client timestamp to filter objects in the response. All objects
                                      will have a timestamp after this time.

        Returns:
            The response message, which includes the filtered list of all world objects.

        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.robot_command.NoTimeSyncError: Couldn't convert the timestamp into robot
                time.
        """
        if time_start_point is not None:
            time_start_point = self._update_time_filter(time_start_point, self.timesync_endpoint)
        req = world_object_pb2.ListWorldObjectRequest(object_type=object_type,
                                                      timestamp_filter=time_start_point)
        return self.call(self._stub.ListWorldObjects, req,
                         value_from_response=_get_world_object_value,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_world_objects_async(self, object_type=None, time_start_point=None, **kwargs):
        """Async version of list_world_objects()."""
        if time_start_point is not None:
            time_start_point = self._update_time_filter(time_start_point, self.timesync_endpoint)
        req = world_object_pb2.ListWorldObjectRequest(object_type=object_type,
                                                      timestamp_filter=time_start_point)
        return self.call_async(self._stub.ListWorldObjects, req,
                               value_from_response=_get_world_object_value,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def mutate_world_objects(self, mutation_req, **kwargs):
        """Mutate (add, change, delete) world objects.

        Args:
            mutation_req (world_object_pb2.MutateWorldObjectRequest): The request including
                                                                    the object to be mutated and the
                                                                    type of mutation.
        Returns:
            The response, which includes the id of the mutated object.

        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.robot_command.NoTimeSyncError: Couldn't convert the timestamp into robot
                time.
        """
        if mutation_req.mutation.object.HasField("acquisition_time"):
            # Ensure the mutation request's object's time of detection is in robot time.
            client_timestamp = mutation_req.mutation.object.acquisition_time
            mutation_req.mutation.object.acquisition_time.CopyFrom(
                self._update_timestamp_filter(client_timestamp, self.timesync_endpoint))
        return self.call(self._stub.MutateWorldObjects, mutation_req,
                         value_from_response=_get_status, error_from_response=common_header_errors,
                         **kwargs)

    def mutate_world_objects_async(self, mutation_req, **kwargs):
        """Async version of mutate_world_objects()."""
        if mutation_req.mutation.object.HasField("acquisition_time"):
            # Ensure the mutation request's object's time of detection is in robot time.
            client_timestamp = mutation_req.mutation.object.acquisition_time
            mutation_req.mutation.object.acquisition_time.CopyFrom(
                self._update_timestamp_filter(client_timestamp, self.timesync_endpoint))
        return self.call_async(self._stub.MutateWorldObjects, mutation_req,
                               value_from_response=_get_status,
                               error_from_response=common_header_errors, **kwargs)

    def _update_time_filter(self, timestamp, timesync_endpoint):
        """Set or convert fields of the proto that need timestamps in the robot's clock.

        Args:
            timestamp (float): Client time, such as from time.time().
            timesync_endpoint (TimeSyncEndpoint): A timesync endpoint associated with the robot object.

        Raises:
            NoTimeSyncError: Could not find the timesync endpoint for the robot to convert the time.
        """
        # Input timestamp is a float. (from time.time())
        if not timesync_endpoint:
            raise NoTimeSyncError("[world object service] No timesync endpoint set for the robot.")
        # Lazy RobotTimeConverter: initialized only if needed to make a conversion.
        converter = _TimeConverter(self, timesync_endpoint)
        return converter.robot_timestamp_from_local_secs(timestamp)

    def _update_timestamp_filter(self, timestamp, timesync_endpoint):
        """Set or convert fields of the proto that need timestamps in the robot's clock.

        Args:
            timestamp (google.protobuf.Timestamp): Client time.
            timesync_endpoint (TimeSyncEndpoint): A timesync endpoint associated with the robot object.

        Raises:
            NoTimeSyncError: Could not find the timesync endpoint for the robot to convert the time.
        """
        # Input timestamp is a google.protobuf.Timestamp
        if not timesync_endpoint:
            raise NoTimeSyncError("[world object service] No timesync endpoint set for the robot.")
        converter = _TimeConverter(self, timesync_endpoint)
        converter.convert_timestamp_from_local_to_robot(timestamp)
        return timestamp

    def draw_sphere(self, name, x_rt_frame_name, y_rt_frame_name, z_rt_frame_name, frame_name,
                    radius=0.05, rgba=(255, 0, 0, 1), list_objects_now=True):
        """Create a drawable sphere world object that will be sent to the world object service
        with a mutation request.

        Args:
            name (string): The human-readable name of the world object.
            x_rt_frame_name,y_rt_frame_name,z_rt_frame_name (int): The coordinate position (x,y,z) of
                the drawable sphere.
            frame_name (string): the frame in which the sphere's position is described.
            radius (float): The radius for the drawn sphere.
            rgba (4 valued tuple): The RGBA color, where RGB are int values in [0,255] and A is a float in [0,1].
            list_objects_now (boolean): Should the ListWorldObjects request be made after creating
                the sphere world object.

        Returns:
            The MutateWorldObjectResponse for the addition of the sphere world object.
        """
        vision_tform_drawable = geom.SE3Pose(
            position=geom.Vec3(x=x_rt_frame_name, y=y_rt_frame_name, z=z_rt_frame_name),
            rotation=geom.Quaternion(w=1, x=0, y=0, z=0))
        # Create a map between the child frame name and the parent frame name/SE3Pose parent_tform_child
        edges = {}
        # Create an edge in the frame tree snapshot that includes vision_tform_drawable
        drawable_frame_name = name
        edges = add_edge_to_tree(edges, vision_tform_drawable, frame_name, drawable_frame_name)
        snapshot = geom.FrameTreeSnapshot(child_to_parent_edge_map=edges)

        # Set the acquisition time for the sphere using a function to get google.protobuf.Timestamp of the current system time.
        time_now = now_timestamp()

        # Create the sphere drawable object
        sphere = world_object_pb2.DrawableSphere(radius=radius)
        draw_color = world_object_pb2.DrawableProperties.Color(r=rgba[0], g=rgba[1], b=rgba[2],
                                                               a=rgba[3])
        sphere_drawable_prop = world_object_pb2.DrawableProperties(
            color=draw_color, label=name, wireframe=False, sphere=sphere,
            frame_name_drawable=drawable_frame_name)

        # Create the complete world object with transform information, a unique name, and the drawable sphere properties.
        sphere_to_add = world_object_pb2.WorldObject(name=name, transforms_snapshot=snapshot,
                                                     acquisition_time=time_now,
                                                     drawable_properties=[sphere_drawable_prop])
        # Add the sphere to the robot's world object service
        add_sphere = make_add_world_object_req(sphere_to_add)
        resp = self.mutate_world_objects(mutation_req=add_sphere)

        if list_objects_now:
            # Request a listing of the world objects so that the sphere shows up in the log.
            self.list_world_objects()

        return resp

    def draw_oriented_bounding_box(self, name, drawable_box_frame_name, frame_name,
                                   frame_name_tform_drawable_box, size_ewrt_box_vec3,
                                   rgba=(255, 0, 0, 1), wireframe=True, list_objects_now=False):
        """Create a drawable 3D box world object that will be sent to the world object service
        with a mutation request.

        Args:
            name (string): The human-readable name of the world object.
            drawable_box_frame_name (string): The frame name for the drawable box frame.
            frame_name (string): The frame name which the drawable box is described relative to.
            frame_name_tform_drawable_box (geometry_pb2.SE3Pose): the SE3 pose of the drawable box relative to frame name.
            size_ewrt_box_vec3 (float): The size of the box (x,y,z) expressed with respect to the
                drawable box frame.
            rgba (4 valued tuple): The RGBA color, where RGB are int values in [0,255] and A is a float in [0,1].
            wireframe  (boolean): Should this be drawn as a wireframe [wireframe=true] or a solid object [wireframe=false].
            list_objects_now (boolean): Should the ListWorldObjects request be made after creating
                the sphere world object.

        Returns:
            The MutateWorldObjectResponse for the addition of the sphere world object.
        """
        # Create a map between the child frame name and the parent frame name/SE3Pose parent_tform_child
        edges = {}
        # Create an edge in the frame tree snapshot that includes frame_tform_box
        drawable_frame_name = name
        edges = add_edge_to_tree(edges, frame_name_tform_drawable_box, frame_name,
                                 drawable_frame_name)
        snapshot = geom.FrameTreeSnapshot(child_to_parent_edge_map=edges)

        # Set the acquisition time for the box using a function to get google.protobuf.Timestamp of the current system time.
        time_now = now_timestamp()

        # Create the box drawable object
        box = world_object_pb2.DrawableBox(size=size_ewrt_box_vec3)
        draw_color = world_object_pb2.DrawableProperties.Color(r=rgba[0], g=rgba[1], b=rgba[2],
                                                               a=rgba[3])
        box_drawable_prop = world_object_pb2.DrawableProperties(
            color=draw_color, label=name, wireframe=wireframe, box=box,
            frame_name_drawable=drawable_box_frame_name)

        # Create the complete world object with transform information, a unique name, and the drawable box properties.
        box_to_add = world_object_pb2.WorldObject(name=name, transforms_snapshot=snapshot,
                                                  acquisition_time=time_now,
                                                  drawable_properties=[box_drawable_prop])
        # Add the box to the robot's world object service
        add_box = make_add_world_object_req(box_to_add)
        resp = self.mutate_world_objects(mutation_req=add_box)

        if list_objects_now:
            # Request a listing of the world objects so that the box shows up in the log.
            self.list_world_objects()

        return resp


def _get_world_object_value(response):
    return response


def _get_status(response):
    if (response.status != world_object_pb2.MutateWorldObjectResponse.STATUS_OK):
        if (response.status == world_object_pb2.MutateWorldObjectResponse.STATUS_INVALID_MUTATION_ID
           ):
            print("Object id not found, and could not be mutated.")
        if (response.status == world_object_pb2.MutateWorldObjectResponse.STATUS_NO_PERMISSION):
            print(
                "Cannot change/delete objects detected by Spot's perception system, only client objects."
            )
    return response


'''
Static helper methods for constructing mutation requests for a given world object.
'''


def make_add_world_object_req(world_obj):
    """Add a world object to the scene.

    Args:
        world_obj (WorldObject): The world object to be added into the robot's perception scene.

    Returns:
        A MutateWorldObjectRequest where the action is to "add" the object to the scene.
    """
    add_obj = world_object_pb2.MutateWorldObjectRequest.Mutation(
        action=world_object_pb2.MutateWorldObjectRequest.ACTION_ADD, object=world_obj)
    req = world_object_pb2.MutateWorldObjectRequest(mutation=add_obj)
    return req


def make_delete_world_object_req(world_obj):
    """Delete a world object from the scene.

    Args:
        world_obj (WorldObject): The world object to be deleted in the robot's perception scene. The
                                 object must be a client-added object and have the correct world object
                                 id returned by the service after adding the object.

    Returns:
        A MutateWorldObjectRequest where the action is to "delete" the object to the scene.
    """
    del_obj = world_object_pb2.MutateWorldObjectRequest.Mutation(
        action=world_object_pb2.MutateWorldObjectRequest.ACTION_DELETE, object=world_obj)
    req = world_object_pb2.MutateWorldObjectRequest(mutation=del_obj)
    return req


def make_change_world_object_req(world_obj):
    """Change/update an existing world object in the scene.

    Args:
        world_obj (WorldObject): The world object to be changed/updated in the robot's perception scene.
                                 The object must be a client-added object and have the correct world object
                                 id returned by the service after adding the object.

    Returns:
        A MutateWorldObjectRequest where the action is to "change" the object to the scene.
    """
    change_obj = world_object_pb2.MutateWorldObjectRequest.Mutation(
        action=world_object_pb2.MutateWorldObjectRequest.ACTION_CHANGE, object=world_obj)
    req = world_object_pb2.MutateWorldObjectRequest(mutation=change_obj)
    return req
