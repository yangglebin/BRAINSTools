# LOGISMOS-B Workflow
# Import Nipype classes

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.pipeline import Node, Workflow
from nipype.interfaces.io import DataSink
from interfaces import *


def leftorright(
        hemisphere,
        lh_wm,
        rh_wm,
        rh_boundary,
        lh_boundary):

    if hemisphere == 'lh':
        wm_file = lh_wm
        boundary_file = lh_boundary
    else:
        wm_file = rh_wm
        boundary_file = rh_boundary
    mask_file = hemisphere + '_g0_wm.nii.gz'
    mesh_file = hemisphere + '_g0_wm.vtk'
    return hemisphere, wm_file, mask_file, mesh_file, boundary_file


def create_logb_workflow(config):

    inputs_node = Node(
        IdentityInterface(
            fields=['subject_id',
                    'session_id',
                    't1_file',
                    't2_file',
                    'csf_file',
                    'fswm_atlas',
                    'brainlabels_file',
                    'hncma_atlas']), name="Inputs")
    inputs_node.run_without_submitting = True

    g0 = Node(interface=GenusZeroImageFilter(), name="GenusZeroImageFilter")
    g0.inputs.connectivity = config['GenusZeroImageFilter']['connectivity']
    g0.inputs.biggestComponent = config['GenusZeroImageFilter']['biggestComponent']
    g0.inputs.connectedComponent = config['GenusZeroImageFilter']['connectedComponent']

    BSG = Node(interface=BRAINSSurfaceGeneration(), name="BRAINSSurfaceGeneration")
    BSG.inputs.smoothSurface = config['BRAINSSurfaceGeneration']['smoothSurface']
    BSG.inputs.numIterations = config['BRAINSSurfaceGeneration']['numIterations']

    logB = Node(interface=LOGISMOSB(), name="LOGISMOSB")
    logB.inputs.smoothnessConstraint = config['LOGISMOSB']['smoothnessConstraint']
    logB.inputs.nColumns = config['LOGISMOSB']['nColumns']
    logB.inputs.columnChoice = config['LOGISMOSB']['columnChoice']
    logB.inputs.columnHeight = config['LOGISMOSB']['columnHeight']
    logB.inputs.nodeSpacing = config['LOGISMOSB']['nodeSpacing']
    logB.inputs.w = config['LOGISMOSB']['w']
    logB.inputs.a = config['LOGISMOSB']['a']
    logB.inputs.nPropagate = config['LOGISMOSB']['nPropagate']
    if config['LOGISMOSB']['useHNCMALabels']:
        logB.inputs.useHNCMALabels = True
        logB.inputs.thick_regions = config['LOGISMOSB']['HNCMAThickRegions']

    logB_outputnode = Node(IdentityInterface(fields=["gmsurface_file",
                                                     "wmsurface_file",
                                                     "thickness_file"]),
                           name="Outputs")

    hemi_inputs_node = Node(Function(["hemisphere",
                                      "lh_boundary",
                                      "rh_boundary",
                                      "lh_wm",
                                      "rh_wm"],
                                     ['hemisphere',
                                      'wm_file',
                                      'mask_file',
                                      'mesh_file',
                                      'boundary_file'],
                                     leftorright
                                     ),
                            name="Hemi_Inputs")
    hemi_inputs_node.iterables = ("hemisphere", ["lh", "rh"])

    wmMasking_node = Node(interface=WMMasking(), name="WMMasking")
    wmMasking_node.inputs.dilation = config['WMMasking']['dilation']
    wmMasking_node.inputs.atlas_info = config['atlas_info']

    gm_labels = Node(interface=CreateGMLabelMap(), name="GM_Labelmap")
    gm_labels.inputs.atlas_info = config['atlas_info']

    ctx_thickness = Node(ComputeDistance(), name="ctx_thickness")
    ctx_thickness.inputs.atlas_info = config['atlas_info']

    LOGB_WF = Workflow(name="LOGB_WF")

    LOGB_WF.connect([(inputs_node, wmMasking_node, [("csf_file", "csf_file"),
                                                    ("fswm_atlas", "atlas_file"),
                                                    ("brainlabels_file", "brainlabels_file"),
                                                    ]),
                     (wmMasking_node, hemi_inputs_node, [("rh_boundary", "rh_boundary"),
                                                         ("lh_boundary", "lh_boundary"),
                                                         ("lh_wm", "lh_wm"),
                                                         ("rh_wm", "rh_wm")]),
                     (inputs_node, logB, [("t1_file", "t1_file"),
                                          ("t2_file", "t2_file")]),
                     (hemi_inputs_node, logB, [("hemisphere", "basename"),
                                               ("boundary_file", "brainlabels_file")]),
                     (hemi_inputs_node, g0, [("wm_file", "in_file"),
                                             ("mask_file", "out_mask")]),
                     (hemi_inputs_node, BSG, [("mesh_file", "out_file")]),
                     (g0, BSG, [("out_file", "in_file")]),
                     (g0, logB, [("out_file", "wm_file")]),
                     (BSG, logB, [("out_file", "mesh_file")]),
                     (logB, logB_outputnode, [("gmsurface_file", "gmsurface_file"),
                                              ("wmsurface_file", "wmsurface_file")]),
                     (logB, ctx_thickness, [("gmsurface_file", "gm_file"),
                                            ("wmsurface_file", "wm_file")]),
                     (gm_labels, ctx_thickness, [('out_file', 'labels_file')]),
                     (hemi_inputs_node, ctx_thickness, [('hemisphere', 'hemisphere')]),
                     (inputs_node, gm_labels, [('fswm_atlas', 'atlas_file')]),
                     (inputs_node, logB, [('hncma_atlas', 'atlas_file')])
                     ])


    if config['Results_Directory']:
        # datasink the workflow
        def myBaseDir(results_dir, subject_id, session):
            import os
            base_dir = os.path.abspath(os.path.join(results_dir, subject_id, session))
            return base_dir

        # DataSink
        base_dir_name = Node(Function(['results_dir', 'subject_id', 'session'],
                                      ['base_dir'],
                                      myBaseDir),
                             name="Base_Dir_Name")
        base_dir_name.inputs.results_dir = config['Results_Directory']
        base_dir_name.run_without_submitting = True

        data_sink = Node(DataSink(), name="LOGISMOSB_DataSink")
        substitutions = [('_hemisphere_lh', ''),
                         ('_hemisphere_rh', '')]
        if config['BAW_Directories'] != None and len(config['BAW_Directories']) > 0:
            for sub in config['BAW_Directories']:
                my_sub = ('_baw_dir_{0}'.format(sub.replace('/', '..')), '')
                substitutions.append(my_sub)
        data_sink.inputs.substitutions = substitutions

        LOGB_WF.connect([(base_dir_name, data_sink, [('base_dir', 'base_directory')]),
                         (inputs_node, base_dir_name, [('subject_id', 'subject_id'),
                                                       ('session_id', 'session')]),
                         (logB, data_sink, [('gmsurface_file', 'LOGISMOSB'),
                                            ('wmsurface_file', 'LOGISMOSB.@a'),
                                            ('profile_file', 'LOGISMOSB.@g'),
                                            ]),
                         (ctx_thickness, data_sink, [('out_file', 'LOGISMOSB.@b')]),
                         (gm_labels, data_sink, [('out_file', 'LOGISMOSB.@c')]),
                         (g0, data_sink, [('out_file', 'LOGISMOSB.@e')]),
                         (BSG, data_sink, [('out_file', 'LOGISMOSB.@f')]),
                         (hemi_inputs_node, data_sink, [("boundary_file", "LOGISMOSB.@h")]),
                         ])

        if config['copy_BAW']:
            LOGB_WF.connect([(inputs_node, data_sink, [('subject_id', 'BAW'),
                                                       ('session_id', 'BAW.@a'),
                                                       ('t1_file', 'BAW.@b'),
                                                       ('t2_file', 'BAW.@c'),
                                                       ('csf_file', 'BAW.@d'),
                                                       ('fswm_atlas', 'BAW.@e'),
                                                       ('brainlabels_file', 'BAW.@f')])])

    return LOGB_WF
