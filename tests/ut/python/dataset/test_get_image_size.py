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
# ==============================================================================

import numpy as np
import pytest
from PIL import Image

import mindspore.dataset.vision.utils as vision
import mindspore.dataset.vision.c_transforms as C
from mindspore import log as logger


def test_get_image_size_output_array():
    """
    Feature: get_image_num_channels array(after Decode array.shape is HWC)
    Description: Test get_image_num_channels
    Expectation: The returned result is as expected
    """
    expect = [2268, 4032]
    img = np.fromfile("../data/dataset/apple.jpg", dtype=np.uint8)
    input_array = C.Decode()(img)
    output = vision.get_image_size(input_array)
    assert expect == output


def test_get_image_num_size_output_img():
    """
    Feature: get_image_num_channels img(Image.size is [H, W])
    Description: Test get_image_num_channels
    Expectation: The returned result is as expected
    """
    expect = [2268, 4032]
    img = Image.open("../data/dataset/apple.jpg")
    output_size = vision.get_image_size(img)
    assert expect == output_size


def test_get_image_num_channels_invalid_input():
    """
    Feature: get_image_num_channels
    Description: Test get_image_num_channels invalid input
    Expectation: Correct error is raised as expected
    """

    def test_invalid_input(test_name, image, error, error_msg):
        logger.info("Test GetImageNumChannels with wrong params: {0}".format(test_name))
        with pytest.raises(error) as error_info:
            vision.get_image_size(image)
        assert error_msg in str(error_info.value)

    invalid_input = 1
    invalid_shape = np.array([1, 2, 3])
    test_invalid_input("invalid input", invalid_input, TypeError,
                       "Input image is not of type <class 'numpy.ndarray'> or <class 'PIL.Image.Image'>, "
                       "but got: <class 'int'>.")
    test_invalid_input("invalid input", invalid_shape, RuntimeError,
                       "GetImageSize: invalid parameter, image should have at least two dimensions, but got: 1")


if __name__ == "__main__":
    test_get_image_size_output_array()
    test_get_image_num_size_output_img()
    test_get_image_num_channels_invalid_input()
