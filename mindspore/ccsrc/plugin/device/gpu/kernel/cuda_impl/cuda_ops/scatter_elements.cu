/**
 * Copyright 2022 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/scatter_elements.cuh"
#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/util.cuh"

template <typename T>
struct ReductionAssignment {
  __device__ void operator()(T *a, const T b) const { (*a) = b; }
};

template <typename T>
struct ReductionAdd {
  __device__ void operator()(T *a, const T b) const { return (void)MsAtomicAdd<T>(a, b); }
};

template <typename T, typename S, typename ReductionT>
__global__ void ScatterElementsKernel(const int input_dims, const int indices_size, const S *indices, const T *updates,
                                      T *output, const int64_t axis, const int64_t input_axis_size,
                                      const size_t *indices_stride, const size_t *output_stride,
                                      const ReductionT reduction_func) {
  int index = blockDim.x * blockIdx.x + threadIdx.x;
  if (index >= indices_size) {
    return;
  }

  int remain = index;
  int output_offset = 0;
  for (size_t i = 0; i < input_dims; ++i) {
    int output_dim_index = remain / indices_stride[i];
    remain %= indices_stride[i];
    if (i == axis) {
      output_dim_index = *(indices + index);
      if (output_dim_index >= input_axis_size || output_dim_index < -input_axis_size) {
        return;
      }
      if (output_dim_index < 0) {
        output_dim_index += input_axis_size;
      }
    }
    output_offset += output_stride[i] * output_dim_index;
  }
  reduction_func(output + output_offset, *(updates + index));
  return;
}

template <typename T, typename S>
void ScatterElements(const enum ScatterElementsReductionType reduction_type, const int input_dims,
                     const int indices_size, const S *indices, const T *updates, T *output, const int64_t axis,
                     const int64_t input_axis_size, const size_t *indices_stride, const size_t *output_stride,
                     const uint32_t &device_id, cudaStream_t stream) {
  switch (reduction_type) {
    case REDUCTION_ASSIGNMENT:
      return ScatterElementsKernel<T, S><<<CUDA_BLOCKS(device_id, indices_size), CUDA_THREADS(device_id), 0, stream>>>(
        input_dims, indices_size, indices, updates, output, axis, input_axis_size, indices_stride, output_stride,
        ReductionAssignment<T>());
    case REDUCTION_ADD:
      return ScatterElementsKernel<T, S><<<CUDA_BLOCKS(device_id, indices_size), CUDA_THREADS(device_id), 0, stream>>>(
        input_dims, indices_size, indices, updates, output, axis, input_axis_size, indices_stride, output_stride,
        ReductionAdd<T>());
    default:
      break;
  }
}

#define SCATTER_ELEMENTS_FUNC(T, S)                                                                       \
  template CUDA_LIB_EXPORT void ScatterElements(                                                          \
    const enum ScatterElementsReductionType reduction_type, const int input_dims, const int indices_size, \
    const S *indices, const T *updates, T *output, const int64_t axis, const int64_t input_axis_size,     \
    const size_t *indices_stride, const size_t *output_stride, const uint32_t &device_id, cudaStream_t stream)

#define SCATTER_ELEMENTS_INDEX_FUNC(T) \
  SCATTER_ELEMENTS_FUNC(T, int32_t);   \
  SCATTER_ELEMENTS_FUNC(T, int64_t);

SCATTER_ELEMENTS_INDEX_FUNC(half)
SCATTER_ELEMENTS_INDEX_FUNC(float)
SCATTER_ELEMENTS_INDEX_FUNC(double)
SCATTER_ELEMENTS_INDEX_FUNC(int8_t)
SCATTER_ELEMENTS_INDEX_FUNC(uint8_t)
SCATTER_ELEMENTS_INDEX_FUNC(int)
SCATTER_ELEMENTS_INDEX_FUNC(bool)
