# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.6

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list


# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/mhatina/dnf-module-plugin

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/mhatina/dnf-module-plugin

# Utility rule file for smoke.

# Include the progress variables for this target.
include tests-smoke/CMakeFiles/smoke.dir/progress.make

tests-smoke/CMakeFiles/smoke:
	cd /home/mhatina/dnf-module-plugin/tests-smoke && ./runtests.sh

smoke: tests-smoke/CMakeFiles/smoke
smoke: tests-smoke/CMakeFiles/smoke.dir/build.make

.PHONY : smoke

# Rule to build all files generated by this target.
tests-smoke/CMakeFiles/smoke.dir/build: smoke

.PHONY : tests-smoke/CMakeFiles/smoke.dir/build

tests-smoke/CMakeFiles/smoke.dir/clean:
	cd /home/mhatina/dnf-module-plugin/tests-smoke && $(CMAKE_COMMAND) -P CMakeFiles/smoke.dir/cmake_clean.cmake
.PHONY : tests-smoke/CMakeFiles/smoke.dir/clean

tests-smoke/CMakeFiles/smoke.dir/depend:
	cd /home/mhatina/dnf-module-plugin && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/mhatina/dnf-module-plugin /home/mhatina/dnf-module-plugin/tests-smoke /home/mhatina/dnf-module-plugin /home/mhatina/dnf-module-plugin/tests-smoke /home/mhatina/dnf-module-plugin/tests-smoke/CMakeFiles/smoke.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : tests-smoke/CMakeFiles/smoke.dir/depend

