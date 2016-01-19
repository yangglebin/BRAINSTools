# This file is mostly copied from vxl/dash_example.cmake from the dashboard branch of vxl

# BRAINSTools Example Dashboard Script
#
# Copy this example script and edit as necessary for your client.
# See brainstools_common.cmake for more instructions.

# Client maintainer: someone@users.sourceforge.net
set(CTEST_SITE "machine.site")
set(CTEST_BUILD_NAME "Linux-gcc")
set(CTEST_BUILD_FLAGS "-j8") # parallel build for makefiles
set(CTEST_BUILD_CONFIGURATION Release)
set(CTEST_CMAKE_GENERATOR "Unix Makefiles")
#set(CTEST_GIT_COMMAND /path/to/git)

#set(dashboard_model Experimental)
#set(dashboard_model Continuous)

#set(dashboard_do_memcheck 1)
#set(dashboard_do_coverage 1)

#set(dashboard_cache "
#BUILD_SHARED_LIBS:BOOL=ON
#")

include(${CTEST_SCRIPT_DIRECTORY}/brainstools_common.cmake)
