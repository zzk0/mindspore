mindspore.ops.bessel_i1
=======================

.. py:class:: mindspore.ops.bessel_i1

    逐元素计算并返回输入Tensor的Bessel i1函数值

    **输入：**

    - **x** (Tensor) - 任意维度的Tensor。数据类型应为float16，float32或float64。

    **输出：**

    Tensor，shape和数据类型与 `x` 相同。

    **异常：**

    - **TypeError** - `x` 不是Tensor。
    - **TypeError** - `x` 的数据类型不是float16，float32或float64。
