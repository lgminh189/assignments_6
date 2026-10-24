#!/usr/bin/env python3
"""Manual Gazebo integration check. Stop gesture_control/Nav2/teleop first.

Uses real scan/odometry and synthetic gesture messages, not webcam recognition.
Run after arena startup, successful undock, and moving the dock aside.
"""
import sys, time, math, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src/tb4_assignment/scripts'))
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped
from robot_behavior_node import RobotBehaviorNode

rclpy.init(args=['--ros-args', '-p', 'use_sim_time:=true', '-r', '/detected_gesture:=/gesture_test/input'])
robot = RobotBehaviorNode()
probe = Node('gesture_integration_probe')
pub = probe.create_publisher(String, '/gesture_test/input', 1)
commands = []
probe.create_subscription(TwistStamped, '/cmd_vel', lambda m: commands.append((time.monotonic(), m.twist.linear.x, m.twist.angular.z)), 10)
executor = SingleThreadedExecutor()
executor.add_node(robot)
executor.add_node(probe)
results = {}

def pump(seconds, label=None):
    end = time.monotonic() + seconds
    next_pub = 0.
    while time.monotonic() < end:
        if label and time.monotonic() >= next_pub:
            pub.publish(String(data=label))
            next_pub = time.monotonic() + .05
        executor.spin_once(timeout_sec=.01)

try:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and time.monotonic() - min(robot.scan_at, robot.odom_at) > .8:
        pump(.1)
    print('Sensors:', robot.scan_at, robot.odom_at, 'obstacle:', robot.obstacle(), flush=True)
    assert time.monotonic() - min(robot.scan_at, robot.odom_at) < .8
    publishers = probe.get_publishers_info_by_topic('/cmd_vel')
    assert sum(p.node_name == 'robot_behavior_node' for p in publishers) == 1, 'Stop other behavior nodes first'
    assert all(p.node_name in {'robot_behavior_node', 'cmd_vel_bridge'} for p in publishers), 'Stop other /cmd_vel publishers first'
    initial = robot.controller.pose
    for label in ['Pointing_Up', 'Victory', 'Wave']:
        pump(.4, 'No_Hand')
        pump(1., label)
        assert robot.controller.pending == label, robot.controller.status
        assert not robot.controller.plan
        selected_pose = robot.controller.pose
        pump(1., 'Thumb_Up')
        assert robot.controller.running == label, robot.controller.status
        started = time.monotonic()
        poses = [robot.controller.pose]
        while robot.controller.plan and time.monotonic() - started < 95:
            pump(.1, 'No_Hand')
            poses.append(robot.controller.pose)
        assert robot.controller.status == 'IDLE: completed', robot.controller.status
        assert max(math.hypot(p[0]-selected_pose[0], p[1]-selected_pose[1]) for p in poses) > (.1 if label != 'Wave' else -.1)
        pump(1., 'Thumb_Up')
        assert not robot.controller.plan
        results[label] = {'status': robot.controller.status, 'duration_seconds': round(time.monotonic()-started, 2), 'start_pose': selected_pose, 'end_pose': robot.controller.pose}
        print(label, results[label], flush=True)
    for stop in ['Open_Palm', 'Closed_Fist', 'Camera_Error', None]:
        pump(.4, 'No_Hand')
        pump(1., 'Pointing_Up')
        pump(1., 'Thumb_Up')
        assert robot.controller.plan, robot.controller.status
        before = time.monotonic()
        pump(.15 if stop else 1.1, stop)
        assert not robot.controller.plan, robot.controller.status
        assert commands[-1][1:] == (0., 0.)
        results[stop or 'signal_loss'] = {'status': robot.controller.status, 'checked_after_seconds': round(time.monotonic()-before, 3)}
        print(stop or 'signal_loss', results[stop or 'signal_loss'], flush=True)
    results['cmd_vel_nonzero_seen'] = any(v or w for _,v,w in commands)
    results['initial_pose'] = initial
    print(json.dumps(results, indent=2), flush=True)
    with Path(__file__).with_name('simulation_results.json').open('w') as f:
        json.dump(results, f, indent=2)
finally:
    robot.controller.stop('STOPPED: integration cleanup')
    robot.publish_velocity(0., 0.)
    pump(.2)
    executor.shutdown()
    robot.destroy_node()
    probe.destroy_node()
    rclpy.shutdown()
