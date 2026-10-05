cmake_minimum_required(VERSION 3.18)
project(pysync_cpp CXX) # CXX means C++, pysync_cpp is the project name

set(CMAKE_CXX_STANDARD 17) # Minimum C++ version
set(CMAKE_CXX_STANDARD_REQUIRED ON) # Requires minimum version for compilation

#find_package(pybind11 REQUIRED CONFIG) # Necessary for running as C++ program that calls embedded python (NTPUpdater)


# Execute python to get the pybind11 cmake path automatically
execute_process(
    COMMAND python -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
include_directories(src/cpp/include) # makes headers shorter

# compile C++ into a static library target to make use with pybind easier
add_library(pysync_core
    src/cpp/src/l1_clock.cpp
    src/cpp/src/offset_anchor.cpp
    src/cpp/src/cppendpoints.cpp
)
if(WIN32)
    target_link_libraries(pysync_core PRIVATE winmm) # Link winmm.lib (Windows Multimedia library) to support timeBeginPeriod 
endif()


# TODO: un-slop these comments

enable_testing()
# Find all test source files in src/cpp/tests/. CONFIGURE_DEPENDS means this updates every time the directory is changed.
file(GLOB TEST_SOURCES CONFIGURE_DEPENDS "src/cpp/tests/*.cpp")

foreach(TEST_SRC ${TEST_SOURCES})
    # Extract filename without extension (e.g. test)
    get_filename_component(TEST_NAME ${TEST_SRC} NAME_WE)
    
    # Register executable target
    add_executable(${TEST_NAME} ${TEST_SRC})
    target_link_libraries(${TEST_NAME} PRIVATE pysync_core)
    
    # Register target with CTest
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
endforeach()

# OLD logic for compiling tests
# foreach(TEST_SRC ${TEST_SOURCES})
#     get_filename_component(TEST_NAME ${TEST_SRC} NAME_WE)
#     add_executable(${TEST_NAME} ${TEST_SRC})
#     target_link_libraries(${TEST_NAME} PRIVATE pysync_core)
# endforeach()


# TODO: fix below later on

# Define a standalone executable for testing embedded Python integration
#add_executable(embed_app src/cpp/main.cpp)

# Link both the core C++ library and pybind11 embedded runtime into the executable
#target_link_libraries(embed_app PRIVATE pysync_core pybind11::embed)