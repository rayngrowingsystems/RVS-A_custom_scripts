# Custom Scripts for RAYN Visions System Analytics
Templates and instructions for creating custom scripts for RAYN Vision System Analytics

<!-- TOC -->
* [Custom Scripts for RAYN Visions System Analytics](#custom-scripts-for-rayn-visions-system-analytics)
  * [Introduction](#introduction)
  * [Structure of RVS Analytics scripts](#structure-of-rvs-analytics-scripts)
    * [Analytics UI elements and .config files (json)](#analytics-ui-elements-and-config-files-json)
      * [Config file structure](#config-file-structure)
      * [Available UI elements in the UI dialogues](#available-ui-elements-in-the-ui-dialogues)
      * [Special cases - dynamic UI elements](#special-cases---dynamic-ui-elements)
      * [How to call the input from the UI elements in the script](#how-to-call-the-input-from-the-ui-elements-in-the-script)
    * [Analysis script (python)](#analysis-script-python)
      * [Functions explained: `create_mask()`](#functions-explained-create_mask)
      * [Functions explained: `execute()`](#functions-explained-execute)
      * [Available analyses](#available-analyses)
  * [Step-by-step instructions on how to create your own RVS script](#step-by-step-instructions-on-how-to-create-your-own-rvs-script)
    * [1. Develop an analysis workflow](#1-develop-an-analysis-workflow)
    * [2. Decide which variables in your script you want to expose](#2-decide-which-variables-in-your-script-you-want-to-expose)
    * [3. Prepare folder and files](#3-prepare-folder-and-files)
    * [4. Prepare the config file](#4-prepare-the-config-file)
    * [5. Prepare the mask script (`create_mask()` function)](#5-prepare-the-mask-script-create_mask-function)
    * [6. Prepare analysis script (`execute()` function)](#6-prepare-analysis-script-execute-function)
      * [6.1. Get settings](#61-get-settings)
      * [6.2. Add object analysis](#62-add-object-analysis)
      * [6.3. Process results](#63-process-results)
    * [7. Write a README](#7-write-a-readme)
    * [8. Add the custom script to RVS Analytics](#8-add-the-custom-script-to-rvs-analytics)
  * [Support](#support)
  * [Contributing](#contributing)
<!-- TOC -->

## Introduction
RAYN Vision System (RVS) Analytics is an open-source application for the processing
and analysis of hyper- and multispectral images from multiple sources, including RVS Cameras
online in the same network. It is based on [PlantCV](https://github.com/danforthcenter/plantcv),
an open-source image analysis software package targeted for plant phenotyping.

The application itself does not contain any analysis scripts out of the box*. It is a framework for PlantCV workflows
with a customizable user interface. The scripts can be added through the "Masks" and "Scripts" folders. You can use 
pre-made scripts or create your own. 

Scripts created by the RAYN as well as from the community can be retrieved from the following repositories:
- [RVS-A Mask Scripts (Development)]()
- [RVS-A Analysis Scripts (Development)]()

*The Windows installer of RVS Analytics already contains the analysis scripts and mask scripts from 
the RAYN repositories

## Structure of RVS Analytics scripts
RVS Scripts consist of a python file containing the code workflow accompanied by a .config file (json format) which
defines UI elements. Both files have to be in the same folder and must have the same name. 

### Analytics UI elements and .config files (json)
RVS Analytics allows you to customize the "Masking", "Script Options" and "Chart Options" dialogues. You can add
UI elements and call the respective selected items/values in the mask or analysis script.

#### Config file structure
The .config file is in json format. It contains the configurations for `mask`, `script` and `chart`. Each configuration
section contains an `info` object and `options` containing an array of UI element definitions.

⚠️ NOTE: mask scripts are special cases and only contain the configurations for `mask`.

Each UI element in the `options` array can have different items depending on the type. However, the following
are always required:
- `displayName` - Name displayed in the UI
- `name` - Name used in the code to get the value of the UI element
- `hint` - Currently has no function in the UI, can be used to comment the function of the UI element
- `type` - Defines the UI element type (see [Available UI elements in the UI dialogues](#available-ui-elements-in-the-ui-dialogues))
- `value` - Default value (either float, integer or bool)

Here is an example of the content of a config file for an analysis script. 

```json
{
  "mask":
  {
    "info":
    {
      "version": "1.0.0",
      "template": "MaskScript",
      "description": "Single line description of mask script"
    },
    "options":
    [
      {
        "displayName": "Example wavelength dropdown",
        "name": "wavelength",
        "hint": "Select wavelength",
        "type": "wavelength",
        "value": "0"
      }
    ]
  },
  "script":
  {
    "info":
    {
      "version": "1.0.0",
      "template": "BasicScript",
      "description": "Single line description of analysis script"
    },
    "options": 
    [
      {
        "displayName": "Example threshold slider",
        "name": "example_thresh",
        "hint": "Cutoff threshold for binary image",
        "type": "slider",
        "value": "0.5",
        "minimum": "0",
        "maximum": "1",
        "steps": 250
      }
    ]
  },
  "chart":
  {
    "info": {
      "version": "1.0.0",
      "template": "ChartScript",
      "description": "Allows the selection of parameters to be displayed in the chart"
    },
    "options" : 
    [
      {
        "displayName": "Example check box",
        "name": "example_checkbox",
        "hint": "does something",
        "type": "checkBox",
        "value": "true"
      }
    ]
  }
}
```


#### Available UI elements in the UI dialogues

| type                  | Masking | Script Options  | Chart Options |
|-----------------------|---------|-----------------|---------------|
| checkBox              | ✔️      | ✔️              | ✔️            |
| slider                | ✔️      | ✔️              | ✔️            |
| dropdown              | ✔️      | ✔️              | ✔️            |
| wavelength (dropdown) | ✔️      | ❌               | ❌             |


The wavelength dropdown menu is a special UI element. It is automatically filled with the wavelength bands available
in the hyper/multispectral image. 

Check out the template scripts for usage examples.

#### Special cases - dynamic UI elements
Dropdowns items and slider limits can be set dynamically. For this to work, you have to add the 
`"getValuesFor": IDENTIFIER` (dropdown) or `"getRangesFor": IDENTIFIER` (slider) item to the respective UI element options in the config file and set it to a 
function that is called to get the respective items (dropdown) or slider parameter (slider).

Here is an example of a dropdown menu to select an index. The respective threshold slider is adjusted according to the
selected index.

Content of the .config file
```json
[
  {
    "displayName": "Select Index", 
    "name": "mask_index",
    "hint": "Select Index",
    "type": "dropdown",
    "getValuesFor": "index_list",
    "value": "0"
  },
  {
    "displayName": "Index Threshold",
    "name": "index_thresh",
    "hint": "Cutoff threshold for binary image",
    "type": "slider",
    "getRangesFor": "mask_index"
  }
]
```
Respective functions in the python script file
```python
def dropdown_values(setting, wavelengths):  # fills UI element with values
    if setting == "index_list":  # defines the UI elements this is applied to
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

    if setting == "mask_index":  # defines the UI elements this is applied to
        index_functions = rayn_utils.get_index_functions()
        minimum = index_functions[name][2]
        maximum = index_functions[name][3]
        value = (maximum - minimum) / 2 + minimum
        steps = 500
        print(f"index settings: min {minimum}, max {maximum}, steps {steps}, value {value}")

    return minimum, maximum, steps, value
```



#### How to call the input from the UI elements in the script
The input received thought the added UI elements is saved and handed over to the mask and analysis script via a nested 
(python) settings dictionary. The dictionary object is named `settings` and can be accessed by all functions in the 
python file.

The path to the respective options is the following:
- Mask options: `mask_options = settings["experimentSettings"]["analysis"]["maskOptions"]`
- Script options: `script_options = settings["experimentSettings"]["scriptOptions"]["general"]`
- Chart options: `chart_options = settings["experimentSettings"]["analysis"]["chartOptions"]`

The values of the UI elements can then be called with the `name` set in the config file.
```json
{
  "displayName": "Example custom dropdown",
  "name": "custom_dropdown",
  "type": "dropdown",
  "displayNames": ["Example 1", "Example 2", "Example 3", "Example 4", "Example 5"],
  "names": ["example_1", "example_2", "example_3", "example_4", "example_5"],
  "value": "0"
}
```
In this case the selected option in the dropdown can be retrieved via
`value_custom_dropdown = mask_options["custom_dropdown"]`

In dropdown menus, `displayNames` lists all the items in the dropdown menu (as they are displayed). `names` contains the 
respective value that is returned when a corresponding item was selected (e.g. in this case, if "Example 5" was selected, 
`value_custom_dropdow` is `example_4`).

### Analysis script (python)

The analysis script is written in python. It only contains functions that are called by RVS Analytics. The main
functions are:
- `create_mask()` - processes the hyper/multispectral image file and creates a mask
- `execute()` - main function running the analysis workflow

The following parameters are automatically provided by RVS Analytics and can be accessed inside the functions:
- `feedback_queue` - internal processing queue
- `script_name` - name of the used script (relevant for the processing queue)
- `settings` - python dictionary containing values of the UI elements 
(see [How to call the input from the UI elements in the script](#how-to-call-the-input-from-the-ui-elements-in-the-script))
- `mask_file_name` - name of the used mask script if not default

Please see the template scripts and function documentation for more information. 

⚠️ NOTE: 
- the mask script is a special case - it only contains `create_mask()` as main function.
- currently there are utility functions in the scripts (e.g. `prepare_spectral_data()` or `process_rois()`)
which might be (re)moved to the rayn_utils python module at some point

#### Functions explained: `create_mask()`
Default mask workflow (if inside an analysis script) or additional mask script. 
Selection of mask scripts is possible in the UI.
- Input: settings dictionary
- Output: spectral array (undistorted and/or normalized), mask (binary 2d-array)

There are numerous ways to create a binary mask to segment objects (plants). Please refer to [this guide in the PlantCV 
documentation](https://plantcv.readthedocs.io/en/stable/analysis_approach/#object-segmentation-approaches). 

#### Functions explained: `execute()`
Contains the analysis workflow. It will be applied in a loop on all files in a folder, single images or incoming images
(depending on the respective source set)
- Input: feedback queue reference, script name, settings dictionary and mask function
- Output: results are sent to the feedback queue and collected by RVS Analytics

The analysis workflow can be separated into the following consecutive steps:
1. Load image and create mask (both done within `create_mask()`)
2. Process ROIs and analyze objects inside
3. Extract relevant results and send them to the feedback queue

⚠️ NOTE: The value that should be plotted in the chart tab has to be added to the results dictionary as `"plot_value"` 
for each ROI. Respective display names (graph title and y-axis label) can be returned with the function 
`get_display_name_for_chart`.

#### Available analyses
We recommend to use the object analysis methods available in PlantCV to analyze your samples, however, you are not
limited to them. Here we will briefly describe the analysis options available in PlantCV Please refer to documentation
[Object Analysis in PlantCV](https://plantcv.readthedocs.io/en/stable/analysis_approach/#2-object-analysis-in-plantcv)
for more information. 

There are currently five main categories of object analysis in PlantCV.
- Object shape parameters:
  - analyze.size
  - analyze.bound_horizontal
  - analyze.bound_vertical 
- Object color or other signal intensity values
  - analyze.color
  - analyze.grayscale
  - analyze.thermal
  - analyze.yii
- Object classification
  - naive-bayesian multiclass mode
- Object hyperspectral parameters:
  - analyze.spectral_reflectance
  - analyze.spectral_index functions. 
- Morphological parameters (check "Morphology Functions" in the [PlantCV documentation](https://plantcv.readthedocs.io/en/stable/))
  - stem height
  - leaf length
  - leaf angle
  - and more ...

## Step-by-step instructions on how to create your own RVS script

Since RVS Analytics is a wrapper for PlantCV functions, you can refer to the 
[PlantCV documentation](https://plantcv.readthedocs.io/en/stable/) or 
[Approaches to Image Analysis with PlantCV](https://plantcv.readthedocs.io/en/stable/analysis_approach/) for background
information and instructions.

The following step-by-step instructions focuses on the essentials for creating a functional mask or analysis script
for RVS Analytics.

### 1. Develop an analysis workflow
We recommend using interactive notebooks (jupyter) to develop and image processing workflow. You can find great 
[Tutorials](https://plantcv.readthedocs.io/en/stable/#tutorials) and instructions
on [Workflow Development](https://plantcv.readthedocs.io/en/stable/analysis_approach/#developing-image-processing-workflows-workflow-development)
in the PlantCV documentation.

The most important part of an analysis script is the object segmentation (masking). There are different approaches to
object segmentation. Currently, mask scripts provided by RAYN only uses binary thresholding on grayscale images (index values
or single wavelength images) to create a binary mask. However, there are a lot more approaches for object segmentation
e.g. automatic thresholding, background subtraction or machine learning. 

### 2. Decide which variables in your script you want to expose
The analysis workflow usually contains variables that might need to be adjusted depending on the image set that is
analyzed. Depending on variable type you need to choose the UI elements you want to use. 

The mask scripts provided by RAYN usually expose the threshold through a slider element. Additional options such as
pixel dilation can be (de)activate through a checkbox. It is also possible to fill dropdown menus e.g. with all the 
indices that can be analyzed. All available UI elements are listed here: 
[Available UI elements in the UI dialogues](#available-ui-elements-in-the-ui-dialogues). See the template scripts and 
existing RVS scripts for examples.

### 3. Prepare folder and files
Copy the full "template_analysis_script" or "template_mask_script" folder from this repository. Rename the folder, 
script file (.py) and the . config file with the script name you chose (apart from the extension, 
names should be identical). The folder should contain three files:
- SCRIPT.py
- SCRIPT.config
- README

### 4. Prepare the config file
See [Analytics UI elements and .config files (json)](#analytics-ui-elements-and-config-files-json).

Change the config file and add UI elements based on the previous step: 
[2. Decide which variables in your script you want to expose](#2-decide-which-variables-in-your-script-you-want-to-expose)

### 5. Prepare the mask script (`create_mask()` function)
See [Functions explained: `create_mask()`](#functions-explained-create_mask).

Get all the values from the UI elements in the "Masking" dialogue through the mask options in the settings dictionary
(see template scripts). Add the steps (code) to create a binary mask of the workflow you developed (replace the code
between BEGIN and END EXAMPLE MASK ACTION in the template scripts). 

### 6. Prepare analysis script (`execute()` function)
See [Functions explained: `execute()`](#functions-explained-execute) and [Available analyses](#available-analyses).

⚠️ Skip this step if you only want to create a mask script.

#### 6.1. Get settings
Get all the values from the UI elements in the "Script Options" and "Chart Options" through the script and chart options
in the settings dictionary. The ROIs are selected in the RVS Analytics UI and can be retrieved from the settings dictionary 
as well (`settings["experimentSettings"]["roiInfo"]["roiItems"]`).

#### 6.2. Add object analysis
Add the analysis steps (code) of your workflow (alter or replace the code below "EXAMPLE analyzing objects" in the 
template script). 

#### 6.3. Process results
The results of the image analysis are signaled back to queue and collected by RVS Analytics. However, currently the 
results have to be processed and put into a result dictionary. See the template script for an example.

NOTE: If you want a parameter to be displayed in the "Chart", you need to add the value as `"plot_value"` to the results
list. Chart title and y-axis label can be set with the `get_display_name_for_chart()` function.

### 7. Write a README
It is a good practice to write a README describing the functionality of your script. See the template README and 
existing RVS Analytics scripts for examples.

### 8. Add the custom script to RVS Analytics
Copy the folder with the three files to RVS Analytics. Depending on its type, add it either to the "Masks" or "Scripts"
folder. The directories are scanned for scripts - organizing them in subfolders are allowed as well.

## Support
If you experience any problems or have feedback on the analysis scripts, please add an issue to this repository or 
contact [Alexander Kutschera](mailto:alexander.kutschera@rayngrowingsystems.com).

## Contributing
We welcome contributions. If it's fixing bugs, adding functionality to existing scripts
or adding entirely new scipts.

Please add any suggestions/issues/bugs as issues in the [RVS Analytics custom scripts repository]().

