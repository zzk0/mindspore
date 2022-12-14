# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""
This module is to support vision augmentations.
Some image augmentations are implemented with C++ OpenCV to provide high performance.
Other additional image augmentations are developed with Python PIL.

Common imported modules in corresponding API examples are as follows:

.. code-block::

    import mindspore.dataset as ds
    import mindspore.dataset.vision as vision
    import mindspore.dataset.vision.utils as utils

Alternative and equivalent imported vision is as follows:

.. code-block::

    import mindspore.dataset.vision.transforms as vision

Note: Legacy c_transforms and py_transforms are deprecated but can still be imported as follows:

.. code-block::

    import mindspore.dataset.vision.c_transforms as c_vision
    import mindspore.dataset.vision.c_transforms as py_vision

Descriptions of common data processing terms are as follows:

- TensorOperation, the base class of all data processing operations implemented in C++.
- PyTensorOperation, the base class of all data processing operations implemented in Python.
"""
from . import c_transforms
from . import py_transforms
from . import transforms
from .transforms import not_random, AdjustGamma, AutoAugment, AutoContrast, BoundingBoxAugment, CenterCrop, \
    ConvertColor, Crop, CutMixBatch, CutOut, Decode, Equalize, FiveCrop, GaussianBlur, Grayscale, HorizontalFlip, \
    HsvToRgb, HWC2CHW, Invert, LinearTransformation, MixUpBatch, MixUp, NormalizePad, Normalize, Pad, PadToSize, \
    RandomAdjustSharpness, RandomAffine, RandomAutoContrast, RandomColorAdjust, RandomColor, RandomCropDecodeResize, \
    RandomCrop, RandomCropWithBBox, RandomEqualize, RandomErasing, RandomGrayscale, RandomHorizontalFlip, \
    RandomHorizontalFlipWithBBox, RandomInvert, RandomLighting, RandomPerspective, RandomPosterize, RandomResizedCrop, \
    RandomResizedCropWithBBox, RandomResize, RandomResizeWithBBox, RandomRotation, RandomSelectSubpolicy, \
    RandomSharpness, RandomSolarize, RandomVerticalFlip, RandomVerticalFlipWithBBox, Rescale, Resize, ResizeWithBBox, \
    RgbToHsv, Rotate, SlicePatches, SoftDvppDecodeRandomCropResizeJpeg, SoftDvppDecodeResizeJpeg, TenCrop, ToNumpy, \
    ToPIL, ToTensor, ToType, UniformAugment, VerticalFlip
from .utils import Inter, Border, ConvertMode, ImageBatchFormat, SliceMode, AutoAugmentPolicy, get_image_num_channels, \
    get_image_size
