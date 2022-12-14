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

#ifndef MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_ARRAYS_SCATTER_ELEMENTS_GPU_KERNEL_H
#define MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_ARRAYS_SCATTER_ELEMENTS_GPU_KERNEL_H

#include <vector>
#include <algorithm>
#include <string>
#include <map>
#include <utility>
#include <memory>
#include "plugin/device/gpu/kernel/cuda_impl/cuda_ops/scatter_elements.cuh"
#include "plugin/device/gpu/kernel/gpu_kernel.h"
#include "plugin/device/gpu/kernel/gpu_kernel_factory.h"
#include "mindspore/core/ops/scatter_elements.h"
#include "mindspore/core/ops/scatter_add_with_axis.h"
#include "mindspore/ccsrc/kernel/common_utils.h"

namespace mindspore {
namespace kernel {
constexpr auto kUnKnown = "UnKnown";
constexpr auto kScatterElements = "ScatterElements";
constexpr auto kScatterAddWithAxis = "ScatterAddWithAxis";
class ScatterElementsGpuKernelMod : public NativeGpuKernelMod {
 public:
  ScatterElementsGpuKernelMod() {}
  ~ScatterElementsGpuKernelMod() { FreeResource(); }

  bool Init(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
            const std::vector<KernelTensorPtr> &outputs) override;

  int Resize(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
             const std::vector<KernelTensorPtr> &outputs,
             const std::map<uint32_t, tensor::TensorPtr> &inputsOnHost) override;

  bool Launch(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &workspace,
              const std::vector<AddressPtr> &outputs, void *stream_ptr) override {
    return kernel_func_(this, inputs, workspace, outputs, stream_ptr);
  }

 protected:
  void ResetResource();
  void MallocResource();
  void FreeResource();
  void InitSizeLists();
  std::vector<KernelAttr> GetOpSupport() override;
  void GetOpTypeAndFuncType(const BaseOperatorPtr &base_operator);
  void GetSize();
  int ShapeCheck();
  int AxisCheck();

  template <typename T, typename S>
  bool LaunchKernel(const std::vector<AddressPtr> &inputs, const std::vector<AddressPtr> &workspace,
                    const std::vector<AddressPtr> &outputs, void *stream_ptr);
  using ScatterElementsFunc =
    std::function<bool(ScatterElementsGpuKernelMod *, const std::vector<kernel::AddressPtr> &,
                       const std::vector<kernel::AddressPtr> &, const std::vector<kernel::AddressPtr> &, void *)>;

 private:
  std::string kernel_name_{};
  BaseOperatorPtr kernel_ptr_{nullptr};
  ScatterElementsFunc kernel_func_;
  ScatterElementsReductionType reduction_type_{REDCUTION_INVALID_TYPE};
  static std::vector<std::pair<KernelAttr, ScatterElementsFunc>> func_list_;

  bool sync_resource_ = false;
  bool update_input_ = false;

  std::vector<size_t> updates_shape_;
  std::vector<size_t> indices_shape_;
  std::vector<size_t> input_shape_;
  std::vector<size_t> output_shape_;
  std::vector<size_t> indices_stride_;
  std::vector<size_t> output_stride_;

  int64_t axis_{0};
  int input_axis_size_{0};
  size_t input_dims_{0};

  size_t input_byte_size_{1};
  size_t updates_byte_size_{1};
  size_t indices_byte_size_{1};

  size_t data_unit_size_{0};    /* sizeof(T) */
  size_t indices_unit_size_{0}; /* sizeof(S) */

  size_t *d_indices_stride_{nullptr};
  size_t *d_output_stride_{nullptr};
};
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_CCSRC_BACKEND_KERNEL_COMPILER_GPU_ARRAYS_TENSOR_TENSOR_SCATTER_ARITHMETIC_GPU_KERNEL_H
