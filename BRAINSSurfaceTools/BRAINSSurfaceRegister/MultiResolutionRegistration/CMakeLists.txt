StandardBRAINSBuildMacro(NAME MultiResolutionRegistration TARGET_LIBRARIES BRAINSCommonLib ${BRAINSSurfaceTools_ITK_LIBRARIES} ${VTK_LIBRARIES})

if (BUILD_TESTING AND NOT BRAINSTools_DISABLE_TESTING)


ExternalData_add_test(${PROJECT_NAME}FetchData NAME TEST_SurfaceMultiResRegistration1
  COMMAND ${LAUNCH_EXE} $<TARGET_FILE:MultiResolutionRegistration>
          --fixedMeshFileList DATA{${TestData_DIR}/0036195_left_sphereIC4.vtk}
          --fixedMeshFileList DATA{${TestData_DIR}/0036195_left_sphereIC5.vtk}
          --fixedMeshFileList DATA{${TestData_DIR}/0036195_left_sphereIC6.vtk}
          --fixedMeshFileList DATA{${TestData_DIR}/0036195_left_sphereIC7.vtk}
          --movingMeshFileList DATA{${TestData_DIR}/0036896_left_sphereIC4.vtk}
          --movingMeshFileList DATA{${TestData_DIR}/0036896_left_sphereIC5.vtk}
          --movingMeshFileList DATA{${TestData_DIR}/0036896_left_sphereIC6.vtk}
          --movingMeshFileList DATA{${TestData_DIR}/0036896_left_sphereIC7.vtk}
          --fixedMeshFileName DATA{${TestData_DIR}/0036195_left_sphere.vtk}
          --movingMeshFileName DATA{${TestData_DIR}/0036896_left_sphere.vtk}
          --rigidIterations 5,5,5,1
          --demonsIterations 5,5,5,1
          --smoothIterations 10,10,10,10
          --metricSignificance 0.05,0.05,0.05,0.05
          --deformedFileNameRes4 deformed0036195IC7_test.vtk
          --deformedFileName deformed0036195_test.vtk
          --deformationFieldFileName deformationFieldOn0036195_test.vtk )

ExternalData_add_test(${PROJECT_NAME}FetchData NAME COMPARE_SurfaceMultiResRegistration1
  COMMAND ${LAUNCH_EXE} $<TARGET_FILE:CompareSurfaces>
          --inputSurfaceFile deformed0036195_test.vtk
          --refSurfaceFile DATA{${TestData_DIR}/deformed0036195.vtk}
          --vertexLocation
          --tolerance 1.0e-7 )

set_tests_properties( COMPARE_SurfaceMultiResRegistration1 PROPERTIES DEPENDS TEST_SurfaceMultiResRegistration1 )

## - ExternalData_Add_Target( ${PROJECT_NAME}FetchData )  # Name of data management target

endif ()
