# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2026 RealSense, Inc. All Rights Reserved.

# Hub-recycle stress test: power-cycles the USB port the device under test is
# connected to (true cold plug-in via the OS, not an in-band hardware_reset),
# then verifies that the re-enumerated device exposes its full sensor set,
# in particular the Motion Module on IMU-bearing devices.
#
# This catches the partial-enumeration race where, on Windows, the device-
# watcher's debounce fires a "device added" callback before the HID Sensor
# Collection has bound at T0+~1s, surfacing a UVC-only device with no IMU and
# triggering "No HID info provided, IMU is disabled" / "HID Motion Sensor
# Failure! bad optional access" in the log.
#
# Requires a controllable hub (Acroname, Ykush, UniFi) attached to the
# machine; skips otherwise. Scheduled on the nightly context.

import pytest
import pyrealsense2 as rs
from rspy import devices, device_hub
from rspy.timer import Timer
import time
import logging
log = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.device_each("D435i"),
    pytest.mark.device_each("D455"),
    pytest.mark.device_each("D436"),
    pytest.mark.device_each("D430i"),
    pytest.mark.context("nightly"),
    pytest.mark.timeout(3600),
]

ITERATIONS_NIGHTLY = 20
ITERATIONS_WEEKLY  = 100
RECYCLE_DOWN_S     = 2   # seconds the port stays powered down between disable/enable

# Module-level state for the devices_changed_callback (matches the pattern used
# in pytest-stress.py - librealsense callbacks fire on internal threads and
# must use heap state).
target_sn    = None
new_dev      = None
device_added = False


def device_changed( info ):
    global target_sn, new_dev, device_added
    for candidate in info.get_new_devices():
        try:
            if candidate.get_info( rs.camera_info.serial_number ) == target_sn:
                new_dev      = candidate
                device_added = True
        except RuntimeError:
            continue


def test_hub_recycle_imu_presence( test_device, test_context_var ):
    global target_sn, new_dev, device_added

    dev, ctx = test_device
    target_sn = dev.get_info( rs.camera_info.serial_number )
    ctx.set_devices_changed_callback( device_changed )

    hub = device_hub.create()
    if hub is None:
        pytest.skip( "Test requires a controllable USB hub (Acroname / Ykush / UniFi)." )

    # Resolve which hub port the device under test is on, so we recycle only
    # its port and don't disturb other devices on the same hub.
    location = dev.get_info( rs.camera_info.physical_port ) if dev.supports( rs.camera_info.physical_port ) else None
    port     = None
    if location is not None:
        # rspy.devices._get_usb_location() does the path parsing; reuse it.
        from rspy.devices import _get_usb_location
        try:
            port = hub.get_port_by_location( _get_usb_location( location ) )
        except Exception:
            port = None
    portlist = [port] if port is not None else None  # None => recycle all ports
    if port is None:
        log.warning( "Could not resolve the device's hub port - recycling all ports" )

    is_weekly  = 'weekly' in test_context_var
    iterations = ITERATIONS_WEEKLY if is_weekly else ITERATIONS_NIGHTLY

    log.info( f"Hub-recycle IMU-presence test: {iterations} iterations on serial {target_sn}, port={port}" )

    missing_imu = []
    no_reappear = []

    for i in range( 1, iterations + 1 ):
        new_dev      = None
        device_added = False

        log.debug( f"[{i}/{iterations}] recycling port(s)" )
        hub.recycle_ports( portlist, timeout=RECYCLE_DOWN_S )

        # Wait for the device to be re-enumerated (callback signals when our
        # serial number reappears - matches pytest-stress.py).
        t = Timer( devices.MAX_ENUMERATION_TIME )
        t.start()
        while not t.has_expired():
            if device_added:
                break
            time.sleep( 0.1 )

        if not device_added:
            log.error( f"[{i}/{iterations}] device did not re-enumerate within {devices.MAX_ENUMERATION_TIME}s" )
            no_reappear.append( i )
            continue

        # Inspect sensors. If the partial-enumeration race fires, the device
        # comes up with only Stereo Module + RGB Camera.
        try:
            sensor_names = [ s.get_info( rs.camera_info.name ) for s in new_dev.query_sensors() ]
        except RuntimeError as e:
            log.error( f"[{i}/{iterations}] query_sensors raised: {e}" )
            missing_imu.append( i )
            continue

        if not any( "Motion" in n for n in sensor_names ):
            log.error( f"[{i}/{iterations}] Motion Module MISSING: {sensor_names}" )
            missing_imu.append( i )
        else:
            log.debug( f"[{i}/{iterations}] OK: {sensor_names}" )

    if no_reappear:
        log.error( f"Iterations that did not re-enumerate: {no_reappear}" )
    if missing_imu:
        log.error( f"Iterations with missing Motion Module: {missing_imu}" )

    assert not no_reappear, f"{len(no_reappear)}/{iterations} iterations: device did not re-enumerate"
    assert not missing_imu, f"{len(missing_imu)}/{iterations} iterations: device re-enumerated without Motion Module"
