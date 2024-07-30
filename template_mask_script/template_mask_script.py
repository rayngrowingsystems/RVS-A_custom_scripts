import os
import numpy as np
import warnings
from plantcv import plantcv as pcv
import rayn_utils


def create_mask(settings, mask_preview=True):
    """
    :param settings: settings dictionary
    :param mask_preview: produce preview image of the mask for display in the mask dialog of the UI
    :return: spectral array (undistorted and/or normalized), mask (binary image)
    """
    # extract masking setting, available options are defined in the .conf file (don't change this)
    mask_options = settings["experimentSettings"]["analysis"]["maskOptions"]

    # extract masking setting, available options are defined in the .conf file (edit this)
    value_wavelength_mask = mask_options["wavelength_mask"]                         # edit/remove this
    value_custom_dropdown_mask = mask_options["custom_dropdown_mask"]               # edit/remove this
    value_dynamic_dropdown_mask = mask_options["dynamic_dropdown_mask"]             # edit/remove this
    value_example_thresh_mask = mask_options["example_thresh_mask"]                 # edit/remove this
    value_example_checkbox_mask = mask_options["example_checkbox_mask"]             # edit/remove this

    spectral_array = prepare_spectral_data(settings)

    # BEGIN EXAMPLE MASK ACTION - replace or edit
    # get data from selected wavelength band
    if (value_wavelength_mask != "None") and (value_wavelength_mask != ""):
        selected_layer = spectral_array.array_data[:, :, int(spectral_array.wavelength_dict[int(value_wavelength_mask)])]
    else:
        selected_layer = spectral_array.array_data[:, :, 0]
        warnings.warn("No wavelength for mask selected. Defaulting to first in list")

    # create binary mask from layer using an adjustable threshold
    binary_img = pcv.threshold.binary(gray_img=selected_layer, threshold=value_example_thresh_mask)

    # END EXAMPLE MASK ACTION

    # creates mask preview image
    create_mask_preview(binary_img, settings, mask_preview)  # Don't change this

    return spectral_array, binary_img


def create_mask_preview(mask, settings, create_preview=True):
    """
    Helper function to create preview image of the mask for display in the mask dialog of the UI
    :param mask: binary mask
    :param settings: settings dictionary
    :param create_preview: if False, nothing is done
    :return:
    """
    if create_preview:
        out_image = settings["outputImage"]
        image_file_name = os.path.normpath(out_image)
        print("Writing image to " + image_file_name)
        pcv.print_image(img=mask, filename=image_file_name)


def prepare_spectral_data(settings):
    """
    Helper function that loads and prepares the data of the hyper- or multispectral image
    :param settings: settings dictionary
    :return: spectral data (PlantCV object)
    """
    # file and folder
    img_file = settings["inputImage"]
    # undistort and normalize
    image_options = settings["experimentSettings"]["imageOptions"]

    lens_angle = image_options["lensAngle"]
    dark_normalize = image_options["normalize"]

    # check if a .hdr file name was provided and set img_file to the binary location
    if os.path.splitext(img_file)[1] == ".hdr":
        img_file = os.path.splitext(img_file)[0]

    else:
        warnings.warn("No header file provided. Processing not possible.")
        return

    # begin masking workflow
    spectral_data = pcv.readimage(filename=img_file, mode='envi')
    spectral_data.array_data = spectral_data.array_data.astype("float32")  # required for further calculations
    if spectral_data.d_type == np.uint8:  # only convert if data seems to be uint8
        spectral_data.array_data = spectral_data.array_data / 255  # convert 0-255 (orig.) to 0-1 range

    # normalize the image cube
    if dark_normalize:
        spectral_data.array_data = rayn_utils.dark_normalize_array_data(spectral_data)

    # undistort the image cube
    if lens_angle != 0:  # only undistort if angle is selected
        cam_calibration_file = f"calibration_data/{lens_angle}_calibration_data.yml"  # select the data set
        mtx, dist = rayn_utils.load_coefficients(cam_calibration_file)  # depending on the lens angle
        spectral_data.array_data = rayn_utils.undistort_data_cube(spectral_data.array_data, mtx, dist)
        spectral_data.pseudo_rgb = rayn_utils.undistort_data_cube(spectral_data.pseudo_rgb, mtx, dist)

    return spectral_data


def dropdown_values(setting, wavelengths):
    """
    Helper function that sets the values of dynamic dropdown menus
    :param setting: settings dictionary
    :param wavelengths: wavelengths list
    :return: list of display names and variable names for the respective dropdown
    """

    if setting == "value_dynamic_dropdown_mask":  # defines the UI element this is applied to
        # Example: List all available indices in a dropdown
        index_dict_dd = rayn_utils.get_index_functions()
        name_list = list(index_dict_dd)
        display_name_list = [item[0] for item in index_dict_dd.values()]

        return display_name_list, name_list

    else:
        return


def range_values(setting, name, index):
    """
    Helper function that sets the values of dynamic sliders. Mainly used for adjusting slider min/max values for
    spectral index thresholds
    in the masking in
    :param setting: settings dictionary
    :param name:
    :param index:
    :return:
    """
    print("range_values", setting, name, index)

    # set default values
    value = 0.5
    minimum = 0
    maximum = 1
    steps = 10

    if setting == "mask_index":  # defines the UI element this is applied to
        # Example: Loading the min/max slider limits for each available index
        index_functions = rayn_utils.get_index_functions()
        minimum = index_functions[name][2]
        maximum = index_functions[name][3]
        value = (maximum - minimum) / 2 + minimum
        steps = 500
        print(f"index settings: min {minimum}, max {maximum}, steps {steps}, value {value}")

    return minimum, maximum, steps, value