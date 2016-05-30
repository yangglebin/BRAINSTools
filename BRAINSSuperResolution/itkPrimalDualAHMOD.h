/*=========================================================================
 *
 *  Copyright Insight Software Consortium
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
 * SINAPSE Lab, The University of Iowa 2016
 */

#ifndef itkPrimalDualAHMOD_h
#define itkPrimalDualAHMOD_h

namespace itk
{
/** \class itkPrimalDualAHMOD
 * \brief put class description here ...
 *
 *
 *
 */

//template< typename TSample >
class itkPrimalDualAHMOD:
  public Object
{
public:
  /** Standard class typedefs */
  typedef PrimalDualAHMOD                       Self;
  typedef Object                                Superclass;
  typedef SmartPointer< Self >                  Pointer;
  typedef SmartPointer< const Self >            ConstPointer;

  /** Strandard macros */
  itkTypeMacro(PrimalDualAHMOD, Object);
  itkNewMacro(Self);


};
} // end namespace itk

#ifndef ITK_MANUAL_INSTANTIATION
#include "itkPrimalDualAHMOD.hxx"
#endif

#endif //itkPrimalDualAHMOD_h
