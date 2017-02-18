//
// Created by Johnson, Hans J on 2/14/17.
//
#include "landmarksConstellationModelIO.h"

void landmarksConstellationModelIO::PrintHeaderInfo(void) const
{
  //
  //
  // //////////////////////////////////////////////////////////////////////////
  std::cout << "SearchboxDims"    << ": " << this->GetSearchboxDims() << std::endl;
  std::cout << "ResolutionUnits"  << ": " << this->GetResolutionUnits() << std::endl;
  std::cout << "NumDataSets"      << ": " << this->GetNumDataSets() << std::endl;
  std::cout << "NumRotationSteps" << ": " << this->GetNumRotationSteps() << std::endl;

  std::map<std::string, bool>::const_iterator it2;

  for( it2 = this->m_TemplateMeansComputed.begin();
       it2 != this->m_TemplateMeansComputed.end(); ++it2 )
  {
    std::cout << it2->first << "Radius: " << this->GetRadius(it2->first) << std::endl;
    std::cout << it2->first << "Height: " << this->GetHeight(it2->first) << std::endl;
  }

  std::cout << "CMtoRPMean: " << this->m_CMtoRPMean << std::endl;
  std::cout << "RPtoECEMean: " << this->m_RPtoCECMean << std::endl;
  std::cout << "RPtoACMean: " << this->m_RPtoXMean.at("AC") << std::endl;
  std::cout << "RPtoPCMean: " << this->m_RPtoXMean.at("PC") << std::endl;
  std::cout << "RPtoVN4Mean: " << this->m_RPtoXMean.at("VN4") << std::endl;
  std::cout << "RPPC_to_RPAC_angleMean: " << this->m_RPPC_to_RPAC_angleMean << std::endl;
  std::cout << "RPAC_over_RPPCMean: " << this->m_RPAC_over_RPPCMean << std::endl;
}


void landmarksConstellationModelIO::WriteModelFile(const std::string & filename)
{
  //
  //
  // //////////////////////////////////////////////////////////////////////////
  itk::NumberToString<double> doubleToString;
  std::ofstream  output( filename.c_str() ); // open setup file for reading

  if( !output.is_open() )
  {
    std::cerr << "Can't write " << filename << std::endl;
    std::cerr.flush();
  }
  try
  {
    this->Write<unsigned int>(output, file_signature);   // Write out the
    // signature first
    /*
     * WEI: As the new model deals with arbitrary landmarks, we need to
     * write the landmark names to the model file in order to
     * differentiate for example the search radius of each landmark.
     * That means ofstream::write() alone is not sufficient for reading
     * landmark names with variable length.
     */
    this->Write<char>(output, '\n');

    output << BCDVersionString << std::endl;

    std::map<std::string, bool>::const_iterator it2;
    for( it2 = this->m_TemplateMeansComputed.begin();
         it2 != this->m_TemplateMeansComputed.end(); ++it2 )
    {
      output << it2->first.c_str() << std::endl;
      output << doubleToString(this->GetRadius(it2->first) ) << std::endl;
      output << doubleToString(this->GetHeight(it2->first) ) << std::endl;
    }
    output << "END" << std::endl;

    this->Write<unsigned int>( output, this->GetSearchboxDims() );
    this->Write<float>( output, this->GetResolutionUnits() );
    this->Write<unsigned int>( output, this->GetNumDataSets() );
    this->Write<unsigned int>( output, this->GetNumRotationSteps() );

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&output, "before vectors", -1);
#endif
    for( it2 = this->m_TemplateMeansComputed.begin();
         it2 != this->m_TemplateMeansComputed.end(); ++it2 )
    {
      ComputeAllMeans(this->m_TemplateMeans[it2->first],
        this->m_Templates[it2->first]);
      this->Write(output, this->m_TemplateMeans[it2->first]);
      this->WritedebugMeanImages(it2->first);
    }

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&output, "after vectors", -1);
#endif

    // We only need those RPtoXMeans
    this->Write<double>(output, this->m_RPtoXMean["PC"][0]);
    this->Write<double>(output, this->m_RPtoXMean["PC"][1]);
    this->Write<double>(output, this->m_RPtoXMean["PC"][2]);
    this->Write<double>(output, this->m_CMtoRPMean[0]);
    this->Write<double>(output, this->m_CMtoRPMean[1]);
    this->Write<double>(output, this->m_CMtoRPMean[2]);
    this->Write<double>(output, this->m_RPtoXMean["VN4"][0]);
    this->Write<double>(output, this->m_RPtoXMean["VN4"][1]);
    this->Write<double>(output, this->m_RPtoXMean["VN4"][2]);
    this->Write<double>(output, this->m_RPtoCECMean[0]);
    this->Write<double>(output, this->m_RPtoCECMean[1]);
    this->Write<double>(output, this->m_RPtoCECMean[2]);
    this->Write<double>(output, this->m_RPtoXMean["AC"][0]);
    this->Write<double>(output, this->m_RPtoXMean["AC"][1]);
    this->Write<double>(output, this->m_RPtoXMean["AC"][2]);
    this->Write<float>(output, this->m_RPPC_to_RPAC_angleMean);
    this->Write<float>(output, this->m_RPAC_over_RPPCMean);

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&output, "end of file", -1);
#endif
  }
  catch( ioErr e )
  {
    std::cerr << "Write failed for " << filename << std::endl;
    std::cerr << e << std::endl;
  }
  output.close();
}

void landmarksConstellationModelIO::ComputeAllMeans(Float2DVectorType & output, const Float3DVectorType & input)
{
  // First allocate the output mememory
  output.resize( input[0].size() );
  for( unsigned int q = 0; q < output.size(); q++ )
  {
    output[q].resize( input[0][0].size() );
    for( FloatVectorIterator oit = output[q].begin(); oit != output[q].end(); ++oit )
    {
      *oit = 0;
    }
  }
  for( ConstFloat3DVectorIterator curr_dataset = input.begin(); curr_dataset != input.end(); ++curr_dataset )
  {
    ConstFloat2DVectorIterator input_angleit = curr_dataset->begin();
    Float2DVectorIterator      output_angleit = output.begin();
    while( input_angleit != curr_dataset->end() && output_angleit != output.end() )
    {
      ConstFloatVectorIterator init = input_angleit->begin();
      FloatVectorIterator      outit = output_angleit->begin();
      while( init != input_angleit->end() && outit != output_angleit->end() )
      {
        *outit += *init;
        ++outit;
        ++init;
      }

      ++input_angleit;
      ++output_angleit;
    }
  }
  // Now divide by number of data sets
  const float inv_size = 1.0 / input.size();
  for( unsigned int q = 0; q < output.size(); q++ )
  {
    for( FloatVectorIterator oit = output[q].begin(); oit != output[q].end(); ++oit )
    {
      *oit *= inv_size;
    }
  }
}


void landmarksConstellationModelIO::ReadModelFile(const std::string & filename)
{
  //
  //
  // //////////////////////////////////////////////////////////////////////////
  std::string entire_file_as_string("");
  {
    std::ifstream myfile(filename.c_str());

    if (!myfile.is_open()) {
      itkGenericExceptionMacro(<< "Cannot open model file!"
                               << filename);
    }
    const std::string temp((std::istreambuf_iterator<char>(myfile)),
      std::istreambuf_iterator<char>());
    entire_file_as_string = temp;
    myfile.close();
  }
  std::stringstream file_as_stream(entire_file_as_string);

  try
  {
    unsigned int sig = 0;
    this->Read<unsigned int>(file_as_stream, sig);
    if( sig != file_signature && sig != swapped_file_signature )
    {
      this->m_Swapped = false;
    }
    else if( sig == swapped_file_signature )
    {
      this->m_Swapped = true;
    }

    {
      std::string Version("INVALID");

      file_as_stream >> Version;

      std::cout << "Input model file version: " << Version << std::endl;
      if( Version.compare( BCDVersionString ) != 0 )
      {
        itkGenericExceptionMacro(<<"Input model file is outdated.\n"
                                 << "Input model file version: " << Version
                                 << ", Required version: " << BCDVersionString << std::endl);
      }
    }
    /*
     * WEI: As the new model deals with arbitrary landmarks, we need to
     * write the landmark names to the model file in order to
     * differentiate for example the search radius of each landmark.
     * That means ofstream::write() alone is not sufficient for reading
     * landmark names with variable length.
     */
    std::string name;
    file_as_stream >> name;
    while( name.compare("END") != 0 )
    {
      file_as_stream >> this->m_Radius[name];
      file_as_stream >> this->m_Height[name];
      this->m_TemplateMeansComputed[name] = false;
      file_as_stream >> name;
    }

    {
      char tmp = '\0';
      this->Read<char>(file_as_stream, tmp);
    }


    this->Read<unsigned int>(file_as_stream, this->m_SearchboxDims);
    this->Read<float>(file_as_stream, this->m_ResolutionUnits);
    this->Read<unsigned int>(file_as_stream, this->m_NumDataSets);
    this->Read<unsigned int>(file_as_stream, this->m_NumRotationSteps);

    std::cout << "NumberOfDataSets: " << this->m_NumDataSets << std::endl;
    std::cout << "SearchBoxDims: " << this->m_SearchboxDims << std::endl;
    std::cout << "ResolutionUnits: " << this->m_ResolutionUnits << std::endl;
    std::cout << "NumberOfRotationSteps: " << this->m_NumRotationSteps << std::endl;

    // initalize the size of m_VectorIndexLocations and m_TemplateMeans
    InitializeModel(false);

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&input, "before vectors", -1);
#endif

    {
      std::map<std::string, bool>::const_iterator it2;
      for( it2 = this->m_TemplateMeansComputed.begin();
           it2 != this->m_TemplateMeansComputed.end(); ++it2 )
      {
        this->Read(file_as_stream, this->m_TemplateMeans[it2->first]);
        this->m_TemplateMeansComputed[it2->first] = true;
      }
    }

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&file_as_stream, "after vectors", -1);
#endif

    this->Read<double>(file_as_stream, this->m_RPtoXMean["PC"][0]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["PC"][1]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["PC"][2]);
    this->Read<double>(file_as_stream, this->m_CMtoRPMean[0]);
    this->Read<double>(file_as_stream, this->m_CMtoRPMean[1]);
    this->Read<double>(file_as_stream, this->m_CMtoRPMean[2]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["VN4"][0]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["VN4"][1]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["VN4"][2]);
    this->Read<double>(file_as_stream, this->m_RPtoCECMean[0]);
    this->Read<double>(file_as_stream, this->m_RPtoCECMean[1]);
    this->Read<double>(file_as_stream, this->m_RPtoCECMean[2]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["AC"][0]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["AC"][1]);
    this->Read<double>(file_as_stream, this->m_RPtoXMean["AC"][2]);
    this->Read<float>(file_as_stream, this->m_RPPC_to_RPAC_angleMean);
    this->Read<float>(file_as_stream, this->m_RPAC_over_RPPCMean);

#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&file_as_stream, "end of file", -1);
#endif
  }
  catch( ioErr e )
  {
#ifdef __USE_OFFSET_DEBUGGING_CODE__
    this->debugOffset(&file_as_stream, "end of file", -1);
#endif
    std::cerr << "ioErr " << e << std::endl;
    throw;
  }
}

void landmarksConstellationModelIO::WritedebugMeanImages(std::string name)
{
  debugImageDescriptor DID(this->m_TemplateMeans[name],
    this->GetRadius(name),
    this->GetHeight(name),
    "");

  Float2DVectorType::iterator meanIt = DID.mean.begin();

  for( int j = 0; meanIt != DID.mean.end(); ++meanIt, j++ )
  {
    typedef itk::Image<float, 3>        FloatImageType;
    typedef FloatImageType::RegionType  FloatImageRegion;
    typedef FloatImageType::SpacingType FloatImageSpacing;
    FloatImageSpacing spacing;
    spacing[0] = spacing[1] = spacing[2] = 1.0;
    FloatImageRegion region;
    region.SetSize
      ( 0, static_cast<FloatImageRegion::SizeValueType>( DID.h + 1 ) );
    region.SetSize
      (1, static_cast<FloatImageRegion::SizeValueType>( 2.0 * DID.r ) + 1);
    region.SetSize
      (2, static_cast<FloatImageRegion::SizeValueType>( 2.0 * DID.r ) + 1);
    FloatImageRegion::IndexType _index;
    _index[0] = _index[1] = _index[2] = 0;
    region.SetIndex(_index);
    FloatImageType::Pointer debugImage = FloatImageType::New();
    debugImage->SetSpacing(spacing);
    // Just use defaults debugImage->SetOrigin(in->GetOrigin());
    // Just use defaults debugImage->SetDirection(in->GetDirection());
    debugImage->SetRegions(region);
    debugImage->Allocate();
    debugImage->FillBuffer(0.0);
    float center[3];

    center[0] = ( DID.h + 1.0 ) * 0.5;
    center[1] = center[2] = ( DID.r + 0.5 );

    IndexLocationVectorType::const_iterator locIt = DID.locations.begin();
    IndexLocationVectorType::const_iterator locItEnd = DID.locations.end();
    for( FloatVectorType::iterator floatIt = ( *meanIt ).begin();
         locIt != locItEnd;
         ++floatIt, ++locIt )
    {
      FloatImageType::IndexType ind;
      for( unsigned k = 0; k < 3; k++ )
      {
        ind[k] = static_cast<FloatImageType::IndexValueType>( center[k] + ( *locIt )[k] );
      }
      debugImage->SetPixel( ind, ( *floatIt ) );
    }
    char buf[512];
    sprintf( buf, "%d%s", j, name.c_str() );
    std::string fname(buf);
    fname += "Mean.nii.gz";
    itkUtil::WriteImage<FloatImageType>(debugImage, fname);
  }
}

void landmarksConstellationModelIO::InitializeModel(const bool CreatingModel)
{
  //
  //
  // ///////////////////////////////////////////////////////////////////////////////
  // NOTE:  THIS IS NOW AT FULL RESOLUTION, but there was an optimization that
  // had reduced
  //       the resolution in the IS/RP direction to gain some speed
  // efficiency.
  std::map<std::string, bool>::const_iterator it2;

  for( it2 = this->m_TemplateMeansComputed.begin(); it2 != this->m_TemplateMeansComputed.end(); ++it2 )
  {
    defineTemplateIndexLocations(this->GetRadius(it2->first), this->GetHeight(it2->first),
      this->m_VectorIndexLocations[it2->first]);
    printf( "%s template size = %u voxels\n", it2->first.c_str(),
      static_cast<unsigned int>( this->m_VectorIndexLocations[it2->first].size() ) );
    if( CreatingModel )
    {
      // Allocate the outter dim for all datasets
      this->m_Templates[it2->first].resize( this->GetNumDataSets() );
      for( unsigned int currdataset = 0; currdataset < this->GetNumDataSets(); ++currdataset )
      {
        // Allocate for number of angles
        this->m_Templates[it2->first][currdataset].resize( this->GetNumRotationSteps() );
        for( unsigned int currrotstep = 0; currrotstep < this->GetNumRotationSteps(); ++currrotstep )
        {
          // Allocate for number of intensity values
          this->m_Templates[it2->first][currdataset][currrotstep].resize
            ( this->m_VectorIndexLocations[it2->first].size() );
        }
      }
    }
    else // make room for reading in template means result
    {
      this->m_TemplateMeans[it2->first].resize( this->GetNumRotationSteps() );
      for( unsigned i = 0; i < this->GetNumRotationSteps(); ++i )
      {
        this->m_TemplateMeans[it2->first][i].resize
          ( this->m_VectorIndexLocations[it2->first].size() );
      }
    }
  }
}