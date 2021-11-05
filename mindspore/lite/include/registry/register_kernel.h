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

#ifndef MINDSPORE_LITE_INCLUDE_REGISTRY_REGISTER_KERNEL_H_
#define MINDSPORE_LITE_INCLUDE_REGISTRY_REGISTER_KERNEL_H_

#include <set>
#include <string>
#include <vector>
#include <memory>
#include "schema/model_generated.h"
#include "include/api/context.h"
#include "include/api/types.h"
#include "include/api/kernel.h"
#include "include/api/data_type.h"
#include "include/api/status.h"

namespace mindspore {
namespace registry {
/// \brief KernelDesc defined kernel's basic attribute.
struct KernelDesc {
  DataType data_type;   /**< kernel data type argument */
  int type;             /**< op type argument */
  std::string arch;     /**< deviceType argument */
  std::string provider; /**< user identification argument */
};

/// \brief KernelDesc defined kernel's basic attribute.
struct KernelDescHelper {
  DataType data_type;         /**< kernel data type argument */
  int type;                   /**< op type argument */
  std::vector<char> arch;     /**< deviceType argument */
  std::vector<char> provider; /**< user identification argument */
};

/// \brief CreateKernel Defined a functor to create a kernel.
///
/// \param[in] inputs Define input tensors of kernel.
/// \param[in] outputs Define output tensors of kernel.
/// \param[in] primitive Define attributes of op.
/// \param[in] ctx Define for holding environment variables during runtime.
///
/// \return Smart Pointer of kernel.
using CreateKernel = std::function<std::shared_ptr<kernel::Kernel>(
  const std::vector<MSTensor> &inputs, const std::vector<MSTensor> &outputs, const schema::Primitive *primitive,
  const mindspore::Context *ctx)>;

/// \brief RegisterKernel Defined registration of kernel.
class MS_API RegisterKernel {
 public:
  /// \brief Static method to register kernel which is correspondng to an ordinary op.
  ///
  /// \param[in] arch Define deviceType, such as CPU.
  /// \param[in] provider Define the identification of user.
  /// \param[in] data_type Define kernel's input data type.
  /// \param[in] type Define the ordinary op type.
  /// \param[in] creator Define a function pointer to create a kernel.
  ///
  /// \return Status as a status identification of registering.
  inline static Status RegKernel(const std::string &arch, const std::string &provider, DataType data_type, int type,
                                 const CreateKernel creator);

  /// \brief Static method to register kernel which is corresponding to custom op.
  ///
  /// \param[in] arch Define deviceType, such as CPU.
  /// \param[in] provider Define the identification of user.
  /// \param[in] data_type Define kernel's input data type.
  /// \param[in] type Define the concrete type of a custom op.
  /// \param[in] creator Define a function pointer to create a kernel.
  ///
  /// \return Status as a status identification of registering.
  inline static Status RegCustomKernel(const std::string &arch, const std::string &provider, DataType data_type,
                                       const std::string &type, const CreateKernel creator);

  /// \brief Static methon to get a kernel's create function.
  ///
  /// \param[in] desc Define kernel's basic attribute.
  /// \param[in] primitive Define the primitive of kernel generated by flatbuffers.
  ///
  /// \return Function pointer to create a kernel.
  inline static CreateKernel GetCreator(const schema::Primitive *primitive, KernelDesc *desc);

 private:
  static Status RegKernel(const std::vector<char> &arch, const std::vector<char> &provider, DataType data_type,
                          int type, const CreateKernel creator);
  static Status RegCustomKernel(const std::vector<char> &arch, const std::vector<char> &provider, DataType data_type,
                                const std::vector<char> &type, const CreateKernel creator);
  static CreateKernel GetCreator(const schema::Primitive *primitive, KernelDescHelper *desc);
};

/// \brief KernelReg Defined registration class of kernel.
class MS_API KernelReg {
 public:
  /// \brief Destructor of KernelReg.
  ~KernelReg() = default;

  /// \brief Method to register ordinary op.
  ///
  /// \param[in] arch Define deviceType, such as CPU.
  /// \param[in] provider Define the identification of user.
  /// \param[in] data_type Define kernel's input data type.
  /// \param[in] op_type Define the ordinary op type.
  /// \param[in] creator Define a function pointer to create a kernel.
  KernelReg(const std::string &arch, const std::string &provider, DataType data_type, int op_type,
            const CreateKernel creator) {
    RegisterKernel::RegKernel(arch, provider, data_type, op_type, creator);
  }

  /// \brief Method to register customized op.
  ///
  /// \param[in] arch Define deviceType, such as CPU.
  /// \param[in] provider Define the identification of user.
  /// \param[in] data_type Define kernel's input data type.
  /// \param[in] op_type Define the concrete type of a custom op.
  /// \param[in] creator Define a function pointer to create a kernel.
  KernelReg(const std::string &arch, const std::string &provider, DataType data_type, const std::string &op_type,
            const CreateKernel creator) {
    RegisterKernel::RegCustomKernel(arch, provider, data_type, op_type, creator);
  }
};

Status RegisterKernel::RegKernel(const std::string &arch, const std::string &provider, DataType data_type, int type,
                                 const CreateKernel creator) {
  return RegKernel(StringToChar(arch), StringToChar(provider), data_type, type, creator);
}

Status RegisterKernel::RegCustomKernel(const std::string &arch, const std::string &provider, DataType data_type,
                                       const std::string &type, const CreateKernel creator) {
  return RegCustomKernel(StringToChar(arch), StringToChar(provider), data_type, StringToChar(type), creator);
}

CreateKernel RegisterKernel::GetCreator(const schema::Primitive *primitive, KernelDesc *desc) {
  if (desc == nullptr || primitive == nullptr) {
    return nullptr;
  }
  KernelDescHelper kernel_desc = {desc->data_type, desc->type, StringToChar(desc->arch), StringToChar(desc->provider)};
  return GetCreator(primitive, &kernel_desc);
}

/// \brief Defined registering macro to register ordinary op kernel, which called by user directly.
///
/// \param[in] arch Define deviceType, such as CPU.
/// \param[in] provider Define the identification of user.
/// \param[in] data_type Define kernel's input data type.
/// \param[in] op_type Define the ordinary op type.
/// \param[in] creator Define a function pointer to create a kernel.
#define REGISTER_KERNEL(arch, provider, data_type, op_type, creator)                                                   \
  namespace {                                                                                                          \
  static mindspore::registry::KernelReg g_##arch##provider##data_type##op_type##kernelReg(#arch, #provider, data_type, \
                                                                                          op_type, creator);           \
  }  // namespace

/// \brief Defined registering macro to register custom op kernel, which called by user directly.
///
/// \param[in] arch Define deviceType, such as CPU.
/// \param[in] provider Define the identification of user.
/// \param[in] data_type Define kernel's input data type.
/// \param[in] op_type Define the concrete type of a custom op.
/// \param[in] creator Define a function pointer to create a kernel.
#define REGISTER_CUSTOM_KERNEL(arch, provider, data_type, op_type, creator)                                            \
  namespace {                                                                                                          \
  static mindspore::registry::KernelReg g_##arch##provider##data_type##op_type##kernelReg(#arch, #provider, data_type, \
                                                                                          #op_type, creator);          \
  }  // namespace
}  // namespace registry
}  // namespace mindspore

#endif  // MINDSPORE_LITE_INCLUDE_REGISTRY_REGISTER_KERNEL_H_
