cmake_minimum_required(VERSION 3.16)
project(SystemC_Test)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON) #...is required...
set(CMAKE_CXX_EXTENSIONS OFF) #...without compiler extensions like gnu++11

set (CMAKE_PREFIX_PATH /home/shiying/systemc)

include_directories(${CMAKE_PREFIX_PATH}/systemc/include)
include_directories(${PROJECT_SOURCE_DIR}/include)

# find_library(SystemC systemc HINTS "${CMAKE_PREFIX_PATH}/systemc-2.3.4/build/src")
link_directories(${CMAKE_PREFIX_PATH}/systemc/lib)
# find_package(SystemC REQUIRED)
# message(${CMAKE_PREFIX_PATH}/systemc/lib-linux64)
set (CMAKE_CXX_STANDARD ${SystemC_CXX_STANDARD})


# # aux_source_directory(. SRC_LIST)
set(SIM_PROCESS ${PROJECT_SOURCE_DIR}/Simulation_Process.cpp)
add_executable(Simulation_Process ${SIM_PROCESS})

set(SIM_STAGE ${PROJECT_SOURCE_DIR}/Simulation_Stage.cpp)
add_executable(Simulation_Stage ${SIM_STAGE})

set(SIM_CONCURRENCY ${PROJECT_SOURCE_DIR}/Concurrency.cpp)
add_executable(Concurrency ${SIM_CONCURRENCY})

set(TLM_block_transport ${PROJECT_SOURCE_DIR}/TLM_block_transport.cpp)
add_executable(TLM_block_transport ${TLM_block_transport})

set(TLM_DMI ${PROJECT_SOURCE_DIR}/TLM_DMI.cpp)
add_executable(TLMDMI ${TLM_DMI})

set(TLM_router ${PROJECT_SOURCE_DIR}/TLM_router.cpp)
add_executable(TLMrouter ${TLM_router})

set(TLM_nonblock_transport ${PROJECT_SOURCE_DIR}/TLM_nonblock_transport.cpp)
add_executable(TLM_nonblock_transport ${TLM_nonblock_transport})

set(TLM_simple_nonblock ${PROJECT_SOURCE_DIR}/TLM_simple_nonblock.cpp)
add_executable(TLM_simple_nonblock ${TLM_simple_nonblock})

target_link_libraries(Simulation_Process systemc)
target_link_libraries(Simulation_Stage systemc)
target_link_libraries(Concurrency systemc)
target_link_libraries(TLM_block_transport systemc)
target_link_libraries(TLMDMI systemc)
target_link_libraries(TLMrouter systemc)
target_link_libraries(TLM_nonblock_transport systemc)
target_link_libraries(TLM_simple_nonblock systemc)
