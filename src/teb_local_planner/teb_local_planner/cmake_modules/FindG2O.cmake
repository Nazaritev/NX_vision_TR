# Locate the g2o libraries
# A general framework for graph optimization.
#
# This module defines
# G2O_FOUND, if false, do not try to link against g2o
# G2O_LIBRARIES, path to the libg2o
# G2O_INCLUDE_DIR, where to find the g2o header files
#
# Niko Suenderhauf <niko@etit.tu-chemnitz.de>
# Adapted by Felix Endres <endres@informatik.uni-freiburg.de>

IF(UNIX)

  #IF(G2O_INCLUDE_DIR AND G2O_LIBRARIES)
    # in cache already
    #  SET(G2O_FIND_QUIETLY TRUE)
    #ENDIF(G2O_INCLUDE_DIR AND G2O_LIBRARIES)

  MESSAGE(STATUS "Searching for g2o ...")
  set(_G2O_SEARCH_PATHS
    ${G2O_ROOT}
    $ENV{G2O_ROOT}
    ${CMAKE_PREFIX_PATH}
    /usr/local
    /usr
    /opt/ros/humble
    /home/dgut/Nazarite/third_party/g2o-install
  )
  FIND_PATH(G2O_INCLUDE_DIR
    NAMES core math_groups types
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES include/g2o include)

  IF (G2O_INCLUDE_DIR)
    get_filename_component(G2O_INCLUDE_DIR_PARENT "${G2O_INCLUDE_DIR}" DIRECTORY)
    if(EXISTS "${G2O_INCLUDE_DIR_PARENT}/g2o")
      set(G2O_INCLUDE_DIR "${G2O_INCLUDE_DIR_PARENT}")
    endif()
    MESSAGE(STATUS "Found g2o headers in: ${G2O_INCLUDE_DIR}")
  ENDIF (G2O_INCLUDE_DIR)

  FIND_LIBRARY(G2O_CORE_LIB             
    NAMES g2o_core g2o_core_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_STUFF_LIB            
    NAMES g2o_stuff g2o_stuff_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_TYPES_SLAM2D_LIB     
    NAMES g2o_types_slam2d g2o_types_slam2d_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_TYPES_SLAM3D_LIB     
    NAMES g2o_types_slam3d g2o_types_slam3d_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_SOLVER_CHOLMOD_LIB   
    NAMES g2o_solver_cholmod g2o_solver_cholmod_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_SOLVER_PCG_LIB       
    NAMES g2o_solver_pcg g2o_solver_pcg_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_SOLVER_CSPARSE_LIB   
    NAMES g2o_solver_csparse g2o_solver_csparse_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_INCREMENTAL_LIB      
    NAMES g2o_incremental g2o_incremental_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)
  FIND_LIBRARY(G2O_CSPARSE_EXTENSION_LIB
    NAMES g2o_csparse_extension g2o_csparse_extension_rd
    PATHS ${_G2O_SEARCH_PATHS}
    PATH_SUFFIXES lib)

  set(_G2O_REQUIRED_LIB_NAMES
      G2O_CORE_LIB
      G2O_STUFF_LIB
      G2O_TYPES_SLAM2D_LIB
      G2O_SOLVER_CSPARSE_LIB
      G2O_CSPARSE_EXTENSION_LIB
  )

  set(_G2O_OPTIONAL_LIB_NAMES
      G2O_TYPES_SLAM3D_LIB
      G2O_SOLVER_CHOLMOD_LIB
      G2O_SOLVER_PCG_LIB
      G2O_INCREMENTAL_LIB
  )

  set(G2O_LIBRARIES "")
  set(_G2O_ALL_REQUIRED_LIBS_FOUND TRUE)

  foreach(_g2o_lib_name IN LISTS _G2O_REQUIRED_LIB_NAMES)
    if(${_g2o_lib_name} AND NOT ${_g2o_lib_name} MATCHES "-NOTFOUND$")
      list(APPEND G2O_LIBRARIES ${${_g2o_lib_name}})
    else()
      set(_G2O_ALL_REQUIRED_LIBS_FOUND FALSE)
    endif()
  endforeach()

  foreach(_g2o_lib_name IN LISTS _G2O_OPTIONAL_LIB_NAMES)
    if(${_g2o_lib_name} AND NOT ${_g2o_lib_name} MATCHES "-NOTFOUND$")
      list(APPEND G2O_LIBRARIES ${${_g2o_lib_name}})
    endif()
  endforeach()

  IF(_G2O_ALL_REQUIRED_LIBS_FOUND AND G2O_INCLUDE_DIR)
    SET(G2O_FOUND "YES")
    IF(NOT G2O_FIND_QUIETLY)
      MESSAGE(STATUS "Found libg2o: ${G2O_LIBRARIES}")
    ENDIF(NOT G2O_FIND_QUIETLY)
  ELSE(_G2O_ALL_REQUIRED_LIBS_FOUND AND G2O_INCLUDE_DIR)
    IF(NOT _G2O_ALL_REQUIRED_LIBS_FOUND)
      IF(G2O_FIND_REQUIRED)
        message(FATAL_ERROR "Could not find libg2o!")
      ENDIF(G2O_FIND_REQUIRED)
    ENDIF(NOT _G2O_ALL_REQUIRED_LIBS_FOUND)

    IF(NOT G2O_INCLUDE_DIR)
      IF(G2O_FIND_REQUIRED)
        message(FATAL_ERROR "Could not find g2o include directory!")
      ENDIF(G2O_FIND_REQUIRED)
    ENDIF(NOT G2O_INCLUDE_DIR)
  ENDIF(_G2O_ALL_REQUIRED_LIBS_FOUND AND G2O_INCLUDE_DIR)

ENDIF(UNIX)
