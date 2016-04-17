# This file is mostly copied from vxl/dash_example.cmake from the dashboard branch of vxl

# BRAINSTools Example Dashboard Script
#
# Copy this example script and edit as necessary for your client.
# See brainstools_common.cmake for more instructions.

# Client maintainer: someone@users.sourceforge.net
set(CTEST_SITE "medusa.psychiatry.uiowa.edu") #the default is the hostname
set(CTEST_BUILD_NAME "Linux-gcc")
set(CTEST_BUILD_FLAGS "-j12") # parallel build for makefiles
set(CTEST_BUILD_CONFIGURATION "Debug")
set(CTEST_CMAKE_GENERATOR "Unix Makefiles")
#set(CTEST_GIT_COMMAND /path/to/git)


set(dashboard_project_name BRAINSTools)
#set(CTEST_BUILD_FLAGS "-j2") # parallel build for makefiles
#set(CTEST_BUILD_CONFIGURATION Release)
#set(CTEST_CMAKE_GENERATOR "Unix Makefiles")
#set(dashboard_multiple_git_branches 1)
#set(dashboard_git_branch dashboard)
set(dashboard_model Nightly)
#set(dashboard_model Continuous)
set(dashboard_git_url http://github.com/BRAINSIa/BRAINSTools.git)
set(dashboard_do_memcheck 1)
set(dashboard_do_coverage 1)

set(secondary_dashboard 1)
set(secondary_drop_method "https")
set(secondary_site "code-testing.iibi.uiowa.edu")
set(secondary_location "/submit.php?project=BRAINSTools")

set(dashboard_no_clean 1)
# brainstools modules all turned off (for testing)
#include(${CTEST_SCRIPT_DIRECTORY}/brainsModulesAllOff.cmake)


#set(dashboard_cache "
#BUILD_SHARED_LIBS:BOOL=ON
#")

include(${CTEST_SCRIPT_DIRECTORY}/brainstools_common.cmake)



