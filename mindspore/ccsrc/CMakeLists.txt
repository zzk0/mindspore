## common setting
include_directories(${CMAKE_SOURCE_DIR}/mindspore/core)
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_BINARY_DIR})
include_directories(${CMAKE_SOURCE_DIR}/mindspore/core/mindrt/include)
include_directories(${CMAKE_SOURCE_DIR}/mindspore/core/mindrt/src)


set(SERVER_FLATBUFFER_OUTPUT "${CMAKE_BINARY_DIR}/schema")
set(FBS_FILES
        ${CMAKE_CURRENT_SOURCE_DIR}/../schema/cipher.fbs
        ${CMAKE_CURRENT_SOURCE_DIR}/../schema/fl_job.fbs
        )
ms_build_flatbuffers(FBS_FILES ${CMAKE_CURRENT_SOURCE_DIR}../../schema generated_fbs_files ${SERVER_FLATBUFFER_OUTPUT})

if(ENABLE_D)
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/plugin/device/ascend/kernel/aicpu/aicpu_ops)
    add_subdirectory(plugin/device/ascend/kernel/aicpu/aicpu_ops)
endif()

if(ENABLE_CPU)
    if(${CMAKE_HOST_SYSTEM_PROCESSOR} MATCHES "aarch64")
        set(PLATFORM_ARM64 "on")
        set(X86_64_SIMD "off")
    elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
        set(X86_64_SIMD "off")
    elseif("${X86_64_SIMD}" STREQUAL "off" AND NOT ${ENABLE_ASAN})
        set(X86_64_SIMD "avx")
    endif()
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/plugin/device/cpu/kernel)
    add_subdirectory(plugin/device/cpu/kernel/nnacl)
endif()

if(NOT CMAKE_SYSTEM_NAME MATCHES "Darwin")
    link_directories(${CMAKE_SOURCE_DIR}/build/mindspore/graphengine)
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 \
        -Wno-delete-non-abstract-non-virtual-dtor -Wno-unused-private-field -Wno-overloaded-virtual \
        -Wno-unused-const-variable -Wno-pessimizing-move -Wno-range-loop-analysis -Wno-mismatched-tags \
        -Wno-c++11-narrowing")
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-attributes -DHAVE_SNPRINTF")
endif()

if(ENABLE_MPI)
    add_compile_definitions(ENABLE_MPI)
endif()

if(ENABLE_GPU)
    find_package(CUDA REQUIRED)
    find_package(Threads)
    if(${CUDA_VERSION} VERSION_LESS ${MS_REQUIRE_CUDA_VERSION})
        message(FATAL_ERROR "The minimum CUDA version ${MS_REQUIRE_CUDA_VERSION} is required, \
              but only CUDA ${CUDA_VERSION} found.")
    endif()
    enable_language(CUDA)
    if(NOT CUDA_PATH OR CUDA_PATH STREQUAL "")
        if(DEFINED ENV{CUDA_HOME} AND NOT $ENV{CUDA_HOME} STREQUAL "")
            set(CUDA_PATH $ENV{CUDA_HOME})
        else()
            set(CUDA_PATH ${CUDA_TOOLKIT_ROOT_DIR})
        endif()
    endif()

    if(DEFINED ENV{CUDNN_HOME} AND NOT $ENV{CUDNN_HOME} STREQUAL "")
        set(CUDNN_INCLUDE_DIR $ENV{CUDNN_HOME}/include)
        set(CUDNN_LIBRARY_DIR $ENV{CUDNN_HOME}/lib64)
        find_path(CUDNN_INCLUDE_PATH cudnn.h HINTS ${CUDNN_INCLUDE_DIR} NO_DEFAULT_PATH)
        find_library(CUDNN_LIBRARY_PATH "cudnn" HINTS ${CUDNN_LIBRARY_DIR} NO_DEFAULT_PATH)
        if(CUDNN_INCLUDE_PATH STREQUAL CUDNN_INCLUDE_PATH-NOTFOUND)
            message(FATAL_ERROR "Failed to find cudnn header file, please set environment variable CUDNN_HOME to \
                    cudnn installation position.")
        endif()
        if(CUDNN_LIBRARY_PATH STREQUAL CUDNN_LIBRARY_PATH-NOTFOUND)
            message(FATAL_ERROR "Failed to find cudnn library file, please set environment variable CUDNN_HOME to \
                    cudnn installation position.")
        endif()
    else()
        list(APPEND CMAKE_PREFIX_PATH  ${CUDA_TOOLKIT_ROOT_DIR})
        find_path(CUDNN_INCLUDE_PATH cudnn.h PATH_SUFFIXES cuda/inclulde include cuda)
        find_library(CUDNN_LIBRARY_PATH "cudnn" PATH_SUFFIXES cuda/lib64 lib64 lib cuda/lib lib/x86_64-linux-gnu)
        if(CUDNN_INCLUDE_PATH STREQUAL CUDNN_INCLUDE_PATH-NOTFOUND)
            message(FATAL_ERROR "Failed to find cudnn header file, if cudnn library is not installed, please put \
                    cudnn header file in cuda include path or user include path(eg. /usr/local/cuda/include; \
                    /usr/local/include; /usr/include), if cudnn library is installed in other position, please \
                    set environment variable CUDNN_HOME to cudnn installation position, there should be cudnn.h \
                    in {CUDNN_HOME}/include.")
        endif()
        if(CUDNN_LIBRARY_PATH STREQUAL CUDNN_LIBRARY_PATH-NOTFOUND)
            message(FATAL_ERROR "Failed to find cudnn library file, if cudnn library is not installed, please put \
                    cudnn library file in cuda library path or user library path(eg. /usr/local/cuda/lib64; \
                    /usr/local/lib64; /usr/lib64; /usr/local/lib; /usr/lib), if cudnn library is installed in other \
                    position, please set environment variable CUDNN_HOME to cudnn installation position, there should \
                    be cudnn library file in {CUDNN_HOME}/lib64.")
        endif()
    endif()

    if(NOT CUPTI_INCLUDE_DIRS OR CUPTI_INCLUDE_DIRS STREQUAL "")
        set(CUPTI_INCLUDE_DIRS  ${CUDA_PATH}/extras/CUPTI/include)
    endif()
    message("CUDA_PATH: ${CUDA_PATH}")
    message("CUDA_INCLUDE_DIRS: ${CUDA_INCLUDE_DIRS}")
    message("CUDNN_INCLUDE_PATH: ${CUDNN_INCLUDE_PATH}")
    message("CUDNN_LIBRARY_PATH: ${CUDNN_LIBRARY_PATH}")
    message("CUPTI_INCLUDE_DIRS: ${CUPTI_INCLUDE_DIRS}")
    include_directories(${CUDNN_INCLUDE_PATH} ${CUDA_PATH} ${CUDA_INCLUDE_DIRS} ${CUPTI_INCLUDE_DIRS})

    file(GLOB_RECURSE GPU_SRC_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
            "plugin/device/gpu/hal/device/*.cc"
            "plugin/device/gpu/hal/device/*.cu"
            "plugin/device/gpu/kernel/*.cu"
            )

    list(REMOVE_ITEM GPU_SRC_LIST "plugin/device/gpu/kernel/cuda_impl/cuda_ops/*.cu")

    list(APPEND CUDA_NVCC_FLAGS -arch=sm_53 --expt-relaxed-constexpr)
    if("${CMAKE_BUILD_TYPE}" STREQUAL "Debug")
        list(APPEND CUDA_NVCC_FLAGS -G)
        message("CUDA_NVCC_FLAGS" ${CUDA_NVCC_FLAGS})
    endif()

    list(REMOVE_ITEM GPU_SRC_LIST "plugin/device/gpu/hal/device/blocking_queue.cc"
            "plugin/device/gpu/hal/device/gpu_buffer_mgr.cc")
    list(REMOVE_ITEM GPU_SRC_LIST "plugin/device/gpu/hal/device/mpi/mpi_initializer.cc"
                                  "plugin/device/gpu/hal/device/distribution/collective_wrapper.cc"
                                  "plugin/device/gpu/hal/device/distribution/mpi_wrapper.cc"
                                  "plugin/device/gpu/hal/device/distribution/nccl_wrapper.cc"
                                  "plugin/device/gpu/hal/device/trt_loader.cc")

    if(NOT ${TENSORRT_HOME} STREQUAL "")
        find_path(TENSORRT_HOME_INCLUDE NvInfer.h HINTS ${TENSORRT_HOME}/include)
        if(TENSORRT_HOME_INCLUDE STREQUAL TENSORRT_HOME_INCLUDE-NOTFOUND)
          message(FATAL_ERROR "Tensor-RT dir not exist ${TENSORRT_HOME}")
        endif()
        message("Enable GPU inference. Tensor-RT include dir: ${TENSORRT_HOME_INCLUDE}")
        set(ENABLE_GPU_INFER TRUE)
        add_compile_definitions(ENABLE_GPU_INFER)
        include_directories(${TENSORRT_HOME_INCLUDE})
        list(APPEND GPU_SRC_LIST ${CMAKE_CURRENT_SOURCE_DIR}/plugin/device/gpu/hal/device/trt_loader.cc)
    endif()

    set(NVCC_TMP_CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS})
    if(${CUDA_VERSION} VERSION_LESS 11.0)
        string(REPLACE "-std=c++17" "-std=c++11" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    else()
        string(REPLACE "-std=c++17" "-std=c++14" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    endif()
    set_property(SOURCE ${GPU_SRC_LIST} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_DEVICE)
    cuda_add_library(gpu_cuda_lib STATIC ${GPU_SRC_LIST})
    set(CMAKE_CXX_FLAGS ${NVCC_TMP_CMAKE_CXX_FLAGS})
    add_compile_definitions(ENABLE_GPU)
    add_dependencies(gpu_cuda_lib proto_input)
    add_subdirectory(plugin/device/gpu/kernel/cuda_impl/cuda_ops)
endif()


## make protobuf files
file(GLOB ONNX_PROTO "" ${CMAKE_SOURCE_DIR}/third_party/proto/onnx/onnx.proto)
message("onnx proto path is :" ${ONNX_PROTO})
ms_protobuf_generate(ONNX_PROTO_SRCS ONNX_PROTO_HDRS ${ONNX_PROTO})
list(APPEND MINDSPORE_PROTO_LIST ${ONNX_PROTO_SRCS})

include_directories("${CMAKE_BINARY_DIR}/ps/core")
file(GLOB_RECURSE COMM_PROTO_IN RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "ps/core/protos/*.proto")
ms_protobuf_generate(COMM_PROTO_SRCS COMM_PROTO_HDRS ${COMM_PROTO_IN})
list(APPEND MINDSPORE_PROTO_LIST ${COMM_PROTO_SRCS})

include_directories("${CMAKE_BINARY_DIR}/distributed/cluster/topology")
file(GLOB_RECURSE DISTRIBUTED_CLUSTER_TOPOLOGY RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
  "distributed/cluster/topology/protocol/*.proto")
ms_protobuf_generate(DISTRIBUTED_CLUSTER_TOPOLOGY_SRCS DISTRIBUTED_CLUSTER_TOPOLOGY_HDRS
  ${DISTRIBUTED_CLUSTER_TOPOLOGY})
list(APPEND MINDSPORE_PROTO_LIST ${DISTRIBUTED_CLUSTER_TOPOLOGY_SRCS})

if(NOT ENABLE_SECURITY)
    include_directories("${CMAKE_BINARY_DIR}/profiler/device/ascend")
    file(GLOB_RECURSE PROFILER_PROTO_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
      "profiler/device/ascend/memory_profiling.proto")
    ms_protobuf_generate_py(PROFILER_MEM_PROTO_PY PROFILER_MEM_PROTO_HDRS_PY PROFILER_MEM_PROTO_PYS
      ${PROFILER_PROTO_LIST})
    list(APPEND MINDSPORE_PROTO_LIST ${PROFILER_MEM_PROTO_PY})
endif()

if(ENABLE_DEBUGGER)
    # debugger: compile proto files
    include_directories("${CMAKE_BINARY_DIR}/debug/debugger")
    file(GLOB_RECURSE DEBUGGER_PROTO_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "debug/debugger/debug_graph.proto")
    ms_protobuf_generate(DEBUGGER_PROTO_SRCS DEBUGGER_PROTO_HDRS ${DEBUGGER_PROTO_LIST})
    file(GLOB_RECURSE DEBUGGER_GRPC_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "debug/debugger/debug_grpc.proto")
    ms_grpc_generate(DEBUGGER_GRPC_SRCS DEBUGGER_GRPC_HDRS ${DEBUGGER_GRPC_LIST})
    file(GLOB_RECURSE DUMP_DATA_PROTO_LIST RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "debug/debugger/dump_data.proto")
    ms_protobuf_generate(DUMP_DATA_PROTO_SRCS DUMP_DATA_PROTO_HDRS ${DUMP_DATA_PROTO_LIST})
    list(APPEND MINDSPORE_PROTO_LIST ${DEBUGGER_PROTO_SRCS})
    list(APPEND MINDSPORE_PROTO_LIST ${DEBUGGER_GRPC_SRCS})
    list(APPEND MINDSPORE_PROTO_LIST ${DUMP_DATA_PROTO_SRCS})
endif()

if(ENABLE_DUMP_PROTO)
    include_directories(${CMAKE_BINARY_DIR})

    file(GLOB_RECURSE PROTO_PY RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
        "utils/anf_ir.proto"
        "utils/summary.proto"
        "utils/lineage.proto"
        "utils/checkpoint.proto"
        "utils/print.proto"
        "utils/node_strategy.proto"
        "utils/profiling_parallel.proto"
    )
    ms_protobuf_generate_py(PY_SRCS PY_HDRS PY_PYS ${PROTO_PY})

    list(APPEND MINDSPORE_PROTO_LIST ${PROTO_SRCS})
    list(APPEND MINDSPORE_PROTO_LIST ${PY_SRCS})
endif()

if(MODE_ASCEND_ALL)
    include_directories("${CMAKE_BINARY_DIR}/plugin/device/ascend/kernel/aicpu")
    file(GLOB_RECURSE PROTO_IN RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "plugin/device/ascend/kernel/aicpu/proto/*.proto")
    ms_protobuf_generate(PROTOSRCS PROTOHDRS ${PROTO_IN})

    file(GLOB_RECURSE PROTO_DUMP RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
            "plugin/device/ascend/hal/device/dump/proto/*.proto")
    ms_protobuf_generate(DUMP_PROTOSRCS PROTOHDRS ${PROTO_DUMP})

    list(APPEND MINDSPORE_PROTO_LIST ${PROTOSRCS})
    list(APPEND MINDSPORE_PROTO_LIST ${PREDICT_PROTOSRCS})
    list(APPEND MINDSPORE_PROTO_LIST ${DUMP_PROTOSRCS})

    add_compile_definitions(ENABLE_D)
endif()

# core/mindir.proto
file(GLOB_RECURSE CORE_PROTO_IN ${CMAKE_SOURCE_DIR}/mindspore/core/proto/*.proto)
ms_protobuf_generate(CORE_PROTO_SRC CORE_PROTO_HDR ${CORE_PROTO_IN})
list(APPEND MINDSPORE_PROTO_LIST ${CORE_PROTO_SRC})

include_directories("${CMAKE_BINARY_DIR}/runtime/graph_scheduler/actor/rpc")
file(GLOB_RECURSE RPC_PROTO RELATIVE ${CMAKE_CURRENT_SOURCE_DIR}
  "runtime/graph_scheduler/actor/rpc/*.proto")
ms_protobuf_generate(RPC_PROTO_SRCS RPC_PROTO_HDRS ${RPC_PROTO})
list(APPEND MINDSPORE_PROTO_LIST ${RPC_PROTO_SRCS})

if(MINDSPORE_PROTO_LIST)
    add_library(proto_input STATIC ${MINDSPORE_PROTO_LIST})
    set_target_properties(proto_input PROPERTIES COMPILE_FLAGS "-Wno-unused-variable -Wno-array-bounds")
endif()

## make sub objects
set(SUB_COMP
        transform/express_ir
        frontend/optimizer
        frontend/parallel
        frontend/operator
        pipeline/jit
        pipeline/pynative
        pybind_api
)

foreach(_comp ${SUB_COMP})
    add_subdirectory(${_comp})
    string(REPLACE "/" "_" sub ${_comp})
    if(TARGET _mindspore_${sub}_obj)
        list(APPEND SUB_OBJECTS_SRC $<TARGET_OBJECTS:_mindspore_${sub}_obj>)
        add_dependencies(_mindspore_${sub}_obj proto_input mindspore_core)
    endif()
endforeach()

set_property(SOURCE ${SUB_OBJECTS_SRC} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_ME)
add_library(mindspore STATIC ${SUB_OBJECTS_SRC})

set(COMMON_SUB_COMP
        transform/graph_ir
        utils
        common
        common/debug
        )

foreach(_comp ${COMMON_SUB_COMP})
    add_subdirectory(${_comp})
    string(REPLACE "/" "_" sub ${_comp})
    if(TARGET _mindspore_${sub}_obj)
        list(APPEND COMMON_SUB_OBJECTS_SRC $<TARGET_OBJECTS:_mindspore_${sub}_obj>)
        add_dependencies(_mindspore_${sub}_obj proto_input mindspore_core)
        if(CMAKE_SYSTEM_NAME MATCHES "Windows")
            target_compile_definitions(_mindspore_${sub}_obj PRIVATE COMMON_DLL)
        endif()
    endif()
endforeach()

add_library(mindspore_common SHARED ${COMMON_SUB_OBJECTS_SRC})
target_link_libraries(mindspore_common PRIVATE mindspore_core proto_input mindspore::protobuf)
set_target_properties(mindspore_common PROPERTIES INSTALL_RPATH $ORIGIN)
if(CMAKE_SYSTEM_NAME MATCHES "Windows" OR CMAKE_SYSTEM_NAME MATCHES "Darwin")
    target_link_libraries(mindspore_common PRIVATE mindspore::pybind11_module)
endif()

target_link_libraries(mindspore PUBLIC securec mindspore::flatbuffers)

if(NOT WIN32)
  target_link_libraries(mindspore PUBLIC dl)
endif()

set(BACKEND_SUB_COMP
        debug
        profiler
        ps
        fl
        distributed
        kernel
        common/mem_reuse
        backend/common/optimizer
        backend/common/pass
        backend/common/session
        backend/common/somas
        common/graph_kernel
        backend/graph_compiler
        runtime/collective
        runtime/device
        runtime/graph_scheduler
        runtime/hardware
        runtime/pynative
        plugin/device/ascend/hal/device
        plugin/device/ascend/hal/hardware
        plugin/device/ascend/hal/hccl_adapter
        plugin/device/ascend/kernel
        plugin/device/ascend/optimizer
        plugin/device/cpu/hal/device
        plugin/device/cpu/hal/hardware
        plugin/device/cpu/kernel
        plugin/device/cpu/optimizer
        plugin/device/gpu/hal/device
        plugin/device/gpu/hal/hardware
        plugin/device/gpu/kernel
        plugin/device/gpu/optimizer
        )

foreach(_comp ${BACKEND_SUB_COMP})
    add_subdirectory(${_comp})
    string(REPLACE "/" "_" sub ${_comp})
    if(TARGET _mindspore_${sub}_obj)
        list(APPEND BACKEND_SUB_OBJECTS_SRC $<TARGET_OBJECTS:_mindspore_${sub}_obj>)
        add_dependencies(_mindspore_${sub}_obj proto_input)
        if(CMAKE_SYSTEM_NAME MATCHES "Windows")
            target_compile_definitions(_mindspore_${sub}_obj PRIVATE BACKEND_DLL)
        endif()
    endif()
endforeach()

if(ENABLE_TEST OR ENABLE_TESTCASES)
    include_directories(${CMAKE_BINARY_DIR})
    list(APPEND STUB_BACKEND_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/fl/fl_stub.cc)
    list(APPEND STUB_BACKEND_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/fl/server_stub.cc)
    list(APPEND STUB_BACKEND_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ps/ps_core_stub.cc)
    add_library(stub_backend_obj OBJECT ${STUB_BACKEND_SOURCE})
    list(APPEND BACKEND_SUB_OBJECTS_SRC $<TARGET_OBJECTS:stub_backend_obj>)
endif()

set_property(SOURCE ${BACKEND_SUB_OBJECTS_SRC} PROPERTY COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_ME)
add_library(mindspore_backend SHARED ${BACKEND_SUB_OBJECTS_SRC})
if(MODE_ASCEND_ACL)
    add_library(mindspore_backend_static STATIC ${BACKEND_SUB_OBJECTS_SRC})
endif()
if(CMAKE_SYSTEM_NAME MATCHES "Windows")
    target_link_libraries(mindspore_backend PRIVATE mindspore::pybind11_module)
endif()
target_link_libraries(mindspore_backend PRIVATE mindspore_core mindspore_common proto_input mindspore::protobuf)
target_link_libraries(mindspore_backend PRIVATE securec)
if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set_target_properties(mindspore_backend PROPERTIES MACOSX_RPATH ON)
    set_target_properties(mindspore_backend PROPERTIES INSTALL_RPATH @loader_path)
else()
    set_target_properties(mindspore_backend PROPERTIES INSTALL_RPATH $ORIGIN)
endif()

if(ENABLE_CPU)
    target_link_libraries(mindspore_backend PRIVATE mindspore::dnnl mindspore::mkldnn nnacl)
endif()
if(ENABLE_GPU)
    message("add gpu lib to mindspore_backend")
    target_link_libraries(mindspore_backend PRIVATE gpu_cuda_lib gpu_queue cublas cuda_ops
            ${CUDA_PATH}/lib64/libcurand.so
            ${CUDNN_LIBRARY_PATH}
            ${CUDA_PATH}/lib64/libcudart.so
            ${CUDA_PATH}/lib64/stubs/libcuda.so
            ${CUDA_PATH}/lib64/libcusolver.so
            ${CUDA_PATH}/lib64/libcufft.so
            ${CUDA_PATH}/lib64/libcusparse.so)
endif()

if(NOT WIN32)
    target_link_libraries(mindspore_backend PRIVATE mindspore::ssl mindspore::crypto)
endif()

if(ENABLE_DEBUGGER)
    # debugger: link grpc
    if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
        target_link_libraries(mindspore_backend PRIVATE mindspore::grpc++)
    else()
        target_link_libraries(mindspore_backend PRIVATE -Wl,--no-as-needed mindspore::grpc++)
    endif()
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    target_link_libraries(mindspore_backend PRIVATE mindspore::event mindspore::event_pthreads mindspore::event_openssl
            mindspore::event_core ps_cache)
elseif(ENABLE_CPU AND NOT WIN32)
    target_link_libraries(mindspore_backend PRIVATE mindspore::event mindspore::event_pthreads mindspore::event_openssl
            -Wl,--no-as-needed mindspore::event_core ps_cache)
endif()

if(MODE_ASCEND_ALL OR MODE_ASCEND_ACL)
    # common env paths
    if(DEFINED ENV{D_LINK_PATH})
        if(CMAKE_HOST_SYSTEM_PROCESSOR MATCHES "aarch64")
            MESSAGE("system processor matches aarch64")
            set(D_LIB_PATH $ENV{D_LINK_PATH}/aarch64)
        elseif(CMAKE_HOST_SYSTEM_PROCESSOR MATCHES "x86_64")
            MESSAGE("system processor matches x86_64")
            set(D_LIB_PATH $ENV{D_LINK_PATH}/x86_64)
        else()
            MESSAGE("system ${CMAKE_HOST_SYSTEM_PROCESSOR} not support")
        endif()
    else()
        MESSAGE("use system default lib")
        if(DEFINED ENV{ASCEND_CUSTOM_PATH})
            set(ASCEND_PATH $ENV{ASCEND_CUSTOM_PATH})
        else()
            set(ASCEND_PATH /usr/local/Ascend)
        endif()
        set(ASCEND_DRIVER_PATH ${ASCEND_PATH}/driver/lib64/common)
        set(ASCEND_DRIVER_BACK_PATH ${ASCEND_PATH}/driver/lib64/driver)
        set(ASCEND_RUNTIME_PATH ${ASCEND_PATH}/fwkacllib/lib64)
        set(ASCEND_RUNTIME_NEW_PATH ${ASCEND_PATH}/lib64)
        set(ASCEND_OPP_PATH ${ASCEND_PATH}/opp/op_impl/built-in/ai_core/tbe/op_tiling)
        set(ASCEND_CANN_RUNTIME_PATH ${ASCEND_PATH}/latest/fwkacllib/lib64)
        set(ASCEND_CANN_RUNTIME_NEW_PATH ${ASCEND_PATH}/latest/lib64)
        set(ASCEND_CANN_OPP_PATH ${ASCEND_PATH}/latest/opp/op_impl/built-in/ai_core/tbe/op_tiling)
        set(ASCEND_TOOLKIT_RUNTIME_PATH ${ASCEND_PATH}/ascend-toolkit/latest/fwkacllib/lib64)
        set(ASCEND_TOOLKIT_RUNTIME_NEW_PATH ${ASCEND_PATH}/ascend-toolkit/latest/lib64)
        set(ASCEND_TOOLKIT_OPP_PATH ${ASCEND_PATH}/ascend-toolkit/latest/opp/op_impl/built-in/ai_core/tbe/op_tiling)
    endif()
endif()

if(ENABLE_D)
    find_library(GE_RUNNER ge_runner ${ASCEND_RUNTIME_PATH} ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(GRAPH graph ${ASCEND_RUNTIME_PATH} ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(HCCL hccl ${ASCEND_RUNTIME_PATH} ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_NEW_PATH})
    target_link_libraries(mindspore_backend PUBLIC ${GE_RUNNER} ${GRAPH} ${HCCL})
endif()

if(MODE_ASCEND_ALL)
    MESSAGE("USE DAV LIB PATH: ${ASCEND_PATH}")
    find_library(ERROR_MANAGER error_manager ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(RUNTIME_LIB runtime ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(TSDCLIENT tsdclient HINTS ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH} ${ASCEND_DRIVER_BACK_PATH})
    find_library(DATATRANSFER datatransfer HINTS ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH} ${ASCEND_DRIVER_BACK_PATH})
    find_library(PROFILING msprofiler ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(ACL ascendcl ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(ACL_TDT_CHANNEL acl_tdt_channel ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(PLATFORM platform ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    find_library(OPTILING optiling ${ASCEND_OPP_PATH} ${ASCEND_TOOLKIT_OPP_PATH} ${ASCEND_CANN_OPP_PATH})
    find_library(OPT_FEATURE opt_feature ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})

    target_link_libraries(mindspore_backend PUBLIC ${RUNTIME_LIB} ${TSDCLIENT} ${DATATRANSFER} ${ERROR_MANAGER}
            -Wl,--no-as-needed ${OPTILING} ${PLATFORM} ${ACL} ${ACL_TDT_CHANNEL} ${OPT_FEATURE} ${PROFILING})
    target_link_libraries(mindspore PUBLIC -Wl,--start-group proto_input mindspore::protobuf -Wl,--end-group)
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
    target_link_libraries(mindspore PUBLIC -Wl,--start-group proto_input mindspore::protobuf mindspore::sentencepiece
                        -Wl,--end-group)
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    target_link_libraries(mindspore PUBLIC -Wl proto_input mindspore::protobuf mindspore::sentencepiece -Wl)
else()
    target_link_libraries(mindspore PUBLIC -Wl,--start-group proto_input mindspore::protobuf -Wl,--end-group)
endif()

# set c_expression building
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set_property(SOURCE "pipeline/jit/init.cc" PROPERTY
            COMPILE_DEFINITIONS SUBMODULE_ID=mindspore::SubModuleId::SM_PIPELINE)
pybind11_add_module(_c_expression NO_EXTRAS "pipeline/jit/init.cc" NO_EXTRAS)

MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM}")
if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    target_link_options(_c_expression PRIVATE -Wl,-init,mindspore_log_init)
    set(ORIGIN_PATH $ORIGIN)
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set_target_properties(_c_expression PROPERTIES MACOSX_RPATH ON)
    set(ORIGIN_PATH @loader_path)
elseif(CMAKE_SYSTEM_NAME MATCHES "Windows")
    set(ORIGIN_PATH $ORIGIN)
else()
    MESSAGE(FATAL_ERROR "other platform: ${CMAKE_SYSTEM_NAME}")
endif()

if(MODE_ASCEND_ALL)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/nnae/latest/fwkacllib/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/nnae/latest/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/ascend-toolkit/latest/fwkacllib/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/ascend-toolkit/latest/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/fwkacllib/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/latest/fwkacllib/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/latest/lib64)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/opp/op_impl/built-in/ai_core/tbe/op_tiling)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/nnae/latest/opp/op_impl/built-in/ai_core/tbe/op_tiling)
    set(MINDSPORE_RPATH
        ${MINDSPORE_RPATH}:/usr/local/Ascend/ascend-toolkit/latest/opp/op_impl/built-in/ai_core/tbe/op_tiling)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:/usr/local/Ascend/latest/opp/op_impl/built-in/ai_core/tbe/op_tiling)
elseif(ENABLE_GPU)
    set(MINDSPORE_RPATH ${MINDSPORE_RPATH}:${CUDA_PATH}/lib64)
endif()
set(MINDSPORE_RPATH ${ORIGIN_PATH}/lib:${MINDSPORE_RPATH})
set_target_properties(_c_expression PROPERTIES INSTALL_RPATH ${MINDSPORE_RPATH})

if(CMAKE_SYSTEM_NAME MATCHES "Windows")
    target_link_libraries(mindspore PUBLIC mindspore::pybind11_module)
    target_link_libraries(_c_expression PRIVATE -Wl,--whole-archive mindspore -Wl,--no-whole-archive mindspore_core
        mindspore_common mindspore_backend)
elseif(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    target_link_libraries(mindspore PUBLIC proto_input mindspore::protobuf mindspore::eigen mindspore::json)
    target_link_libraries(_c_expression PRIVATE -Wl,-all_load mindspore proto_input -Wl,-noall_load mindspore_core
        mindspore_common mindspore_backend)
    target_link_libraries(_c_expression PRIVATE mindspore::pybind11_module)
else()
    if(ENABLE_CPU AND NOT WIN32)
        target_link_libraries(mindspore PUBLIC proto_input mindspore::protobuf mindspore::eigen mindspore::json)
        if(${ENABLE_IBVERBS} STREQUAL "ON")
            target_link_libraries(mindspore PUBLIC ibverbs rdmacm)
        endif()
    endif()
    target_link_libraries(_c_expression PRIVATE -Wl,--whole-archive mindspore proto_input -Wl,--no-whole-archive
            mindspore_core mindspore_common mindspore_backend)
    target_link_libraries(_c_expression PRIVATE mindspore::pybind11_module)
endif()

if(USE_GLOG)
    target_link_libraries(_c_expression PRIVATE mindspore::glog)
endif()

if(ENABLE_GPU)
    if(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
        target_link_libraries(_c_expression PRIVATE mindspore::ssl mindspore::crypto)
    endif()
    if(ENABLE_MPI)
        set_target_properties(_ms_mpi PROPERTIES INSTALL_RPATH ${MINDSPORE_RPATH})
        set_target_properties(nvidia_collective PROPERTIES INSTALL_RPATH ${ORIGIN_PATH})
        set_target_properties(gpu_collective PROPERTIES INSTALL_RPATH ${ORIGIN_PATH})
    endif()
endif()

if(CMAKE_SYSTEM_NAME MATCHES "Darwin")
    set(CMAKE_MACOSX_RPATH 1)
    set(CMAKE_INSTALL_RPATH "@loader_path/lib;@loader_path")
    set_target_properties(_c_expression PROPERTIES INSTALL_RPATH "${CMAKE_INSTALL_RPATH}")
endif()

if(ENABLE_CPU)
    target_link_libraries(_c_expression PRIVATE mindspore::dnnl mindspore::mkldnn nnacl)
endif()

if(ENABLE_MINDDATA)
    add_subdirectory(minddata/mindrecord)
    add_subdirectory(minddata/dataset)
endif()

if(MODE_ASCEND_ALL)
    find_library(adump_server libadump_server.a ${ASCEND_RUNTIME_PATH} ${ASCEND_TOOLKIT_RUNTIME_PATH}
                ${ASCEND_CANN_RUNTIME_PATH} ${ASCEND_RUNTIME_NEW_PATH}
                ${ASCEND_TOOLKIT_RUNTIME_NEW_PATH} ${ASCEND_CANN_RUNTIME_NEW_PATH})
    target_link_libraries(_c_expression PRIVATE ${adump_server})
endif()

if(ENABLE_D)
    if(ENABLE_MPI)
        set_target_properties(_ascend_mpi PROPERTIES INSTALL_RPATH ${MINDSPORE_RPATH})
    endif()
endif()

if(ENABLE_TEST OR ENABLE_TESTCASES)
    include_directories(${CMAKE_BINARY_DIR})
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ge/ge_operator_stub.cc)
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/transform/util.cc)
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/pipeline/action_stub.cc)
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ps/ps_stub.cc)
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/cluster/cluster_stub.cc)
    list(APPEND STUB_COMMON_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/profiling/parallel_strategy_profiling_stub.cc)

    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/fl/fl_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ps/ps_core_stub.cc)

    add_library(stub_common STATIC ${STUB_COMMON_SOURCE})
    target_link_libraries(mindspore_common PUBLIC stub_common)

    add_library(expression_ STATIC ${EXPRESSION_STUB_SOURCE})
    target_link_libraries(_c_expression PUBLIC expression_)
endif()

if(NOT ENABLE_TESTCASES AND NOT (ENABLE_D OR ENABLE_CPU OR ENABLE_GPU))
    include_directories(${CMAKE_BINARY_DIR})
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/cluster/cluster_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ps/ps_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/fl/fl_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/fl/server_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/ps/ps_core_stub.cc)
    list(APPEND EXPRESSION_STUB_SOURCE
            ${CMAKE_SOURCE_DIR}/tests/ut/cpp/stub/profiling/parallel_strategy_profiling_stub.cc)

    add_library(expression_ STATIC ${EXPRESSION_STUB_SOURCE})
    target_link_libraries(_c_expression PUBLIC expression_)
endif()
add_subdirectory(cxx_api)
