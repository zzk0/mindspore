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
""" test graph fallback control flow."""
import pytest
import numpy as np
from mindspore import Tensor, ms_function, context

context.set_context(mode=context.GRAPH_MODE)


@pytest.mark.level0
@pytest.mark.platform_x86_gpu_training
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_for_after_for_in_while_1():
    """
    Feature: JIT Fallback
    Description: Test fallback with control flow.
    Expectation: No exception.
    """

    @ms_function
    def func3311():
        x = Tensor([0])
        y = Tensor([0])

        while x < Tensor([3]):
            for _ in range(3):
                x = x + Tensor([1])

        for _ in range(3):
            y = y - 1
        return x + y

    res = func3311()
    assert res == 0


@pytest.mark.level0
@pytest.mark.platform_x86_gpu_training
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_for_after_for_in_while_2():
    """
    Feature: JIT Fallback
    Description: Test fallback with control flow.
    Expectation: No exception.
    """

    @ms_function
    def func3312():
        x = Tensor([2])
        y = Tensor([2])
        while y < Tensor([5]) and x > Tensor([1]):
            for _ in range(3):
                y = y + Tensor([1])

        for i in range(3):
            z = Tensor([i])
            x = x + z

        return x, y

    res_x, res_y = func3312()
    assert res_x == 5
    assert res_y == 5


@pytest.mark.level0
@pytest.mark.platform_x86_gpu_training
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_for_after_for_in_while_3():
    """
    Feature: JIT Fallback
    Description: Test fallback with control flow.
    Expectation: No exception.
    """

    @ms_function
    def func3313():
        x = np.array([0])
        y = np.array([5, 6, 7])
        while x < 2:
            for _ in range(1):
                y = y - np.array([2, 2, 2])
                x = x + 1

        z = Tensor(y)
        out = 1
        for i in z:
            out = out * i
        return out * Tensor(x)

    res = func3313()
    assert res == 12


@pytest.mark.level0
@pytest.mark.platform_x86_gpu_training
@pytest.mark.platform_arm_ascend_training
@pytest.mark.platform_x86_ascend_training
@pytest.mark.env_onecard
def test_for_after_for_in_while_4():
    """
    Feature: JIT Fallback
    Description: Test fallback with control flow.
    Expectation: No exception.
    """

    @ms_function
    def func3314():
        x = Tensor([1])
        y = Tensor([2])
        z = []
        while max(x, y) == Tensor([2]):
            y = y + min(x, y)
            for _ in range(3):
                z.append(Tensor([2]))

        for i in z:
            x = x * i
        return x

    res = func3314()
    assert res == 8
