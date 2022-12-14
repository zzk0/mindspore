# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""
Test lite python API.
"""
import mindspore_lite as mslite
import numpy as np


def common_predict(context):
    model = mslite.Model()
    model.build_from_file("mnist.tflite.ms", mslite.ModelType.MINDIR_LITE, context)

    inputs = model.get_inputs()
    outputs = model.get_outputs()
    in_data = np.fromfile("mnist.tflite.ms.bin", dtype=np.float32)
    inputs[0].set_data_from_numpy(in_data)
    model.predict(inputs, outputs)
    for output in outputs:
        data = output.get_data_to_numpy()
        print("data: ", data)


# ============================ cpu inference ============================
def test_cpu_inference_01():
    cpu_device_info = mslite.CPUDeviceInfo(enable_fp16=False)
    print("cpu_device_info: ", cpu_device_info)
    context = mslite.Context(thread_num=1, thread_affinity_mode=2)
    context.append_device_info(cpu_device_info)
    common_predict(context)


# ============================ gpu inference ============================
def test_gpu_inference_01():
    gpu_device_info = mslite.GPUDeviceInfo(device_id=0, enable_fp16=False)
    print("gpu_device_info: ", gpu_device_info)
    cpu_device_info = mslite.CPUDeviceInfo(enable_fp16=False)
    print("cpu_device_info: ", cpu_device_info)
    context = mslite.Context(thread_num=1, thread_affinity_mode=2)
    context.append_device_info(gpu_device_info)
    context.append_device_info(cpu_device_info)
    common_predict(context)


# ============================ ascend inference ============================
def test_ascend_inference_01():
    ascend_device_info = mslite.AscendDeviceInfo(device_id=0, input_format=None,
                                                 input_shape=None,
                                                 precision_mode="force_fp16",
                                                 op_select_impl_mode="high_performance",
                                                 dynamic_batch_size=None,
                                                 dynamic_image_size="",
                                                 fusion_switch_config_path="",
                                                 insert_op_cfg_path="")
    print("ascend_device_info: ", ascend_device_info)
    cpu_device_info = mslite.CPUDeviceInfo(enable_fp16=False)
    print("cpu_device_info: ", cpu_device_info)
    context = mslite.Context(thread_num=1, thread_affinity_mode=2)
    context.append_device_info(ascend_device_info)
    context.append_device_info(cpu_device_info)
    common_predict(context)


# ============================ server inference ============================
def test_server_inference_01():
    cpu_device_info = mslite.CPUDeviceInfo()
    print("cpu_device_info: ", cpu_device_info)
    context = mslite.Context(thread_num=4)
    context.append_device_info(cpu_device_info)
    runner_config = mslite.RunnerConfig(context, 4)
    model_parallel_runner = mslite.ModelParallelRunner()
    model_parallel_runner.init(model_path="mnist.tflite.ms", runner_config=runner_config)

    inputs = model_parallel_runner.get_inputs()
    in_data = np.fromfile("mnist.tflite.ms.bin", dtype=np.float32)
    inputs[0].set_data_from_numpy(in_data)
    outputs = model_parallel_runner.get_outputs()
    model_parallel_runner.predict(inputs, outputs)
    data = outputs[0].get_data_to_numpy()
    print("data: ", data)
