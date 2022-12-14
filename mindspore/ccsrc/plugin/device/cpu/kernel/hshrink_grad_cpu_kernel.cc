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

#include "plugin/device/cpu/kernel/hshrink_grad_cpu_kernel.h"
#include <algorithm>
#include "mindspore/core/ops/grad/hshrink_grad.h"
#include "plugin/factory/ms_factory.h"

namespace mindspore {
namespace kernel {
namespace {
constexpr size_t kHShrinkGradInputsNum = 2;
constexpr size_t kHShrinkGradOutputsNum = 1;
}  // namespace
bool HShrinkGradCpuKernelMod::Init(const BaseOperatorPtr &base_operator, const std::vector<KernelTensorPtr> &inputs,
                                   const std::vector<KernelTensorPtr> &outputs) {
  kernel_name_ = base_operator->name();
  if (inputs.size() != kHShrinkGradInputsNum || outputs.size() != kHShrinkGradOutputsNum) {
    MS_LOG(ERROR) << kernel_name_ << ": input and output size should be " << kHShrinkGradInputsNum << " and "
                  << kHShrinkGradOutputsNum << ", but get " << inputs.size() << " and " << outputs.size();
    return false;
  }

  auto kernel_ptr = std::dynamic_pointer_cast<ops::HShrinkGrad>(base_operator);
  if (!kernel_ptr) {
    MS_LOG(ERROR) << "Cast HShrinkGrad ops failed!";
    return false;
  }
  lambd_ = kernel_ptr->get_lambd();

  if (!MatchKernelFunc(base_operator, inputs, outputs)) {
    return false;
  }

  return true;
}

template <typename T>
bool HShrinkGradCpuKernelMod::LaunchKernel(const std::vector<kernel::AddressPtr> &inputs,
                                           const std::vector<AddressPtr> &,
                                           const std::vector<kernel::AddressPtr> &outputs) {
  CHECK_KERNEL_INPUTS_NUM(inputs.size(), kHShrinkGradInputsNum, kernel_name_);
  CHECK_KERNEL_OUTPUTS_NUM(outputs.size(), kHShrinkGradOutputsNum, kernel_name_);
  auto *dy = reinterpret_cast<T *>(inputs[kIndex0]->addr);
  MS_ERROR_IF_NULL_W_RET_VAL(dy, false);
  auto *x = reinterpret_cast<T *>(inputs[kIndex1]->addr);
  MS_ERROR_IF_NULL_W_RET_VAL(x, false);
  auto *dx = reinterpret_cast<T *>(outputs[kIndex0]->addr);
  MS_ERROR_IF_NULL_W_RET_VAL(dx, false);

  size_t lens = inputs[0]->size > 0 ? static_cast<size_t>(inputs[0]->size / sizeof(T)) : 1;
  const float &lambd = this->lambd_;
  auto task = [dy, x, dx, &lambd](size_t start, size_t end) {
    const T positive_lambd = static_cast<T>(lambd);
    const T negative_lambd = static_cast<T>(-1 * lambd);
    const T zero = static_cast<T>(0);
    for (size_t i = start; i < end; i++) {
      dx[i] = (x[i] >= negative_lambd && x[i] <= positive_lambd) ? zero : dy[i];
    }
  };
  ParallelLaunchAutoSearch(task, lens, this, &parallel_search_info_);
  return true;
}

const std::vector<std::pair<KernelAttr, HShrinkGradCpuKernelMod::KernelRunFunc>> &HShrinkGradCpuKernelMod::GetFuncList()
  const {
  static const std::vector<std::pair<KernelAttr, HShrinkGradCpuKernelMod::KernelRunFunc>> func_list = {
    {KernelAttr().AddInputAttr(kNumberTypeFloat32).AddInputAttr(kNumberTypeFloat32).AddOutputAttr(kNumberTypeFloat32),
     &HShrinkGradCpuKernelMod::LaunchKernel<float>},
    {KernelAttr().AddInputAttr(kNumberTypeFloat16).AddInputAttr(kNumberTypeFloat16).AddOutputAttr(kNumberTypeFloat16),
     &HShrinkGradCpuKernelMod::LaunchKernel<float16>},
  };
  return func_list;
}

MS_KERNEL_FACTORY_REG(NativeCpuKernelMod, HShrinkGrad, HShrinkGradCpuKernelMod);
}  // namespace kernel
}  // namespace mindspore
