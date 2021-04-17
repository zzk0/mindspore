/**
 * Copyright 2021 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_LITE_SRC_REGISTER_KERNEL_H_
#define MINDSPORE_LITE_SRC_REGISTER_KERNEL_H_

#include <string>
#include <vector>
#include "schema/ops_generated.h"
#include "src/lite_kernel.h"

namespace mindspore {
namespace kernel {
typedef kernel::Kernel *(*CreateKernel)(const std::vector<tensor::MSTensor *> &inputs,
                                        const std::vector<tensor::MSTensor *> &outputs,
                                        const schema::Primitive *primitive, const lite::Context *ctx);
class RegisterKernel {
 public:
  static RegisterKernel *GetInstance();
  int RegKernel(const std::string &arch, const std::string &provider, TypeId data_type, int type, CreateKernel creator);
  int RegCustomKernel(const std::string &arch, const std::string &provider, TypeId data_type, const std::string &type,
                      CreateKernel creator);
};

class KernelReg {
 public:
  ~KernelReg() = default;

  KernelReg(const std::string &arch, const std::string &provider, TypeId data_type, int op_type, CreateKernel creator) {
    RegisterKernel::GetInstance()->RegKernel(arch, provider, data_type, op_type, creator);
  }

  KernelReg(const std::string &arch, const std::string &provider, TypeId data_type, const std::string &op_type,
            CreateKernel creator) {
    RegisterKernel::GetInstance()->RegCustomKernel(arch, provider, data_type, op_type, creator);
  }
};

#define REGISTER_KERNEL(arch, provider, data_type, op_type, creator) \
  static KernelReg g_##arch##provider##data_type##op_type##kernelReg(arch, provider, data_type, op_type, creator);

#define REGISTER_CUSTOM_KERNEL(arch, provider, data_type, op_type, creator) \
  static KernelReg g_##arch##provider##data_type##op_type##kernelReg(arch, provider, data_type, op_type, creator);
}  // namespace kernel
}  // namespace mindspore

#endif  // MINDSPORE_LITE_SRC_REGISTER_KERNEL_H_
