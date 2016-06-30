# LOGISMOS-B Workflow
# Import Nipype classes

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.pipeline import Node, Workflow
from nipype.interfaces.io import DataSink
from interfaces import *
import json

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


def create_logb_workflow(name="LOGIMSOSB_WF"):
    logb_wf = Workflow(name=name)

    with open("config.json", "rb") as config_file:
        config = json.load(config_file)

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

    wmMasking_node = Node(interface=WMMasking(), name="WMMasking")
    wmMasking_node.inputs.dilation = config['WMMasking']['dilation']
    wmMasking_node.inputs.atlas_info = config['atlas_info']

    logb_wf.connect([(inputs_node, wmMasking_node, [("csf_file", "csf_file"),
                                                    ("fswm_atlas", "atlas_file"),
                                                    ("brainlabels_file", "brainlabels_file")])])

    gm_labels = Node(interface=CreateGMLabelMap(), name="GM_Labelmap")
    gm_labels.inputs.atlas_info = config['atlas_info']
    logb_wf.connect([(inputs_node, gm_labels, [('fswm_atlas', 'atlas_file')])])

    logismosb_output_node = LOGIMOSBOutputSpec(["wmsurface_file", "gmsurface_file"], config["hemisphere_names"])

    for hemisphere in config["hemisphere_names"]:
        g0 = Node(interface=GenusZeroImageFilter(), name="{0}_GenusZeroImageFilter".format(hemisphere))
        g0.inputs.connectivity = config['GenusZeroImageFilter']['connectivity']
        g0.inputs.biggestComponent = config['GenusZeroImageFilter']['biggestComponent']
        g0.inputs.connectedComponent = config['GenusZeroImageFilter']['connectedComponent']
        g0.inputs.out_mask = "{0}_genus_zero_white_matter.nii.gz".format(hemisphere)

        logb_wf.connect([(wmMasking_node, g0, [('{0}_wm'.format(hemisphere), 'in_file')])])

        BSG = Node(interface=BRAINSSurfaceGeneration(), name="{0}_BRAINSSurfaceGeneration".format(hemisphere))
        BSG.inputs.smoothSurface = config['BRAINSSurfaceGeneration']['smoothSurface']
        BSG.inputs.numIterations = config['BRAINSSurfaceGeneration']['numIterations']
        BSG.inputs.out_file = "{0}_white_matter_surface.vtk".format(hemisphere)

        logb_wf.connect([(g0, BSG, [('out_file', 'in_file')])])

        logB = Node(interface=LOGISMOSB(), name="{0}_LOGISMOSB".format(hemisphere))
        logB.inputs.smoothnessConstraint = config['LOGISMOSB']['smoothnessConstraint']
        logB.inputs.nColumns = config['LOGISMOSB']['nColumns']
        logB.inputs.columnChoice = config['LOGISMOSB']['columnChoice']
        logB.inputs.columnHeight = config['LOGISMOSB']['columnHeight']
        logB.inputs.nodeSpacing = config['LOGISMOSB']['nodeSpacing']
        logB.inputs.w = config['LOGISMOSB']['w']
        logB.inputs.a = config['LOGISMOSB']['a']
        logB.inputs.nPropagate = config['LOGISMOSB']['nPropagate']
        logB.inputs.basename = hemisphere
        if config['LOGISMOSB']['thickRegions']:
            logB.inputs.thick_regions = config['LOGISMOSB']['thickRegions']
        else:
            logB.inputs.useHNCMALabels = True

        logb_wf.connect([(inputs_node, logB, [("t1_file", "t1_file"),
                                              ("t2_file", "t2_file"),
                                              ('hncma_atlas', 'atlas_file')]),
                         (g0, logB, [("out_file", "wm_file")]),
                         (BSG, logB, [("out_file", "mesh_file")]),
                         (wmMasking_node, logB, [('{0}_boundary'.format(hemisphere), 'brainlabels_file')]),
                         (logB, logismosb_output_node, [("gmsurface_file", "{0}_gmsurface_file".format(hemisphere)),
                                                        ("wmsurface_file", "{0}_wmsurface_file".format(hemisphere))])])

        ctx_thickness = Node(ComputeDistance(), name="ctx_thickness")
        ctx_thickness.inputs.atlas_info = config['atlas_info']
        ctx_thickness.inputs.hemisphere = hemisphere
        logb_wf.connect([(gm_labels, ctx_thickness, [('out_file', 'labels_file')])])

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

        logb_wf.connect([(base_dir_name, data_sink, [('base_dir', 'base_directory')]),
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
                         ])

    return logb_wf


class LOGIMOSBOutputSpec(IdentityInterface):
    def __init__(self, outputs, hemisphere_names, **inputs):
        final_output_names = list()
        for output in outputs:
            for hemisphere in hemisphere_names:
                final_output_names.append("{0}_".format(hemisphere) + output)
        super(LOGIMOSBOutputSpec, self).__init__(fields=final_output_names, **inputs)
