import os
import sys
import subprocess
import stat
import time

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


    
def set_camera_parameters(cam, nodemap, nodemap_tldevice, fps=5, height=1080,
                          width=1920, offsetx=80, offsety=236):
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

        # allow to set frqme rate
        node_acquisition_fps_auto = PySpin.CEnumerationPtr(
                    nodemap.GetNode("AcquisitionFrameRateAuto"))
        node_acquisition_fps_auto.SetIntValue(0)

        # get the current frame rate
        i = cam.AcquisitionFrameRate.GetValue()
        print("Current frame rate: %d " % i)
        # set the new frame rate
        cam.AcquisitionFrameRate.SetValue(fps)
        i = cam.AcquisitionFrameRate()
        print("Frame rate set to: %d " % i)

        # *** Image size ***

        # Set image height and width to maximum values
        max_height = cam.Height.GetMax()
        max_width = cam.Width.GetMax()
        cam.Height.SetValue(max_height)
        cam.Width.SetValue(max_width)


        # set the current exposure
        cam.ExposureAuto.SetValue(2)
        i = cam.ExposureAuto.GetValue()
        print("Image exposure set to: %d " % i)
        # Set auto exposure mode to 'Once'
        #node_acquisition_exposure_auto = PySpin.CEnumerationPtr(
                    #nodemap.GetNode("ExposureAuto"))
        #node_acquisition_exposure_auto.SetIntValue(2)  # Set to 'Once'

        print("Image exposure set to: %d " % i)
        # *** Image offset ***

        # get the current image offsetx
        i = cam.OffsetX.GetValue()
        print("Current OffsetX : %d " % i)
        # set the current image offsetX
        cam.OffsetX.SetValue(offsetx)
        i = cam.OffsetX.GetValue()
        print("Image OffsetX set to: %d " % i)

        # get the current image offsetY
        i = cam.OffsetY.GetValue()
        print("Current OffsetX : %d " % i)
        # set the current image offsetY
        cam.OffsetY.SetValue(offsety)
        i = cam.OffsetY.GetValue()
        print("Image OffsetX set to: %d " % i)
        
       
        

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result


def acquire_images(cam, nodemap, nodemap_tldevice):
    """
    Acquires and saves N images from a device.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print("\n*** IMAGE ACQUISITION ***\n")
    try:
        result = True

        # Set acquisition mode to continuous
       
        # In order to access the node entries, they have to be casted to a
        # pointer type (CEnumerationPtr here)
        node_acquisition_mode = PySpin.CEnumerationPtr(
            nodemap.GetNode("AcquisitionMode"))
        if not PySpin.IsAvailable(node_acquisition_mode) \
                or not PySpin.IsWritable(node_acquisition_mode):
            print(
                "Unable to set acquisition mode to continuous"
                "(enum retrieval)."
                "Aborting...")
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous =  \
            node_acquisition_mode.GetEntryByName("Continuous")
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) \
                or not PySpin.IsReadable(node_acquisition_mode_continuous):
            print(
                "Unable to set acquisition mode to continuous"
                "(entry retrieval). Aborting...")
            return False

        # Retrieve integer value from entry node
        acquisition_mode_continuous =  \
            node_acquisition_mode_continuous.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        print("Acquisition mode set to continuous...")

        # Begin acquiring images
       
        # Image acquisition must be ended when no more images are needed.
        cam.BeginAcquisition()

        print("\n *** Acquiring images ***\n")
        
        # Retrieve device serial number for filename
        #
        # *** NOTES ***
        # The device serial number is retrieved in order to keep cameras from
        # overwriting one another. Grabbing image IDs could also accomplish
        # this.
        device_serial_number = ""
        node_device_serial_number = PySpin.CStringPtr(
            nodemap_tldevice.GetNode("DeviceSerialNumber"))
        if PySpin.IsAvailable(node_device_serial_number) and \
                PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
            # print("\nDevice serial number retrieved as %s...\n" %
            #  device_serial_number)
        processor = PySpin.ImageProcessor()

        # Set default image processor color processing method
        #
        # *** NOTES ***
        # By default, if no specific color processing algorithm is set, the image
        # processor will default to NEAREST_NEIGHBOR method.
        processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)
        # Retrieve, convert, and save images
              
       
       
        for i in range(NUM_IMAGES):
            try:

                # Retrieve next received image
                #
                # *** NOTES ***
                # Capturing an image houses images on the camera buffer.
                # Trying to capture an image that does not exist will hang the
                # camera.
                #
                # *** LATER ***
                # Once an image from the buffer is saved and/or no longer
                # needed, the image must be released in order to keep the
                # buffer from filling up.
                image_result = cam.GetNextImage()

                # Ensure image completion
                #
                # *** NOTES ***
                # Images can easily be checked for completion. This should be
                # done whenever a complete image is expected or required.
                # Further, check image status for a little more insight into
                # why an image is incomplete.
                if image_result.IsIncomplete():
                    print("Image incomplete with image status %d ..." %
                          image_result.GetImageStatus())

                else:

                    # Print image information; height and width recorded in
                    # pixels
                    #
                    # *** NOTES ***
                    # Images have quite a bit of available metadata including
                    # things such as CRC, image status, and offset values, to
                    # name a few.
                    width = image_result.GetWidth()
                    height = image_result.GetHeight()
                    # print("Grabbed Image %d, width = %d, height = %d" %
                    #       (i, width, height))

                    # Convert image to RGB8
                    #
                    # *** NOTES ***
                    # Images can be converted between pixel formats by using
                    # the appropriate enumeration value. Unlike the original
                    # image, the converted one does not need to be released as
                    # it does not affect the camera buffer.
                    #
                    # When converting images, color processing algorithm is an
                    # optional parameter.
                    image_converted = processor.Convert(image_result, PySpin.PixelFormat_RGB8)

                    # Create a unique filename
                    now = today.strftime("%Y%m%d_%H%M%S")
                    if device_serial_number:
                        filename = "{}-{}-{}.{}".format(device_serial_number,
                                                        now, str(i).zfill(6),
                                                        EXT)
                    else:  # if serial number is empty
                        filename = "{}-{}.{}".format(now, str(i).zfill(6),
                                                     EXT)

                    # Save image
                    #
                    # *** NOTES ***
                    # The standard practice of the examples is to use device
                    # serial numbers to keep images of one device from
                    # overwriting those of another.
                    image_converted.Save(os.path.join(OUTPATH, filename))
                    print("Image saved at %s" % filename)

                    #  Release image
                    #
                    #  *** NOTES ***
                    # Images retrieved directly from the camera  (i.e.
                    # non-converted images) need to be released in order
                    # to keep from filling the buffer.
                    image_result.Release()
                    # print("")

            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
                return False

        # End acquisition
        #
        # *** NOTES ***
        # Ending acquisition appropriately helps ensure that devices clean up
        # properly and do not need to be power-cycled to maintain integrity.
        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

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


def run_single_camera(cam, cfg):
    """
    Run the camera.

    This function acts as the body of the example; please see NodeMapInfo
    example for more in-depth comments on setting up cameras.

    :param cam: Camera to run on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Retrieve TL device nodemap and print device information
        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        result &= print_device_info(nodemap_tldevice)

        # Initialize camera
        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

        # Set camera parameters
        result &= set_camera_parameters(cam, nodemap, nodemap_tldevice,
                                        fps=cfg["capture"]["framerate"],
                                        height=cfg["capture"]["resolution"][1],
                                        width=cfg["capture"]["resolution"][0],
                                        offsetx=cfg["capture"]["offset"][0],
                                        offsety=cfg["capture"]["offset"][1])

        # Acquire images
        result &= acquire_images(cam, nodemap, nodemap_tldevice)

        # Deinitialize camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        result = False

    return result


def main():
    """
    Run the main program.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    # Argument parser
    parser = argparse.ArgumentParser()

    # input configuration file
    parser.add_argument("--configuration-file", "-cfg", "-i",
                        nargs=1,
                        action="store",
                        dest="config",
                        required=True,
                        help="Configuration JSON file.",)
    # output destination
    parser.add_argument("--output", "-o",
                        action="store",
                        dest="output",
                        default="output",
                        required=False,
                        help="Output folder for processed images.")

    args = parser.parse_args()

    # verify if the input file exists,
    # if it does, then read it
    inp = args.config[0]
    if os.path.isfile(inp):
        with open(inp, "r") as f:
            cfg = json.load(f)
    else:
        raise IOError("No such file or directory \"{}\"".format(inp))

    # get the date
    global today
    today = datetime.datetime.now()

    # check if the current hour is in capture hours
    hour = today.hour
    capture_hours = cfg["data"]["hours"]
    if hour in capture_hours:
        print("Sunlight hours. Starting capture cycle.\n")
        print("Capture starting at {}:\n".format(today))
    else:
        print("Not enough sunlight at {}. Not starting capture cycle.".format(
            today))
        sys.exit()

    # read the output path
    main_path = cfg["data"]["output"]

    # current cycle output path - note that this is a global variable
    global OUTPATH
    OUTPATH = args.output
    if not os.path.isdir(OUTPATH):
        os.makedirs(OUTPATH)
        os.chmod(OUTPATH, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    result = True

    # Retrieve singleton reference to the system object
    system = PySpin.System.GetInstance()

    # Get the current library version
    version = system.GetLibraryVersion()
    print("Library version: %d.%d.%d.%d" %
          (version.major, version.minor, version.type, version.build))

    # Retrieve the list of cameras from the system
    cam_list = system.GetCameras()

    num_cameras = cam_list.GetSize()

    print("\nNumber of cameras detected: %d" % num_cameras)

    # Finish if there are no cameras
    if num_cameras < 2:  # Require at least two cameras

        # Clear camera list before releasing the system
        cam_list.Clear()

        # Release the system instance
        system.ReleaseInstance()

        print("Not enough cameras!")
        input("Done! Press Enter to exit...")
        return False

    # Run the example on each camera
    for i in range(2):  # Loop through the first two cameras

        cam = cam_list.GetByIndex(i)

        print("\nRunning capture cycle for camera %d..." % i)

        result &= run_single_camera(cam, cfg)
        print("\nCamera %d example complete... \n" % i)
        print("My work is done!")

        # Release reference to the camera
        del cam

    # Clear the camera list before releasing the system
    cam_list.Clear()

    # Release the system instance
    system.ReleaseInstance()

    # input("Done! Press Enter to exit...")
    return result


if __name__ == "__main__":
    # Call the main program
    main()
                        
    args = parser.parse_args()

    # call the main program
    main()
