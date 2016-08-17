from nipype import Workflow, IdentityInterface, Node, Function
from nipype_interfaces import PredictEdgeProbability, CollectFeatureFiles, CreateReferenceImage
from nipype.interfaces.semtools import BRAINSResample
from nipype.interfaces.freesurfer import MRIsConvert
from ..workflow import LOGISMOSB, read_json_config
import os


def read_machine_learning_config():
    return read_json_config(os.path.join("maclearn", "logismosb_maclearn_config.json"))


def create_machine_learning_workflow(name="CreateEdgeProbabilityMap", edge_name="gm", resample=True, plugin_args=None):
    workflow = Workflow(name)
    input_spec = Node(IdentityInterface(["rho", "phi", "theta", "posteriors", "t1_file", "acpc_transform",
                                         "classifier_file"]), name="input_spec")

    predict_edge_probability = Node(PredictEdgeProbability(), name="PredictEdgeProbability")
    predict_edge_probability.inputs.out_file = "{0}_edge_probability_map.nii.gz".format(edge_name)
    if plugin_args:
        predict_edge_probability.plugin_args = plugin_args
    workflow.connect([(input_spec, predict_edge_probability, [("t1_file", "t1_file"),
                                                              ("classifier_file", "classifier_file")])])

    if resample:
        collect_features = Node(CollectFeatureFiles(), name="CollectFeatureFiles")
        collect_features.inputs.inverse_transform = True
        workflow.connect([(input_spec, collect_features, [("rho", "rho"),
                                                          ("phi", "phi"),
                                                          ("theta", "theta"),
                                                          ("posteriors", "posterior_files"),
                                                          ("t1_file", "reference_file"),
                                                          ("acpc_transform", "transform_file")])])

        workflow.connect([(collect_features, predict_edge_probability, [("feature_files", "additional_files")])])
    else:
        print("workflow not yet created")
        # TODO: create workflow that does not resample the input images
        return

    output_spec = Node(IdentityInterface(["probability_map"]), name="output_spec")
    workflow.connect(predict_edge_probability, "out_file", output_spec, "probability_map")

    return workflow


def set_inputs(node, input_dict):
    for key in input_dict:
        node.set_input(key, input_dict[key])
    return node


def create_logismosb_node(name="LOGISMOSB"):
    node = Node(LOGISMOSB(), name=name)
    config = read_machine_learning_config()
    return set_inputs(node, config)


def create_workflow_to_resample_baw_files(name="ResampleBAWOutputs"):
    workflow = Workflow(name)
    inputs_to_resample = ["t1_file", "t2_file", "hncma_file", "abc_file"]
    other_inputs = ["reference_file", "acpc_transform"]
    label_maps = ["hncma_file", "abc_file"]
    input_spec = Node(IdentityInterface(inputs_to_resample + other_inputs), name="input_spec")
    output_spec = Node(IdentityInterface(inputs_to_resample), name="output_spec")
    for input in inputs_to_resample:
        node = Node(BRAINSResample(), "Resample_{0}".format(input))
        node.inputs.pixelType = "short"
        node.inputs.inverseTransform = True
        node.inputs.outputVolume = input + ".nii.gz"
        if input in label_maps:
            node.inputs.interpolationMode = "NearestNeighbor"
        workflow.connect([(input_spec, node, [("reference_file", "referenceVolume"),
                                              ("acpc_transform", "warpTransform"),
                                              ("{0}".format(input), "inputVolume")]),
                          (node, output_spec, [("outputVolume", "{0}".format(input))])])
    return workflow


def create_identity_interface_node(inputs, name):
    return Node(IdentityInterface(inputs), name=name)


def create_workflow_to_mask_white_matter(name):
    from ..freesurfer_utils import SurfaceMask, create_ones_image
    from nipype.interfaces.freesurfer import MRIConvert

    workflow = Workflow(name)

    input_spec = create_identity_interface_node(["t1_file", "white"], "input_spec")

    # convert raw t1 to lia
    t1_to_lia = Node(MRIConvert(), "T1toLIA")
    t1_to_lia.inputs.out_orientation = "LIA"
    t1_to_lia.inputs.out_file = "t1_lia.mgz"
    workflow.connect(input_spec, 't1_file', t1_to_lia, 'in_file')

    # Create ones image for use when masking the white matter
    ones = Node(Function(['in_volume', 'out_file'],
                         ['out_file'],
                         create_ones_image),
                name="Ones_Image")
    ones.inputs.out_file = "ones.mgz"

    workflow.connect(t1_to_lia, 'out_file', ones, 'in_volume')

    # use the ones image to obtain a white matter mask
    surfmask = Node(SurfaceMask(), name="WhiteMask")
    surfmask.inputs.out_file = "white_ras.mgz"

    workflow.connect(ones, 'out_file', surfmask, 'in_volume')
    workflow.connect(input_spec, 'white', surfmask, 'in_surface')

    surfmask_to_nifti = Node(MRIConvert(), "MasktoNIFTI")
    surfmask_to_nifti.inputs.out_file = "white.nii.gz"
    surfmask_to_nifti.inputs.out_orientation = "LPS"

    workflow.connect(surfmask, 'out_file', surfmask_to_nifti, 'in_file')

    output_spec = create_identity_interface_node(["white_mask"], "output_spec")
    workflow.connect(surfmask_to_nifti, "out_file", output_spec, "white_mask")

    return workflow


def create_logismosb_machine_learning_workflow(name="MachineLearningLOGISMOSB", resample=True, hemispheres=None,
                                               plugin_args=None):
    workflow = Workflow(name)
    input_spec = Node(IdentityInterface(["rho", "phi", "theta", "posteriors", "t1_file", "t2_file", "acpc_transform",
                                         "classifier_file", "orig_t1", "hncma_file", "abc_file",
                                         "lh_white_surface_file", "rh_white_surface_file"]), name="input_spec")

    outputs = []
    surface_files = ['gmsurface_file', 'wmsurface_file']
    if not hemispheres:
        hemispheres = ["lh", "rh"]
    for hemi in hemispheres:
        for surface_name in surface_files:
            outputs.append(hemi + "_" + surface_name)
    output_spec = create_identity_interface_node(outputs, "output_spec")

    if resample:
        # resample reference image to spacing (1,1,1)
        reference_image = Node(CreateReferenceImage(), name="ResampleInputT1")
        workflow.connect([(input_spec, reference_image, [("orig_t1", "orig_t1"),
                                                         ("t1_file", "baw_t1")])])

        # resample input images that are not used in the feature data
        resample_baw = create_workflow_to_resample_baw_files()
        workflow.connect([(reference_image, resample_baw, [("reference_file", "input_spec.reference_file")]),
                          (input_spec, resample_baw, [("hncma_file", "input_spec.hncma_file"),
                                                      ("abc_file", "input_spec.abc_file"),
                                                      ("t1_file", "input_spec.t1_file"),
                                                      ("t2_file", "input_spec.t2_file"),
                                                      ("acpc_transform", "input_spec.acpc_transform"),
                                                      ])])

        # create and connect machine learning
        predict_gm = create_machine_learning_workflow(resample=resample, plugin_args=plugin_args)
        feature_files = ["rho", "phi", "theta", "posteriors"]
        for feature in feature_files:
            workflow.connect([(input_spec, predict_gm, [(feature, "input_spec.{0}".format(feature))])])
        workflow.connect([(resample_baw, predict_gm, [("output_spec.t1_file", "input_spec.t1_file")]),
                          (input_spec, predict_gm, [("acpc_transform", "input_spec.acpc_transform"),
                                                    ("classifier_file", "input_spec.classifier_file")]),
                          ])

        from nipype_interfaces import scale_image
        scale_gm_proba = Node(Function(["image_file", "out_file", "scale", "square"], ["out_file"], scale_image),
                              name="ScaleGMPorbabilityMap")
        scale_gm_proba.inputs.square = True
        scale_gm_proba.inputs.scale = 1000
        scale_gm_proba.inputs.out_file = "gm_probability_scaled.nii.gz"
        workflow.connect(predict_gm, "output_spec.probability_map", scale_gm_proba, "image_file")

        from nipype_interfaces import create_white_edge_cost_image
        white_edge_cost = Node(Function(["t1_file", "t2_file", "gm_proba_file", "out_file"], ["out_file"],
                                        create_white_edge_cost_image), name="WhiteMatterEdgeCost")
        workflow.connect([(resample_baw, white_edge_cost, [("output_spec.t1_file", "t1_file"),
                                                           ("output_spec.t2_file", "t2_file")]),
                          (predict_gm, white_edge_cost, [("output_spec.probability_map", "gm_proba_file")])])
        white_edge_cost.inputs.out_file = "white_edge_cost.nii.gz"

        for hemisphere in hemispheres:

            mask_wm = create_workflow_to_mask_white_matter("{0}_MaskWhiteMatter".format(hemisphere))
            workflow.connect([(input_spec, mask_wm, [("{0}_white_surface_file".format(hemisphere), "input_spec.white")]),
                              (resample_baw, mask_wm, [("output_spec.t1_file", "input_spec.t1_file")])])

            convert_white = Node(MRIsConvert(), name="{0}_Convert_White".format(hemisphere))
            convert_white.inputs.out_file = "{0}_white.vtk".format(hemisphere)
            convert_white.inputs.to_scanner = True
            workflow.connect([(input_spec, convert_white, [("{0}_white_surface_file".format(hemisphere), "in_file")])])

            logb = create_logismosb_node("{0}_LOGISMOSB".format(hemisphere))
            logb.inputs.basename = hemisphere
            # connect logb inputs
            workflow.connect([(resample_baw, logb, [("output_spec.hncma_file", "atlas_file"),
                                                    ("output_spec.abc_file", "brainlabels_file"),
                                                    ("output_spec.t1_file", "t1_file"),
                                                    ("output_spec.t2_file", "t2_file")]),
                              (convert_white, logb, [("converted", "mesh_file")]),
                              (mask_wm, logb, [("output_spec.white_mask", "wm_file")]),
                              (scale_gm_proba, logb, [("out_file", "gm_proba_file")]),
                              (white_edge_cost, logb, [("out_file", "wm_proba_file")])])

            for surface_name in surface_files:
                workflow.connect(logb, surface_name, output_spec, hemisphere + "_" + surface_name)

        return workflow
