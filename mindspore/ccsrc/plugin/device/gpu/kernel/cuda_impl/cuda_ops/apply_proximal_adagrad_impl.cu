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

#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/apply_proximal_adagrad_impl.cuh"
#include <algorithm>
#include "include/cuda_fp16.h"

template <typename T>
__device__ __forceinline__ T RsqrtFunc(T x) {
  return rsqrt(x);
}

template <>
__device__ __forceinline__ half RsqrtFunc(half x) {
  return hrsqrt(x);
}

template <typename T>
__device__ __forceinline__ T AbsFunc(T x) {
  return abs(x);
}

template <>
__device__ __forceinline__ half AbsFunc(half x) {
  return abs(__half2float(x));
}

template <typename T>
__device__ __forceinline__ T MaxFunc(T x, T y) {
  return max(x, y);
}

template <>
__device__ __forceinline__ half MaxFunc(half x, half y) {
  return max(__half2float(x), __half2float(y));
}

template <typename T>
__device__ __forceinline__ T SinFunc(T x) {
  return sin(x);
}

template <>
__device__ __forceinline__ half SinFunc(half x) {
  return hsin(x);
}

template <typename T>
__global__ void CalApplyProximalAdagradKernel(const size_t input_elements, const T *lr, const T *l1, const T *l2,
                                              const T *grad, T *var, T *accum) {
  if (l1[0] > static_cast<T>(0.0)) {
    for (int pos = blockIdx.x * blockDim.x + threadIdx.x; pos < static_cast<int>(input_elements);
         pos += gridDim.x * blockDim.x) {
      accum[pos] += grad[pos] * grad[pos];
      auto learning_rate = lr[0] * RsqrtFunc(accum[pos]);
      auto prox_v = var[pos];
      prox_v -= grad[pos] * learning_rate;

      var[pos] = SinFunc(prox_v) * MaxFunc(AbsFunc(prox_v) - learning_rate * l1[0], static_cast<T>(0.0)) /
                 (static_cast<T>(1) + l2[0] * learning_rate);
    }
  } else {
    for (int pos = blockIdx.x * blockDim.x + threadIdx.x; pos < static_cast<int>(input_elements);
         pos += gridDim.x * blockDim.x) {
      accum[pos] += grad[pos] * grad[pos];
      auto learning_rate = lr[0] * RsqrtFunc(accum[pos]);
      auto prox_v = var[pos];
      prox_v -= grad[pos] * learning_rate;

      var[pos] = prox_v / (static_cast<T>(1) + l2[0] * learning_rate);
    }
  }
}

template <typename T>
void CalApplyProximalAdagrad(const size_t input_elements, const T *lr, const T *l1, const T *l2, const T *grad, T *var,
                             T *accum, const uint32_t &device_id, cudaStream_t cuda_stream) {
  CalApplyProximalAdagradKernel<<<CUDA_BLOCKS(device_id, input_elements), CUDA_THREADS(device_id), 0, cuda_stream>>>(
    input_elements, lr, l1, l2, grad, var, accum);
}

template CUDA_LIB_EXPORT void CalApplyProximalAdagrad<float>(const size_t size, const float *lr, const float *l1,
                                                             const float *l2, const float *grad, float *var,
                                                             float *accum, const uint32_t &device_id,
                                                             cudaStream_t cuda_stream);
template CUDA_LIB_EXPORT void CalApplyProximalAdagrad<half>(const size_t size, const half *lr, const half *l1,
                                                            const half *l2, const half *grad, half *var, half *accum,
                                                            const uint32_t &device_id, cudaStream_t cuda_stream);
