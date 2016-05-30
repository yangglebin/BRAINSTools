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
/*
 * \author: Ali Ghayoor
 * at SINAPSE Lab,
 * The University of Iowa 2016
 */

#include <iostream>
#include <itkImageFileReader.h>
#include <itkImageFileWriter.h>

#include "GenerateMaxGradientImage.h"

#include "BRAINSSuperResolutionCLP.h"
#include <BRAINSCommonLib.h>

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  typedef float PixelType;
  const unsigned int Dim = 3;

  typedef itk::Image<PixelType, Dim>                  InputImageType;
  typedef InputImageType::Pointer                     InputImagePointer;
  typedef std::vector<InputImagePointer>              InputImageList;
  typedef itk::ImageFileReader<InputImageType>        ImageReaderType;

  typedef unsigned char                               EdgeMapPixelType;
  typedef itk::Image<EdgeMapPixelType, Dim>           EdgeMapImageType;

  std::vector<std::string> inputMRFileNames;
  if( inputMRVolumes.size() > 0 )
    {
    inputMRFileNames = inputMRVolumes;
    }
  else
    {
    std::cerr << "ERROR: At least one MR image modality is needed to generate the maximum edgemap." << std::endl;
    return EXIT_FAILURE;
    }
  const unsigned int numberOfMRImages = inputMRFileNames.size(); // number of modality images

  // Read the input MR modalities and set them in a vector of images
  typedef ImageReaderType::Pointer             LocalReaderPointer;

  InputImageList inputMRImageModalitiesList;
  for( unsigned int i = 0; i < numberOfMRImages; i++ )
    {
    std::cout << "Reading image: " << inputMRFileNames[i] << std::endl;
    LocalReaderPointer imgreader = ImageReaderType::New();
    imgreader->SetFileName( inputMRFileNames[i].c_str() );
    try
      {
      imgreader->Update();
      }
    catch( ... )
      {
      std::cerr << "ERROR:  Could not read image " << inputMRFileNames[i] << "." << std::endl;
      return EXIT_FAILURE;
      }
    inputMRImageModalitiesList.push_back( imgreader->GetOutput() );
    }

  // Create maximum gradient image using the input structural MR images.
  EdgeMapImageType::Pointer edgeMap = GenerateMaxGradientImage<
    InputImageType,EdgeMapImageType>(inputMRImageModalitiesList);

  if( outputEdgeMap.compare( "" ) != 0 )
    {
    typedef itk::ImageFileWriter<EdgeMapImageType> WriterType;
    WriterType::Pointer writer = WriterType::New();
    writer->UseCompressionOn();
    writer->SetFileName( outputEdgeMap );
    writer->SetInput( edgeMap );
    try
      {
      writer->Update();
      }
    catch( itk::ExceptionObject & exp )
      {
      std::cerr << "ExceptionObject with writer" << std::endl;
      std::cerr << exp << std::endl;
      return EXIT_FAILURE;
      }
    }

  // Read the input DWI image
  std::cout << "Reading DWI image: " << inputVolumeDWI << std::endl;
  ImageReaderType::Pointer dwi_b0_imageReader = ImageReaderType::New();
  dwi_b0_imageReader->SetFileName(inputVolumeDWI);
  try
    {
    dwi_b0_imageReader->Update();
    }
  catch( ... )
    {
    std::cerr << "ERROR:  Could not read image " << inputVolumeDWI << "." << std::endl;
    return EXIT_FAILURE;
    }
  InputImagePointer dwi_b0 = dwi_b0_imageReader->GetOutput();


  return EXIT_SUCCESS;
}
