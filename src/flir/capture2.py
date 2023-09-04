import os
import sys
import subprocess
import stat
import time
import threading  # Added for multi-threading support

# files
from glob import glob
from natsort import natsorted

# dates
import datetime

# arguments
import json
import argparse

# PySpin
import PySpin


NUM_IMAGES = 10  # Number of images to capture

def set_camera_parameters(cam, nodemap, nodemap_tldevice, fps=5, height=1080,
                          width=1000, offsetx=80, offsety=236):
    """
    Set capture parameters.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :param fps: Frames per second.
    :param height: Image height.
    :param width: Image width.
    :param offsetx: Image offset x.
    :param offsety: Image offset y.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :type fps: int Default = 5.
    :type height: int Default = 1080.
    :type width: int Default = 1920.
    :type offsetx: int Default = 80.
    :type offsety: int. Default = 236.
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print("\n*** SETTING CAMERA PARAMETERS ***\n")
    try:
        result = True

        # *** Frame rate ***
        node_acquisition_fps_auto = PySpin.CEnumerationPtr(
            nodemap.GetNode("AcquisitionFrameRateAuto"))
        node_acquisition_fps_auto.SetIntValue(0)

        cam.AcquisitionFrameRate.SetValue(fps)

        # *** Image size ***
        #max_height = cam.Height.GetMax()
        #max_width = cam.Width.GetMax()
        #cam.Height.SetValue(max_height)
        #cam.Width.SetValue(max_width)

        cam.OffsetX.SetValue(offsetx)
        cam.OffsetY.SetValue(offsety)

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result

def acquire_images(cam, nodemap, nodemap_tldevice, output_folder):
    """
    Acquires and saves N images from a device.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :param output_folder: Folder to save captured images.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :type output_folder: str
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print("\n*** IMAGE ACQUISITION ***\n")
    try:
        result = True

        # Set acquisition mode to continuous
        node_acquisition_mode = PySpin.CEnumerationPtr(
            nodemap.GetNode("AcquisitionMode"))
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName("Continuous")
        node_acquisition_mode.SetIntValue(node_acquisition_mode_continuous.GetValue())

        cam.BeginAcquisition()

        print("\n*** Acquiring images ***\n")

        device_serial_number = ""
        node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceSerialNumber"))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()

        processor = PySpin.ImageProcessor()
        processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)

        for i in range(NUM_IMAGES):
            try:
                image_result = cam.GetNextImage()

                if image_result.IsIncomplete():
                    print("Image incomplete with image status %d ..." % image_result.GetImageStatus())
                else:
                    width = image_result.GetWidth()
                    height = image_result.GetHeight()

                    image_converted = processor.Convert(image_result, PySpin.PixelFormat_RGB8)

                    now = today.strftime("%Y%m%d_%H%M%S")
                    if device_serial_number:
                        filename = "{}-{}-{}.jpg".format(device_serial_number, now, str(i).zfill(6))
                    else:
                        filename = "{}-{}.jpg".format(now, str(i).zfill(6))

                    image_converted.Save(os.path.join(output_folder, filename))
                    print("Image saved at %s" % filename)

                    image_result.Release()

            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
                return False

        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result

def run_single_camera(cam, cfg):
    """
    Run the camera.

    :param cam: Camera to run on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        result &= print_device_info(nodemap_tldevice)
        cam.Init()
        
        nodemap = cam.GetNodeMap()
        result &= set_camera_parameters(cam, nodemap, nodemap_tldevice, fps=cfg["capture"]["framerate"],
                                        height=cfg["capture"]["resolution"][1], width=cfg["capture"]["resolution"][0],
                                        offsetx=cfg["capture"]["offset"][0], offsety=cfg["capture"]["offset"][1])

        result &= acquire_images(cam, nodemap, nodemap_tldevice, cfg["data"]["output"])

        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        result = False

    return result

def print_device_info(nodemap):
    """
    Print the device information of the camera from the transport layer.

    Please see NodeMapInfo example for more in-depth
    comments on printing device information from the nodemap.

    :param nodemap: Transport layer device nodemap.
    :type nodemap: INodeMap
    :returns: True if successful, False otherwise.
    :rtype: bool
    """
    print("\n*** DEVICE INFORMATION ***\n")

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(
            nodemap.GetNode("DeviceInformation"))

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(
                node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print("%s: %s" % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(
                                  node_feature) else "Node not readable"))

        else:
            print("Device control information not available.")

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result

def main():
    """
    Run the main program.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration-file", "-cfg", "-i", nargs=1, action="store", dest="config", required=True,
                        help="Configuration JSON file.")
    parser.add_argument("--output", "-o", action="store", dest="output", default="output", required=False,
                        help="Output folder for processed images.")
    args = parser.parse_args()

    inp = args.config[0]
    if os.path.isfile(inp):
        with open(inp, "r") as f:
            cfg = json.load(f)
    else:
        raise IOError("No such file or directory \"{}\"".format(inp))

    global today
    today = datetime.datetime.now()
    hour = today.hour
    capture_hours = cfg["data"]["hours"]
    if hour in capture_hours:
        print("Sunlight hours. Starting capture cycle.\n")
        print("Capture starting at {}:\n".format(today))
    else:
        print("Not enough sunlight at {}. Not starting capture cycle.".format(today))
        sys.exit()

    global OUTPATH
    OUTPATH = args.output
    if not os.path.isdir(OUTPATH):
        os.makedirs(OUTPATH)
        os.chmod(OUTPATH, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    # compute the number of images to capture based on frame rate
    # and capture duration
    fps = cfg["capture"]["framerate"]
    duration = cfg["capture"]["duration"]

    # number of images to grab - note that this is a global variable
    global NUM_IMAGES
    NUM_IMAGES = fps * duration

    # image extenstion - note that this is a global variable
    global EXT
    EXT = cfg["data"]["format"]

    # Since this application saves images in the current folder
    # we must ensure that we have permission to write to this folder.
    # If we do not have permission, fail right away.
    try:
        test_file = open(os.path.join(OUTPATH, "test.txt"), "w+")
    except IOError:
        print("Unable to write to current directory."
              "Please check permissions.")
        # input("Press Enter to exit...")
        return False

    test_file.close()
    os.remove(test_file.name)
    result = True

    system = PySpin.System.GetInstance()
    version = system.GetLibraryVersion()
    print("Library version: %d.%d.%d.%d" % (version.major, version.minor, version.type, version.build))

    cam_list = system.GetCameras()
    num_cameras = cam_list.GetSize()
    print("\nNumber of cameras detected: %d" % num_cameras)

    if num_cameras < 2:
        cam_list.Clear()
        system.ReleaseInstance()
        print("Not enough cameras!")
        input("Done! Press Enter to exit...")
        return False

    threads = []
    for i in range(2):
        cam = cam_list.GetByIndex(i)
        print("\nRunning capture cycle for camera %d..." % i)
        thread = threading.Thread(target=run_single_camera, args=(cam, cfg))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    cam_list.Clear()
    system.ReleaseInstance()

if __name__ == "__main__":
    main()
