# Install script for directory: /home/mhatina/dnf-module-plugin/fm

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "0")
endif()

if("${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/lib/python2.7/site-packages/fm/__init__.py;/usr/lib/python2.7/site-packages/fm/api_client.py;/usr/lib/python2.7/site-packages/fm/api_clients.py;/usr/lib/python2.7/site-packages/fm/cli.py;/usr/lib/python2.7/site-packages/fm/config_file.py;/usr/lib/python2.7/site-packages/fm/exceptions.py;/usr/lib/python2.7/site-packages/fm/fm_modules_resolver.py;/usr/lib/python2.7/site-packages/fm/main.py;/usr/lib/python2.7/site-packages/fm/metadata_cache.py;/usr/lib/python2.7/site-packages/fm/module.py;/usr/lib/python2.7/site-packages/fm/modules.py;/usr/lib/python2.7/site-packages/fm/modules_search.py;/usr/lib/python2.7/site-packages/fm/option_parser.py;/usr/lib/python2.7/site-packages/fm/repo_config_file.py;/usr/lib/python2.7/site-packages/fm/repo_file.py")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/lib/python2.7/site-packages/fm" TYPE FILE FILES
    "/home/mhatina/dnf-module-plugin/fm/__init__.py"
    "/home/mhatina/dnf-module-plugin/fm/api_client.py"
    "/home/mhatina/dnf-module-plugin/fm/api_clients.py"
    "/home/mhatina/dnf-module-plugin/fm/cli.py"
    "/home/mhatina/dnf-module-plugin/fm/config_file.py"
    "/home/mhatina/dnf-module-plugin/fm/exceptions.py"
    "/home/mhatina/dnf-module-plugin/fm/fm_modules_resolver.py"
    "/home/mhatina/dnf-module-plugin/fm/main.py"
    "/home/mhatina/dnf-module-plugin/fm/metadata_cache.py"
    "/home/mhatina/dnf-module-plugin/fm/module.py"
    "/home/mhatina/dnf-module-plugin/fm/modules.py"
    "/home/mhatina/dnf-module-plugin/fm/modules_search.py"
    "/home/mhatina/dnf-module-plugin/fm/option_parser.py"
    "/home/mhatina/dnf-module-plugin/fm/repo_config_file.py"
    "/home/mhatina/dnf-module-plugin/fm/repo_file.py"
    )
endif()

