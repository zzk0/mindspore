/**
 * Copyright 2020-2021 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_LITE_SRC_PASS_FUSION_CONV_TRANSFORM_FUSION_H_
#define MINDSPORE_LITE_SRC_PASS_FUSION_CONV_TRANSFORM_FUSION_H_

#include <string>
#include "backend/optimizer/common/optimizer.h"
#include "tools/converter/converter_flags.h"

using mindspore::converter::FmkType;
namespace mindspore::opt {
class ConvTransformFusion : public PatternProcessPass {
 public:
  explicit ConvTransformFusion(bool multigraph = true, const std::string &name = "ConvTransformFusion")
      : PatternProcessPass(name, multigraph) {}
  ~ConvTransformFusion() override = default;

 protected:
  virtual void InitTransParam(const CNodePtr &, int, float *, float *) const = 0;

 private:
  const AnfNodePtr Process(const FuncGraphPtr &, const AnfNodePtr &, const EquivPtr &) const override;
  void GenTransParam(const CNodePtr &, int, float *, float *) const;
  void GenNewConvTensor(const FuncGraphPtr &, const CNodePtr &, int, const float *, const float *) const;
  void CalNewWeightTensor(const CNodePtr &, const tensor::TensorPtr &, int, const float *) const;
  static void CalNewBiasTensor(float *, int, bool, const float *, const float *);
  bool IsVariableWeightConv(const CNodePtr &conv_node) const;

 protected:
  FmkType fmk_type_ = converter::kFmkTypeTf;
};
}  // namespace mindspore::opt
#endif  // MINDSPORE_LITE_SRC_PASS_FUSION_CONV_TRANSFORM_FUSION_H_
