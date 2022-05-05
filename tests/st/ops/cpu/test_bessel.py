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

import numpy as np
import pytest

import mindspore.context as context
from mindspore import Tensor
import mindspore.ops as F


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_j0(dtype, eps):
    """
    Feature: bessel j0 function
    Description: test cases for BesselJ0
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([0.5, 1., 2., 4.]).astype(dtype))
    expect = np.array([0.9384698, 0.7651977, 0.22389078, -0.3971498]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_j0(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_j1(dtype, eps):
    """
    Feature: bessel j1 function
    Description: test cases for BesselJ1
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([0.5, 1., 2., 4.]).astype(dtype))
    expect = np.array([0.24226846, 0.44005057, 0.5767248, -0.06604332]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_j1(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_i0(dtype, eps):
    """
    Feature: bessel i0 function
    Description: test cases for BesselI0
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([-1, -0.5, 0.5, 1]).astype(dtype))
    expect = np.array([1.2660658, 1.0634834, 1.0634834, 1.2660658]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_i0(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_i0e(dtype, eps):
    """
    Feature: bessel i0e function
    Description: test cases for BesselI0e
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([-1, -0.5, 0.5, 1]).astype(dtype))
    expect = np.array([0.4657596, 0.64503527, 0.64503527, 0.4657596]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_i0e(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_k0(dtype, eps):
    """
    Feature: bessel k0 function
    Description: test cases for BesselK0
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([0.5, 1., 2., 4.]).astype(dtype))
    expect = np.array([0.92441905, 0.42102444, 0.11389387, 0.01115968]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_k0(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)


@pytest.mark.level0
@pytest.mark.platform_x86_cpu
@pytest.mark.env_onecard
@pytest.mark.parametrize('dtype, eps', [(np.float16, 1.0e-3), (np.float32, 1.0e-6), (np.float64, 1.0e-6)])
def test_bessel_k0e(dtype, eps):
    """
    Feature: bessel k-e function
    Description: test cases for BesselK0e
    Expectation: the result matches scipy
    """
    x = Tensor(np.array([0.5, 1., 2., 4.]).astype(dtype))
    expect = np.array([1.5241094, 1.1444631, 0.84156823, 0.6092977]).astype(dtype)
    error = np.ones(shape=[4]) * eps
    context.set_context(mode=context.GRAPH_MODE, device_target="CPU")

    output = F.bessel_k0e(x)
    diff = output.asnumpy() - expect
    assert np.all(diff < error)
