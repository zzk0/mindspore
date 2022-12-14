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
Model API.
"""
import os
from enum import Enum

from ._checkparam import check_isinstance
from .context import Context
from .lib import _c_lite_wrapper
from .tensor import Tensor

__all__ = ['ModelType', 'Model', 'RunnerConfig', 'ModelParallelRunner']


class ModelType(Enum):
    """
    The MoedelType is used to define the model type.
    """
    MINDIR = 0
    MINDIR_LITE = 4


class Model:
    """
    The Model class is used to define a MindSpore model, facilitating computational graph management.

    Args:

    Examples:
        >>> import mindspore_lite as mslite
        >>> model = mslite.Model()
        >>> context.append_device_info(mslite.CPUDeviceInfo())
        >>> model.build_from_file("mnist.tflite.ms", mslite.ModelType.MINDIR_LITE, context)
    """

    def __init__(self):
        self._model = _c_lite_wrapper.ModelBind()
        self.model_path_ = ""

    def __str__(self):
        res = f"model_path: {self.model_path_}."
        return res

    def build_from_file(self, model_path, model_type, context):
        """
        Load and build a model from file.

        Args:
            model_path (str): Define the model path.
            model_type (ModelType): Define The type of model file.
                                              Options: ModelType::MINDIR, ModelType::MINDIR_LITE.
            context (Context): Define the context used to store options during execution.

        Raises:
            TypeError: type of input parameters are invalid.
            RuntimeError: build model failed.

        Examples:
            >>> model.build_from_file("mnist.tflite.ms", mslite.ModelType.MINDIR_LITE, context)
        """
        check_isinstance("model_path", model_path, str)
        check_isinstance("model_type", model_type, ModelType)
        check_isinstance("context", context, Context)
        if model_path != "":
            if not os.path.exists(model_path):
                raise RuntimeError(f"build_from_file failed! model_path is not exist!")

        self.model_path_ = model_path
        model_type_ = _c_lite_wrapper.ModelType.kMindIR_Lite
        if model_type is ModelType.MINDIR:
            model_type_ = _c_lite_wrapper.ModelType.kMindIR
        ret = self._model.build_from_file(self.model_path_, model_type_, context._context)
        if not ret.IsOk():
            raise RuntimeError(f"build_from_file failed! Error is {ret.ToString()}")

    def resize(self, inputs, dims):
        """
        Resizes the shapes of inputs.

        Args:
            inputs (list[Tensor]): A list that includes all input tensors in order.
            dims (list[list[int]]): Defines the new shapes of inputs, should be consistent with inputs.

        Raises:
            TypeError: type of input parameters are invalid.
            RuntimeError: resize model failed.

        Examples:
            >>> inputs = model.get_inputs()
            >>> model.resize(inputs, [[1, 224, 224, 3]])
        """
        if not isinstance(inputs, list):
            raise TypeError("inputs must be list, but got {}.".format(type(inputs)))
        _inputs = []
        if not isinstance(dims, list):
            raise TypeError("dims must be list, but got {}.".format(type(dims)))
        for i, element in enumerate(inputs):
            if not isinstance(element, Tensor):
                raise TypeError(f"inputs element must be Tensor, but got "
                                f"{type(element)} at index {i}.")
        for i, element in enumerate(dims):
            if not isinstance(element, list):
                raise TypeError(f"dims element must be list, but got "
                                f"{type(element)} at index {i}.")
            for j, dim in enumerate(element):
                if not isinstance(dim, int):
                    raise TypeError(f"dims element's element must be int, but got "
                                    f"{type(dim)} at {i}th dims element's {j}th element.")
        if len(inputs) != len(dims):
            raise ValueError(f"inputs's size does not match dims's size, but got "
                             f"inputs: {len(inputs)} and dims: {len(dims)}.")
        for i, element in enumerate(inputs):
            if len(element.get_shape()) != len(dims[i]):
                raise ValueError(f"one of inputs's size does not match one of dims's size, but got "
                                 f"input: {element.get_shape()} and dim: {len(dims[i])} at {i} index.")
            _inputs.append(element._tensor)
        ret = self._model.resize(_inputs, dims)
        if not ret.IsOk():
            raise RuntimeError(f"resize failed! Error is {ret.ToString()}")

    def predict(self, inputs, outputs):
        """
        Inference model.

        Args:
            inputs (list[Tensor]): A list that includes all input tensors in order.
            outputs (list[Tensor]): The model outputs are filled in the container in sequence.

        Raises:
            TypeError: type of input parameters are invalid.
            RuntimeError: resize model failed.

        Examples:
            >>> inputs = model.get_inputs()
            >>> outputs = model.get_outputs()
            >>> model.predict(inputs, outputs)
        """
        if not isinstance(inputs, list):
            raise TypeError("inputs must be list, but got {}.".format(type(inputs)))
        if not isinstance(outputs, list):
            raise TypeError("outputs must be list, but got {}.".format(type(outputs)))
        _inputs = []
        for i, element in enumerate(inputs):
            if not isinstance(element, Tensor):
                raise TypeError(f"inputs element must be Tensor, but got "
                                f"{type(element)} at index {i}.")
            _inputs.append(element._tensor)
        _outputs = []
        for i, element in enumerate(outputs):
            if not isinstance(element, Tensor):
                raise TypeError(f"outputs element must be Tensor, but got "
                                f"{type(element)} at index {i}.")
            _outputs.append(element._tensor)

        ret = self._model.predict(_inputs, _outputs, None, None)
        if not ret.IsOk():
            raise RuntimeError(f"predict failed! Error is {ret.ToString()}")

    def get_inputs(self):
        """
        Obtains all input tensors of the model.

        Returns:
            list[Tensor], the inputs tensor list of the model.

        Examples:
            >>> inputs = model.get_inputs()
        """
        inputs = []
        for _tensor in self._model.get_inputs():
            inputs.append(Tensor(_tensor))
        return inputs

    def get_outputs(self):
        """
        Obtains all output tensors of the model.

        Returns:
            list[Tensor], the outputs tensor list of the model.

        Examples:
            >>> outputs = model.get_outputs()
        """
        outputs = []
        for _tensor in self._model.get_outputs():
            outputs.append(Tensor(_tensor))
        return outputs

    def get_input_by_tensor_name(self, tensor_name):
        """
        Obtains the input tensor of the model by name.

        Args:
            tensor_name (str): tensor name.

        Returns:
            Tensor, the input tensor of the tensor name.

        Raises:
            TypeError: type of input parameters are invalid.

        Examples:
            >>> input = model.get_input_by_tensor_name("tensor_in")
        """
        check_isinstance("tensor_name", tensor_name, str)
        _tensor = self._model.get_input_by_tensor_name(tensor_name)
        if _tensor.is_null():
            raise RuntimeError(f"get_input_by_tensor_name failed!")
        return Tensor(_tensor)

    def get_output_by_tensor_name(self, tensor_name):
        """
        Obtains the output tensor of the model by name.

        Args:
            tensor_name (str): tensor name.

        Returns:
            Tensor, the output tensor of the tensor name.

        Raises:
            TypeError: type of input parameters are invalid.

        Examples:
            >>> output = model.get_output_by_tensor_name("tensor_out")
        """
        check_isinstance("tensor_name", tensor_name, str)
        _tensor = self._model.get_output_by_tensor_name(tensor_name)
        if _tensor.is_null():
            raise RuntimeError(f"get_output_by_tensor_name failed!")
        return Tensor(_tensor)


class RunnerConfig:
    """
    RunnerConfig Class

    Args:
        context (Context): Define the context used to store options during execution.
        workers_num (int): the num of workers.

    Raises:
        TypeError: type of input parameters are invalid.

    Examples:
        >>> import mindspore_lite as mslite
        >>> runner_config = mslite.RunnerConfig(context, 4)
    """

    def __init__(self, context, workers_num):
        check_isinstance("context", context, Context)
        check_isinstance("workers_num", workers_num, int)
        if workers_num < 0:
            raise ValueError(f"RunnerConfig's init failed! workers_num must be positive.")
        self._runner_config = _c_lite_wrapper.RunnerConfigBind()
        self._runner_config.set_workers_num(workers_num)
        self._runner_config.set_context(context._context)

    def __str__(self):
        res = f"workers num: {self._runner_config.get_workers_num()}, " \
              f"context: {self._runner_config.get_context_info()}."
        return res


class ModelParallelRunner:
    """
    The ModelParallelRunner class is used to define a MindSpore ModelParallelRunner, facilitating Model management.

    Args:
        None

    Examples:
        >>> import mindspore_lite as mslite
        >>> model_parallel_runner = mslite.ModelParallelRunner()
    """

    def __init__(self):
        self._model = _c_lite_wrapper.ModelParallelRunnerBind()
        self.model_path_ = ""

    def __str__(self):
        return f"model_path: {self.model_path_}."

    def init(self, model_path, runner_config):
        """
        build a model parallel runner from model path so that it can run on a device.

        Args:
            model_path (str): Define the model path.
            runner_config (RunnerConfig, optional): Define the config used to store options during model pool init.

        Raises:
            TypeError: type of input parameters are invalid.
            RuntimeError: init ModelParallelRunner failed.

        Examples:
            >>> model_parallel_runner.init("mnist.tflite.ms", runner_config)
        """
        check_isinstance("model_path", model_path, str)
        check_isinstance("runner_config", runner_config, RunnerConfig)
        if model_path != "":
            if not os.path.exists(model_path):
                raise RuntimeError(f"ModelParallelRunner's init failed! model_path is not exist!")
        self.model_path_ = model_path
        ret = self._model.init(self.model_path_, runner_config._runner_config)
        if not ret.IsOk():
            raise RuntimeError(f"ModelParallelRunner's init failed! Error is {ret.ToString()}")

    def predict(self, inputs, outputs):
        """
        Inference ModelParallelRunner.

        Args:
            inputs (list[Tensor]): A list that includes all input tensors in order.
            outputs (list[Tensor]): The model outputs are filled in the container in sequence.

        Raises:
            TypeError: type of input parameters are invalid.
            RuntimeError: resize model failed.

        Examples:
            >>> inputs = model_parallel_runner.get_inputs()
            >>> outputs = model_parallel_runner.get_outputs()
            >>> model_parallel_runner.predict(inputs, outputs)
        """
        if not isinstance(inputs, list):
            raise TypeError("inputs must be list, but got {}.".format(type(inputs)))
        if not isinstance(outputs, list):
            raise TypeError("outputs must be list, but got {}.".format(type(outputs)))
        _inputs = []
        for i, element in enumerate(inputs):
            if not isinstance(element, Tensor):
                raise TypeError(f"inputs element must be Tensor, but got "
                                f"{type(element)} at index {i}.")
            _inputs.append(element._tensor)
        _outputs = []
        for i, element in enumerate(outputs):
            if not isinstance(element, Tensor):
                raise TypeError(f"outputs element must be Tensor, but got "
                                f"{type(element)} at index {i}.")
            _outputs.append(element._tensor)

        ret = self._model.predict(_inputs, _outputs, None, None)
        if not ret.IsOk():
            raise RuntimeError(f"predict failed! Error is {ret.ToString()}")

    def get_inputs(self):
        """
        Obtains all input tensors of the model.

        Returns:
            list[Tensor], the inputs tensor list of the model.

        Examples:
            >>> inputs = model_parallel_runner.get_inputs()
        """
        inputs = []
        for _tensor in self._model.get_inputs():
            inputs.append(Tensor(_tensor))
        return inputs

    def get_outputs(self):
        """
        Obtains all output tensors of the model.

        Returns:
            list[Tensor], the outputs tensor list of the model.

        Examples:
            >>> outputs = model_parallel_runner.get_outputs()
        """
        outputs = []
        for _tensor in self._model.get_outputs():
            outputs.append(Tensor(_tensor))
        return outputs
