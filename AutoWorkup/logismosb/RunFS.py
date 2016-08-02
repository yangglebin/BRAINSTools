
# coding: utf-8

# In[ ]:

#from workflow import create_logb_workflow
from nipype.workflows.smri.freesurfer import create_reconall_workflow
from workflow import create_fs_logb_workflow_for_both_hemispheres

import sqlite3
connection = sqlite3.connect("/Shared/sinapse/CACHE/20160712_AtrophySimulation_Results/results.db")
cursor = connection.cursor()

num_threads = 12

import glob
import os
from nipype import Workflow, DataSink, Node
base_dir = "/Shared/sinapse/CACHE/20160728_LOGISMOSB_baseline_CACHE"
for row in cursor.execute("SELECT t1_image_file, t2_image_file, session_id from input"):
    session_id = str(row[2])
    t1_file = str(row[0])
    t2_file = str(row[1])
    
    wf = Workflow(name="FreeSurfer_{0}".format(session_id))
    
    subject_directory = os.path.dirname(os.path.dirname(t1_file))
    
    fs = create_reconall_workflow(name="FreeSurfer_{0}".format(session_id),
                                  plugin_args={"qsub_args": "-q HJ,UI,all.q,COE -pe smp {0}".format(num_threads),
                                               "overwrite": True})
    fs.inputs.inputspec.T1_files = [t1_file]
    fs.inputs.inputspec.T2_file = t2_file
    fs.inputs.inputspec.num_threads = num_threads
    fs.inputs.inputspec.subject_id = "FreeSurfer"
    fs.inputs.inputspec.subjects_dir = subject_directory
    
    hncma_atlas = os.path.join(subject_directory, "WarpedAtlas2Subject", "hncma_atlas.nii.gz")
    
    logb = create_fs_logb_workflow_for_both_hemispheres(name="FSLOGB_{0}".format(session_id), 
                                                        plugin_args={"qsub_args": "-q HJ,UI,all.q,COE -pe smp {0}".format(num_threads),
                                                                     "overwrite": True})
    wf.connect([(fs, logb, [('outputspec.aseg_presurf', 'inputspec.aseg_presurf'),
                            ('outputspec.rawavg', 'inputspec.rawavg'),
                            ('outputspec.t2_raw', 'inputspec.t2_raw'),
                            ('outputspec.lh_white', 'inputspec.lh_white'),
                            ('outputspec.rh_white', 'inputspec.rh_white')])])
    logb.inputs.inputspec.hncma_atlas = hncma_atlas
    
    datasink = Node(DataSink(), name="DataSink")
    datasink.inputs.base_directory = subject_directory
    for hemisphere in ("lh", "rh"):
        for matter in ("gm", "wm"):
            wf.connect(logb, "outputspec.{0}_{1}_surf_file".format(hemisphere, matter),
                       datasink, "LOGISMOSB.FreeSurfer.@{0}_{1}".format(hemisphere, matter))
            
    wf.base_dir = base_dir
    wf.config['execution']['job_finished_timeout'] = 120
    # wf.run(plugin="SGEGraph", plugin_args={"qsub_args": "-q HJ,all.q,COE,UI"})
    wf.run()
