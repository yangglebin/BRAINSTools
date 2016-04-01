/*=========================================================================
 *
 *  Copyright SINAPSE: Scalable Informatics for Neuroscience, Processing and Software Engineering
 *            The University of Iowa
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0.txt
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 *=========================================================================*/
// Author: Ali Ghayoor

#include <iostream>
#include "itkIO.h"
#include "itkImageFileReader.h"
#include "itkMultiResolutionPyramidImageFilter.h"

#include "StandardizeMaskIntensity.h"
#include "itkReflectiveCorrelationCenterToImageMetric.h"

#include "ComputeReflectiveCorrelationMetricCLP.h"

typedef itk::MultiResolutionPyramidImageFilter<SImageType, SImageType>  PyramidFilterType;
typedef Rigid3DCenterReflectorFunctor< itk::PowellOptimizerv4<double> > ReflectionFunctorType;
typedef ReflectionFunctorType::ParametersType                           ParametersType;
typedef itk::CastImageFilter<DImageType3D, SImageType>                  CasterType;

PyramidFilterType::Pointer MakeOneLevelPyramid(SImageType::Pointer refImage)
{
  PyramidFilterType::ScheduleType pyramidSchedule;

  PyramidFilterType::Pointer MyPyramid = PyramidFilterType::New();

  MyPyramid->SetInput(refImage);
  MyPyramid->SetNumberOfLevels(1);
  pyramidSchedule.SetSize(1, 3);

  SImageType::SpacingType refImageSpacing = refImage->GetSpacing();
  for( unsigned int c = 0; c < pyramidSchedule.cols(); ++c )
    {
    pyramidSchedule[0][c] = static_cast<unsigned int>( 2 * round(4.0 / refImageSpacing[c]) );
    }
  MyPyramid->SetSchedule(pyramidSchedule);
  MyPyramid->Update();
  return MyPyramid;
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;
  BRAINSRegisterAlternateIO();

  // load image
  std::cout << "\nLoading image..." << std::endl;
  // Input image is read as a double image;
  // then it is rescaled to a specific dynamic range;
  // Finally it is cast to a Short type image.
  typedef itk::ImageFileReader<DImageType3D> ReaderType;
  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName( inputVolume );
  try
    {
    reader->Update();
    }
  catch( itk::ExceptionObject & err )
    {
    std::cerr << " Error while reading image file( s ) with ITK:\n "
              << err << std::endl;
    }

  DImageType3D::Pointer rescaledInputVolume =
    StandardizeMaskIntensity<DImageType3D, ByteImageType>(reader->GetOutput(),
                                                          ITK_NULLPTR,
                                                          0.0005, 1.0 - 0.0005,
                                                          1, 0.95 * MAX_IMAGE_OUTPUT_VALUE,
                                                          0, MAX_IMAGE_OUTPUT_VALUE);

  CasterType::Pointer caster = CasterType::New();
  caster->SetInput( rescaledInputVolume );
  caster->Update();

  //SImageType::Pointer inputImage = caster->GetOutput();
  PyramidFilterType::Pointer MyPyramid = MakeOneLevelPyramid( caster->GetOutput() );
  SImageType::Pointer inputImage = MyPyramid->GetOutput(0); // one-eighth image

  ReflectionFunctorType::Pointer reflectionFunctor = ReflectionFunctorType::New();
  reflectionFunctor->SetDownSampledReferenceImage(inputImage);

  // optimal parameters
  ParametersType opt_params;
  opt_params.set_size(ReflectionFunctorType::SpaceDimension);
  opt_params.fill(0.0);
  reflectionFunctor->SetParameters(opt_params);
  double opt_cc = reflectionFunctor->GetValue();

  // search parameters
  ParametersType current_params;
  current_params.set_size(ReflectionFunctorType::SpaceDimension);
  current_params.fill(0.0);

  std::stringstream csvFileOfMetricValues;
  csvFileOfMetricValues << "#HA, BA, LR, cc" << std::endl;

  const double HA_range = 45.0;
  const double BA_range = 45.0;
  const double LR_range = 5;

  const double LR_stepsize = 1; // mm
  const double HA_stepsize = 5; // degree
  const double BA_stepsize = 5; // degree

  const double degree_to_rad = 1.0F * vnl_math::pi / 180.0F;

  for( double LR = -LR_range; LR <= LR_range; LR += LR_stepsize)
    {
    for( double HA = -HA_range; HA <= HA_range; HA += HA_stepsize )
      {
      for( double BA = -BA_range; BA <= BA_range; BA += BA_stepsize )
        {
        current_params[0] = HA * degree_to_rad;
        current_params[1] = BA * degree_to_rad;
        current_params[2] = LR;

        reflectionFunctor->SetParameters(current_params);
        reflectionFunctor->SetDoPowell(false);
        reflectionFunctor->Update();
        const double current_cc = reflectionFunctor->GetValue();

        if( current_cc < opt_cc )
          {
          opt_params = current_params;
          opt_cc = current_cc;
          }
/*
#define WRITE_CSV_FILE
#ifdef WRITE_CSV_FILE
*/
        csvFileOfMetricValues << HA << "," << BA << "," << LR << "," << current_cc << std::endl;
//#endif
        }
      }
    }

  std::cout << "Optimize parameters by exhaustive search: [" << opt_params[0] << "," << opt_params[1] << "," << opt_params[2] << "]" << std::endl;
  std::cout << "Optimize metric value by exhaustive search: " << opt_cc << std::endl;

  if( outputCSVFile != "" )
    {
    std::cout << "\nWriting out metric values in a csv file..." << std::endl;
    std::ofstream csvFile;
    csvFile.open( outputCSVFile.c_str() );
    if( !csvFile.is_open() )
      {
      itkGenericExceptionMacro( << "Error: Can't write oputput csv file!" << std::endl );
      }
    csvFile << csvFileOfMetricValues.str();
    csvFile.close();
    }

  // Now compare find the optimal parameters using Powell Optimizer
  ReflectionFunctorType::Pointer reflectionFunctor2 = ReflectionFunctorType::New();
  reflectionFunctor2->SetDownSampledReferenceImage(inputImage);
  reflectionFunctor2->Initialize();
  reflectionFunctor2->Update();
  ParametersType powell_params = reflectionFunctor2->GetParameters();
  double powell_cc = reflectionFunctor2->GetValue();

  std::cout << "Optimize parameters by exhaustive search: [" << powell_params[0] << "," << powell_params[1] << "," << powell_params[2] << "]" << std::endl;
  std::cout << "Optimize metric value by exhaustive search: " << powell_cc << std::endl;

  // here compare opt_params with input baseline params to return failure or success.

  return EXIT_SUCCESS;
}
