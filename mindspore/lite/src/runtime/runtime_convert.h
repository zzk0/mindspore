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

#ifndef MINDSPORE_LITE_SRC_RUNTIME_RUNTIME_CONVERT_H_
#define MINDSPORE_LITE_SRC_RUNTIME_RUNTIME_CONVERT_H_

#ifdef RUNTIME_CONVERT
#include <stdio.h>
#include <string>
#include <memory>

namespace mindspore::lite {
char *RuntimeConvert(const char *model_buf, const size_t &buf_size, size_t *size);
char *RuntimeConvert(const std::string &file_path, size_t *size);
}  // namespace mindspore::lite
#endif  // RUNTIME_CONVERT

#endif  // MINDSPORE_LITE_SRC_RUNTIME_RUNTIME_CONVERT_H_
