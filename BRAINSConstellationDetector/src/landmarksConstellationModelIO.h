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
 * Author: Hans J. Johnson, Wei Lu
 * at Psychiatry Imaging Lab,
 * University of Iowa Health Care 2010
 */

#ifndef landmarksConstellationModelIO_h
#define landmarksConstellationModelIO_h

#include "landmarksConstellationCommon.h"
#include "landmarksConstellationTrainingDefinitionIO.h"
#include "landmarksConstellationModelBase.h"

#include "itkByteSwapper.h"
#include "itkIO.h"
#include "itkNumberToString.h"
#include <vector>
#include <fstream>
#include <iostream>
#include <cmath>
#include <cstring>
#include <map>

#include "BRAINSConstellationDetectorVersion.h"

//TODO: Move non-templated implementation of member functions to the landmarksConstellationDetectorModelIO.cxx file

////
inline void
defineTemplateIndexLocations
  (const float r,
  const float h,
  std::vector<SImageType::PointType::VectorType> & indexLocations)
{
  typedef SImageType::PointType::VectorType::ComponentType CoordType;

  // Reserve space that will be needed
  indexLocations.reserve( static_cast<unsigned int>( 4 * r * r * h ) );

  const CoordType h_2 = h / 2;
  const CoordType r2 = r * r;
  for( CoordType SI = -r; SI <= r; SI += 1.0F )
    {
    for( CoordType PA = -r; PA <= r; PA += 1.0F )
      {
      for( CoordType LR = -h_2; LR <= h_2; LR += 1.0F )
        {
        if( ( SI * SI + PA * PA )  <= r2 )  // a suspicious place
          {
          SImageType::PointType::VectorType temp;
          temp[0] = LR;
          temp[1] = PA;
          temp[2] = SI;
          indexLocations.push_back(temp);
          }
        }
      }
    }
}

class landmarksConstellationModelIO : public landmarksConstellationModelBase
{
private:
  typedef landmarksConstellationModelIO Self;
  typedef enum { readFail, writeFail }  ioErr;
  typedef enum { file_signature = 0x12345678,
                 swapped_file_signature = 0x78563412 } fileSig;
public:
  typedef std::vector<SImageType::PointType::VectorType> IndexLocationVectorType;
  typedef std::vector<float>                             FloatVectorType;
  typedef std::vector<FloatVectorType>                   Float2DVectorType;
  typedef std::vector<Float2DVectorType>                 Float3DVectorType;

  typedef FloatVectorType::iterator       FloatVectorIterator;
  typedef FloatVectorType::const_iterator ConstFloatVectorIterator;

  typedef Float2DVectorType::iterator       Float2DVectorIterator;
  typedef Float2DVectorType::const_iterator ConstFloat2DVectorIterator;

  typedef Float3DVectorType::iterator       Float3DVectorIterator;
  typedef Float3DVectorType::const_iterator ConstFloat3DVectorIterator;

  landmarksConstellationModelIO() : m_Swapped(false), m_RPPC_to_RPAC_angleMean(0), m_RPAC_over_RPPCMean(0)
  {
  }

  virtual ~landmarksConstellationModelIO()
  {
  }

  void SetCMtoRPMean(const SImageType::PointType::VectorType & CMtoRPMean)
  {
    this->m_CMtoRPMean = CMtoRPMean;
  }

  void SetRPtoXMean(std::string name, const SImageType::PointType::VectorType & RPtoXMean)
  {
    this->m_RPtoXMean[name] = RPtoXMean;
  }

  void SetRPtoCECMean(const SImageType::PointType::VectorType & RPtoCECMean)
  {
    this->m_RPtoCECMean = RPtoCECMean;
  }

  void SetRPPC_to_RPAC_angleMean(float RPPC_to_RPAC_angleMean)
  {
    this->m_RPPC_to_RPAC_angleMean = RPPC_to_RPAC_angleMean;
  }

  void SetRPAC_over_RPPCMean(float RPAC_over_RPPCMean)
  {
    this->m_RPAC_over_RPPCMean = RPAC_over_RPPCMean;
  }

  const SImageType::PointType::VectorType & GetCMtoRPMean() const
  {
    return this->m_CMtoRPMean;
  }

  const SImageType::PointType::VectorType & GetRPtoXMean(std::string name)
  {
    return this->m_RPtoXMean[name];
  }

  const SImageType::PointType::VectorType & GetRPtoCECMean() const
  {
    return this->m_RPtoCECMean;
  }

  float GetRPPC_to_RPAC_angleMean() const
  {
    return this->m_RPPC_to_RPAC_angleMean;
  }

  float GetRPAC_over_RPPCMean() const
  {
    return this->m_RPAC_over_RPPCMean;
  }

  /**
   * Creates a mean for each of the angles by collapsing the image
   * dimensions.
   *
   * @author hjohnson (9/6/2008)
   *
   * @param output
   * @param input
   */
  void ComputeAllMeans(Float2DVectorType & output, const Float3DVectorType & input);

  // Access the internal memory locations for modification.
  FloatVectorType & AccessTemplate(std::string name, const unsigned int indexDataSet, const unsigned int indexAngle)
  {
    if( this->m_Templates.find(name) == this->m_Templates.end() )
      {
      itkGenericExceptionMacro(<< "Attempt to access an undifined landmark template for "
                               << name);
      }
    return this->m_Templates[name][indexDataSet][indexAngle];
  }

  // Access the mean vectors of templates
  const FloatVectorType & AccessTemplateMean(std::string name, const unsigned int indexAngle)
  {
    if( this->m_TemplateMeansComputed.find(name) == this->m_TemplateMeansComputed.end()
        || this->m_Templates.find(name) == this->m_Templates.end() )
      {
      itkGenericExceptionMacro(<< "Attempt to access an undifined landmark template (mean)!");
      }
    ComputeAllMeans(this->m_TemplateMeans[name], this->m_Templates[name]);
    return this->m_TemplateMeans[name][indexAngle];
  }

  const Float2DVectorType & AccessAllTemplateMeans(std::string name)
  {
    if( this->m_TemplateMeansComputed.find(name) == this->m_TemplateMeansComputed.end()
        && this->m_Templates.find(name) == this->m_Templates.end() )
      {
      itkGenericExceptionMacro(<< "Attempt to access an undefined landmark template (mean)!");
      }
    ComputeAllMeans(this->m_TemplateMeans[name], this->m_Templates[name]);
    return this->m_TemplateMeans[name];
  }

  const Float2DVectorType & GetTemplateMeans(const std::string& name)
  {
    return this->m_TemplateMeans[name];
  }

  void WriteModelFile(const std::string & filename);


  void PrintHeaderInfo(void) const;

  void ReadModelFile(const std::string & filename);


  class debugImageDescriptor  // An inner class
  {
public:
    Float2DVectorType &     mean;
    IndexLocationVectorType locations;
    float                   r;
    float                   h;
    const char *            debugImageName;

    debugImageDescriptor(Float2DVectorType & _mean, float _r, float _h, const char *_debugImageName) :
      mean(_mean), r(_r), h(_h), debugImageName(_debugImageName)
    {
      defineTemplateIndexLocations(_r, _h, this->locations);
    }
  };

  void WritedebugMeanImages(std::string name);
  void InitializeModel(const bool CreatingModel);


  void CopyFromModelDefinition(const landmarksConstellationTrainingDefinitionIO & mDef)
  {
    this->SetNumDataSets( mDef.GetNumDataSets() );
    this->SetSearchboxDims( mDef.GetSearchboxDims() );
    this->SetResolutionUnits( mDef.GetResolutionUnits() );
    this->SetInitialRotationAngle( mDef.GetInitialRotationAngle() );
    this->SetInitialRotationStep( mDef.GetInitialRotationStep() );
    this->SetNumRotationSteps( mDef.GetNumRotationSteps() );

      {
      ValMapConstIterator it2;
      for( it2 = mDef.GetRadii().begin(); it2 != mDef.GetRadii().end(); ++it2 )
        {
        this->SetRadius(it2->first, it2->second);
        this->SetHeight( it2->first, mDef.GetHeight(it2->first) );
        this->m_TemplateMeansComputed[it2->first] = false;
        }
      }
  }

  bool NE(double const a, double const b)
  {
    if( ( a < 0.0 && b >= 0.0 )
        || ( b < 0.0 && a >= 0.0 ) )
      {
      return true;
      }
    double absa( fabs(a) ),
    absb( fabs(b) );
    double absdiff( fabs(absa - absb) );
    double avg( ( absa + absb ) / 2.0 );
    if( absdiff > ( avg / 1000.0 ) )
      {
      return true;
      }
    return false;
  }

  bool NE(const std::string & label,
          const Float2DVectorType & a,
          const Float2DVectorType & b)
  {
    itk::NumberToString<double> doubleToString;

    for( unsigned i = 0; i < a.size(); i++ )
      {
      for( unsigned j = 0; j < a[i].size(); j++ )
        {
        if( NE(a[i][j], b[i][j]) )
          {
          std::cerr << label << " a[" << i
                    << "] = " << doubleToString(a[i][j])
                    << "b[" << j << "] = "
                    << doubleToString(b[i][j]) << std::endl;
          return true;
          }
        }
      }
    return false;
  }

  bool operator==(Self & other)
  {
    if( ( NE(this->m_SearchboxDims, other.m_SearchboxDims) )
        || ( NE(this->m_ResolutionUnits, other.m_ResolutionUnits) )
        || ( NE(this->m_NumDataSets, other.m_NumDataSets) )
        || ( NE(this->m_NumRotationSteps, other.m_NumRotationSteps) )
        || ( NE(this->m_RPPC_to_RPAC_angleMean, other.m_RPPC_to_RPAC_angleMean) )
        || ( NE(this->m_RPAC_over_RPPCMean, other.m_RPAC_over_RPPCMean) )
        || ( NE(this->m_CMtoRPMean[0], other.m_CMtoRPMean[0]) )
        || ( NE(this->m_CMtoRPMean[1], other.m_CMtoRPMean[1]) )
        || ( NE(this->m_CMtoRPMean[2], other.m_CMtoRPMean[2]) ) )
      {
      return false;
      }

    std::map<std::string, bool>::const_iterator it2;
    for( it2 = this->m_TemplateMeansComputed.begin(); it2 != this->m_TemplateMeansComputed.end(); ++it2 )
      {
      if( ( NE( this->GetRadius(it2->first), other.GetRadius(it2->first) ) )
          || ( NE( this->GetHeight(it2->first), other.GetHeight(it2->first) ) )
          || ( NE(it2->first + " template mean",
                  this->m_TemplateMeans[it2->first], other.m_TemplateMeans[it2->first]) ) )
        {
        return false;
        }
      }

    if( ( NE(this->m_RPtoXMean["AC"][0], other.m_RPtoXMean["AC"][0]) )
        || ( NE(this->m_RPtoXMean["AC"][1], other.m_RPtoXMean["AC"][1]) )
        || ( NE(this->m_RPtoXMean["PC"][0], other.m_RPtoXMean["PC"][0]) )
        || ( NE(this->m_RPtoXMean["PC"][1], other.m_RPtoXMean["PC"][1]) )
        || ( NE(this->m_RPtoXMean["VN4"][0], other.m_RPtoXMean["VN4"][0]) )
        || ( NE(this->m_RPtoXMean["VN4"][1], other.m_RPtoXMean["VN4"][1]) ) )
      {
      return false;
      }

    return true;
  }

  // TODO: HACK:  Kent please wrap these in member variables
  std::map<std::string, landmarksConstellationModelIO::IndexLocationVectorType> m_VectorIndexLocations;
private:
  bool m_Swapped;

  template <class T>
  void Write(std::ofstream & f, T var)
  {
    if( f.bad() || f.eof() )
      {
      throw landmarksConstellationModelIO::writeFail;
      }
    f.write( reinterpret_cast<char *>( &var ), sizeof( T ) );
  }

  template <class T>
  void Read(std::stringstream & f, T & var)
  {
    if( f.bad() || f.eof() )
      {
      throw landmarksConstellationModelIO::readFail;
      }

    f.read( reinterpret_cast<char *>( &var ), sizeof( T ) );
    if( this->m_Swapped )
      {
      if( itk::ByteSwapper<T>::SystemIsBigEndian() )
        {
        itk::ByteSwapper<T>::SwapFromSystemToLittleEndian(&var);
        }
      else
        {
        itk::ByteSwapper<T>::SwapFromSystemToBigEndian(&var);
        }
      }
  }

  void Write(std::ofstream & f, const Float2DVectorType & vec)
  {
    for( ConstFloat2DVectorIterator it1 = vec.begin();
         it1 != vec.end(); ++it1 )
      {
      for( ConstFloatVectorIterator it2 = it1->begin();
           it2 != it1->end(); ++it2 )
        {
        this->Write<float>(f, *it2);
        }
      }
  }

  void Read(std::stringstream & f, Float2DVectorType & vec)
  {
    for( Float2DVectorIterator it1 = vec.begin();
         it1 != vec.end(); ++it1 )
      {
      for( FloatVectorIterator it2 = it1->begin();
           it2 != it1->end(); ++it2 )
        {
        this->Read<float>(f, *it2);
        }
      }
  }

#ifdef __USE_OFFSET_DEBUGGING_CODE__
  void debugOffset(std::ifstream *f, const std::string & msg, long int x)
  {
    std::ostream::pos_type offset(-1);

    offset = f->tellg();
    std::cerr << msg << " " << x << " offset " << offset << std::endl;
    std::cerr.flush();
  }

  void debugOffset(std::ofstream *f, const std::string & msg, long int x)
  {
    std::ostream::pos_type offset(-1);

    offset = f->tellp();
    std::cerr << msg << " " << x << " offset " << offset << std::endl;
    std::cerr.flush();
  }

#endif
  // The templates are arrays of data sets, arrayed by number of angles, and a
  // vector of model intensity values.
  std::map<std::string, Float3DVectorType> m_Templates;
  std::map<std::string, Float2DVectorType> m_TemplateMeans;
  std::map<std::string, bool>              m_TemplateMeansComputed;
  std::map<std::string,
           SImageType::PointType::VectorType> m_RPtoXMean;

  SImageType::PointType::VectorType m_RPtoCECMean;           // CEC is a little
                                                             // different
  SImageType::PointType::VectorType m_CMtoRPMean;
  float                             m_RPPC_to_RPAC_angleMean;
  float                             m_RPAC_over_RPPCMean;
};

#endif // landmarksConstellationModelIO_h
