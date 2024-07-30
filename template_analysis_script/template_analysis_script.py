import os
import numpy as np
import warnings
from plantcv import plantcv as pcv
import sys
import importlib
import rayn_utils


# Default mask workflow. Selection of other mask scripts is possible in the UI.
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


# Analysis workflow
def execute(feedback_queue, script_name, settings, mask_file_name):
    """
    :param feedback_queue: queue of feedback messages
    :param script_name: name of the analysis script (required for feedback queue
    :param settings: settings dictionary
    :param mask_file_name: name of the mask script (required for feedback queue
    """
    print("Execute:", script_name, settings)
    # Load parameters from the settings dict (don't change this)
    out_folder = settings["outputFolder"]  # target folder
    roi_items = settings["experimentSettings"]["roiInfo"]["roiItems"]  # ROI coordinates

    # extract script setting, available options are defined in the .conf file (don't change this)
    script_options = settings["experimentSettings"]["scriptOptions"]["general"]
    chart_options = settings["experimentSettings"]["analysis"]["chartOptions"]

    # script specific settings (edit this)
    value_custom_dropdown_script = script_options["custom_dropdown_script"]     # edit/remove this
    value_dynamic_dropdown_script = script_options["dynamic_dropdown_script"]   # edit/remove this
    value_example_thresh_script = script_options["example_thresh_script"]       # edit/remove this
    value_example_checkbox_script = script_options["example_checkbox_script"]   # edit/remove this

    # script specific settings for charting (options are defined in the .config file) (edit this)
    plot_selection = chart_options["plot_selection"]  # edit/remove this

    # plantCV settings
    pcv.params.debug = None

    # determine mask script based on the chosen option (don't change this)
    if mask_file_name != "":  # external mask script (= mask function defined in another file)
        mask_path, mask_file = os.path.split(mask_file_name)
        print("External mask file used: ", mask_file_name)

        sys.path.append(mask_path)
        mask_script = importlib.import_module(mask_file.replace(".py", ""))
        create_function = mask_script.create_mask

    else:  # default/internal mask script is used (= mask function defined in this script)
        print("Internal mask used")

        create_function = create_mask

    # BEGIN WORKFLOW
    print("Starting workflow")

    # retrieving preprocessed data cube and mask (don't change this)
    spectral_array, mask = create_mask(settings, mask_preview=False)

    # extract image name (don't change this)
    filename = spectral_array.filename
    image_name = os.path.split(filename)[-1]
    image_name = os.path.splitext(image_name)[0]

    # signal which file is processed (don't change this)
    feedback_queue.put([script_name, 'Processing: ' + spectral_array.filename])

    # copy unaltered pseudo rgb image for plotting results/debug information on it later (optional)
    img_plant_labelled = np.copy(spectral_array.pseudo_rgb)
    img_roi_labelled = np.copy(spectral_array.pseudo_rgb)

    # process ROI items forwarded from the UI  (don't change this)
    rois = process_rois(roi_items, img_roi_labelled)

    # identify objects in the ROIs  (edit this, if required)
    labeled_objects, n_obj = pcv.create_labels(mask=mask, rois=rois, roi_type="partial")

    # EXAMPLE analyzing objects
    if value_example_checkbox_script:  # analyze spectral index selected via a dynamic dropdown
        index_functions = rayn_utils.get_index_functions()
        index_array = index_functions[value_dynamic_dropdown_script][1](spectral_array, 10)
        pcv.analyze.spectral_index(index_img=index_array,
                                   labeled_mask=labeled_objects,
                                   n_labels=n_obj,
                                   label="plant")

    if value_custom_dropdown_script == "shape":  # shape spectral index
        img_plant_labelled = pcv.analyze.size(img=img_plant_labelled,
                                              labeled_mask=labeled_objects,
                                              n_labels=n_obj,
                                              label="plant")

    # return preview image
    image_file_name = os.path.normpath(out_folder + "/ProcessedImages/" + image_name + ".png")
    path, file_name = os.path.split(image_file_name)

    if not os.path.exists(path):
        os.makedirs(path)
        print("created folder " + path)

    print("Writing image to " + image_file_name)

    pcv.print_image(img=img_plant_labelled, filename=image_file_name)

    # Use feedbackQueue.put to send feedback to the main application
    print("writing info to queue")
    feedback_queue.put([script_name, 'preview', image_file_name])

    print("Workflow done")

    # END WORKFLOW

    # START PROCESSING RESULTS
    # You have to edit most of this code to output the results of your analyses
    # TODO: This is currently very limited and inflexible. Needs to change!
    #       Adding meta data to the results will be possible in a later version of PlantCV
    #       which will in turn make the result processing done here obsolete

    results = pcv.outputs.observations  # get the results

    results_dict = {}  # prepare empty dict to store filtered results in.
    results_list = []

    index_key = "index_" + value_dynamic_dropdown_script

    if plot_selection == "plot_index":
        selected_key = "mean_" + index_key
    else:
        selected_key = plot_selection

    for i in range(1, n_obj + 1):  # loop through analyzed objects (plants)
        if f"plant_{i}" in results:
            roi_results = results[f"plant_{i}"]

            # this part has to be adjusted to the analyses that are performed.
            # below you can find example results from analyze.spectral_index and analyze.size called in the workflow
            # we recommend to look at the full results output (e.g. with print(results)) and select the respective
            # parameters you are interested in from there.

            results_list.append({"roi": i,                                              # required parameter
                                "area": roi_results["area"]["value"],
                                "width": roi_results["width"]["value"],
                                "height": roi_results["height"]["value"],
                                "perimeter": roi_results["perimeter"]["value"],
                                "index": value_dynamic_dropdown_script,
                                "mean": roi_results["mean_" + index_key]["value"],
                                "median": roi_results["med_" + index_key]["value"],
                                "std": roi_results["std_" + index_key]["value"],
                                "plot_value": roi_results[selected_key]["value"]})      # required parameter

            # If you want to skip this step and do it your way, you can do the following:
            """
            results_list.append({"roi": i,
                                "area": None,
                                "width": None,
                                "height": None,
                                "perimeter": None,
                                "index": None,
                                "mean": None,
                                "median": None,
                                "std": None,
                                "plot_value": None})
            
            
            """

    results_dict["rois"] = results_list

    # signal results
    signal_dict = {"imageFileName": image_file_name, "dict": results_dict}
    feedback_queue.put([script_name, 'results', signal_dict])


def process_rois(roi_items, rgb_image):  # get the rois from individual coordinates
    # creating empty ROI object
    rois = pcv.Objects(contours=[], hierarchy=[])

    for roi_type, roi_x, roi_y, roi_width, roi_height in roi_items:
        print("RoiItem:", roi_type, roi_x, roi_y, roi_width, roi_height)

        if roi_type == "Circle":
            roi_radius = int(roi_width / 2)
            # create a single circular roi
            roi = pcv.roi.circle(x=roi_x, y=roi_y, r=roi_radius, img=rgb_image)
        elif roi_type == "Rectangle":
            # create a single rectangle roi
            print("calculated x/y", roi_x - roi_width / 2, roi_y - roi_height / 2)
            roi = pcv.roi.rectangle(x=roi_x - roi_width / 2, y=roi_y - roi_height / 2,
                                    h=roi_height, w=roi_width, img=rgb_image)

        else:
            warnings.warn("Roi type is neither circle or rectangle")
            break

        # append the roi contour and hierarchy to the object collecting all the rois
        rois.append(roi.contours, roi.hierarchy)

    return rois


def prepare_spectral_data(settings):
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


def create_mask_preview(mask, settings, create_preview=True):
    if create_preview:
        out_image = settings["outputImage"]
        image_file_name = os.path.normpath(out_image)
        print("Writing image to " + image_file_name)
        pcv.print_image(img=mask, filename=image_file_name)


def dropdown_values(setting, wavelengths):  # fills the index dropdown (see .config file)

    if setting == "index_list":  # defines the UI element this is applied to
        index_dict_dd = rayn_utils.get_index_functions()
        name_list = list(index_dict_dd)
        display_name_list = [item[0] for item in index_dict_dd.values()]

        return display_name_list, name_list

    else:
        return


def range_values(setting, name, index):  # sets the slider ranges (see .config file)
    print("range_values", setting, name, index)

    # set default values
    value = 0.5
    minimum = 0
    maximum = 1
    steps = 10

    if setting == "mask_index":  # defines the UI element this is applied to
        index_functions = rayn_utils.get_index_functions()
        minimum = index_functions[name][2]
        maximum = index_functions[name][3]
        value = (maximum - minimum) / 2 + minimum
        steps = 500
        print(f"index settings: min {minimum}, max {maximum}, steps {steps}, value {value}")

    return minimum, maximum, steps, value


def get_display_name_for_chart(settings):
    # load settings
    plot_selection = settings["experimentSettings"]["analysis"]["chartOptions"]["plot_selection"]
    script_options = settings["experimentSettings"]["scriptOptions"]["general"]
    value_dynamic_dropdown_script = script_options["dynamic_dropdown_script"]

    index_key = "index_" + value_dynamic_dropdown_script

    if plot_selection == "plot_index":
        selected_key = "mean_" + index_key
    else:
        selected_key = plot_selection

    if plot_selection == "plot_index":
        index_dict_dd = rayn_utils.get_index_functions()
        full_index_name = index_dict_dd[selected_key][0]
        title = full_index_name
        y_label = "relative index value"

    else:
        title = f"Leaf {plot_selection}"
        y_label = f"Leaf {plot_selection} [px]"

    return title, y_label
