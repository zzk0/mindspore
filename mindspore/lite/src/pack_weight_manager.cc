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
#ifdef SERVER_INFERENCE
#include "src/pack_weight_manager.h"
namespace mindspore::lite {
PackWeightManager *PackWeightManager::GetInstance() {
  static PackWeightManager instance;
  return &instance;
}

void PackWeightManager::InitWeightManagerByPath(const std::string &model_path, const char *model_buf) {
  MS_CHECK_TRUE_RET_VOID(model_buf != nullptr);
  if (path_model_buf_.find(model_path) == path_model_buf_.end()) {
    auto *model_const_weight = new (std::nothrow) ModelConstWeight();
    if (model_const_weight == nullptr) {
      return;
    }
    path_model_weight_[model_path] = model_const_weight;
  }
  path_model_buf_[model_path].push_back(model_buf);
}

STATUS PackWeightManager::StoreLiteModel(const char *model_buf, const Model *model) {
  MS_CHECK_TRUE_RET(model_buf != nullptr, RET_ERROR);
  MS_CHECK_TRUE_RET(model != nullptr, RET_ERROR);
  for (auto &item : path_model_buf_) {
    auto &model_bufs = item.second;
    auto path = item.first;
    if (find(model_bufs.begin(), model_bufs.end(), model_buf) != model_bufs.end()) {
      path_model_weight_[path]->lite_models.push_back(model);
      return RET_OK;
    }
  }

  return RET_OK;
}

void *PackWeightManager::GetTensorData(const LiteModel *model, const SchemaTensorWrapper *origin_tensor,
                                       size_t tensor_index) {
  MS_CHECK_TRUE_RET(model != nullptr, nullptr);
  for (auto &item : path_model_weight_) {
    auto &path = item.first;
    auto &model_weight = item.second;
    auto &models = model_weight->lite_models;
    if (find(models.begin(), models.end(), model) != models.end()) {
      if (model_weight->packed_weight.find(tensor_index) != model_weight->packed_weight.end()) {
        return model_weight->packed_weight[tensor_index];
      }
      path_model_weight_[path]->origin_weight[tensor_index] = origin_tensor->data();
      path_model_weight_[path]->origin_data_index[origin_tensor->data()] = tensor_index;
      return nullptr;
    }
  }
  MS_LOG(DEBUG) << "tensor data not packed.";
  return nullptr;
}

std::pair<PackStatus, void *> PackWeightManager::FindPackedTensor(ModelConstWeight *weight, const Tensor *tensor,
                                                                  const size_t size) {
  std::unique_lock<std::mutex> weight_lock(mtx_weight_);
  MS_CHECK_TRUE_RET(tensor != nullptr, std::make_pair(MALLOC, nullptr));
  auto &packed_weights = weight->packed_weight;
  if (size > MAX_MALLOC_SIZE) {
    MS_LOG(ERROR) << "malloc size more than MAX_MALLOC_SIZE";
    return std::make_pair(MALLOC, nullptr);
  }
  if (weight->packed_data.find(tensor->data()) != weight->packed_data.end()) {
    return std::make_pair(PACKED, tensor->data());
  } else if (weight->origin_data_index.find(tensor->data()) != weight->origin_data_index.end()) {
    auto origin_index = weight->origin_data_index[tensor->data()];
    void *data = malloc(size);
    if (data == nullptr) {
      MS_LOG(ERROR) << "malloc failed.";
      return std::make_pair(MALLOC, nullptr);
    }
    weight->packed_data.insert(data);
    packed_weights.insert(std::make_pair(origin_index, data));
    return std::make_pair(NOTPACK, packed_weights.at(origin_index));
  }
  return std::make_pair(MALLOC, nullptr);
}

std::pair<PackStatus, void *> PackWeightManager::GetPackedTensor(const Tensor *tensor, const size_t size) {
  MS_CHECK_TRUE_RET(tensor != nullptr, std::make_pair(MALLOC, nullptr));
  std::pair<PackStatus, void *> packed_tensor_pair;
  for (auto &item : path_model_weight_) {
    auto &model_weight = item.second;
    packed_tensor_pair = FindPackedTensor(model_weight, tensor, size);
    if (packed_tensor_pair.second != nullptr) {
      return packed_tensor_pair;
    }
  }
  MS_LOG(DEBUG) << "not const tensor, need pack in kernel.";
  return std::make_pair(MALLOC, nullptr);
}

void PackWeightManager::DeleteSavedModelPtr(LiteModel *delete_model) {
  std::unique_lock<std::mutex> weight_lock(mtx_weight_);
  MS_CHECK_TRUE_RET_VOID(delete_model != nullptr);
  for (auto &item : path_model_weight_) {
    auto &weight = item.second;
    auto it = find(weight->lite_models.begin(), weight->lite_models.end(), delete_model);
    if (it != weight->lite_models.end()) {
      weight->lite_models.erase(it);
    }
  }
}

void PackWeightManager::FreePackedWeight(ModelConstWeight *weight) {
  auto &packed_tensors = weight->packed_weight;
  for (auto &packed_tensor : packed_tensors) {
    if (packed_tensor.second != nullptr) {
      free(packed_tensor.second);
      packed_tensor.second = nullptr;
    }
  }
  if (weight != nullptr) {
    delete weight;
    weight = nullptr;
  }
}

PackWeightManager::~PackWeightManager() {
  for (auto &item : path_model_weight_) {
    FreePackedWeight(item.second);
    path_model_weight_.erase(item.first);
  }
}
}  // namespace mindspore::lite
#endif
