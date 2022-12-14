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

"""nn_ops vmap impl."""

from mindspore.ops import operations as P
from mindspore.ops.operations import _grad_ops as G
from mindspore.ops.operations import nn_ops as NN
from mindspore.ops import functional as F
from mindspore.ops import constexpr
from ..primitive import Primitive
from .._vmap.vmap_base import vmap_rules_getters, vmap_general_preprocess, get_unop_vmap_rule, _bdim_at_front, \
    get_unary_grad_vmap_rule


@vmap_rules_getters.register(P.BiasAdd)
def get_bias_add_vmap_rule(prim, axis_size):
    """VmapRule for `BiasAdd` operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)
        data_format = "NCHW"
    else:
        data_format = prim.data_format
    add_op = P.Add()

    @constexpr
    def _get_bias_broadcast_shape(x_shape, bias_shape, bias_dim, data_format):
        """Get the broadcast shape for bias and use it in 'BiasAdd' VmapRule."""
        bias_rank = len(bias_shape)
        if bias_dim is None and bias_rank == 1:
            bias_batch = 1
            bias_channel = bias_shape[0]
        elif bias_dim is not None and bias_rank == 2:
            bias_batch = bias_shape[0]
            bias_channel = bias_shape[1]
        else:
            raise ValueError("The rank of 'bias' in 'BiasAdd' operator is invalid, which is rank: {}"
                             " with bias_dim: {}.".format(bias_rank, bias_dim))

        # The 'Biasadd' operator supports 2-5 dimensions input, and another 'batch' dimension is added to the front in
        # vmap scenario.
        x_min_rank = 3
        x_max_rank = 5
        if data_format == "NCDHW":
            x_max_rank += 1
        x_rank = len(x_shape)

        if x_rank < x_min_rank or x_rank > x_max_rank:
            raise ValueError("For primitive[BiasAdd] in vmap, the dims of input_x must be in [x_min_rank, {}"
                             "], but got {}.".format(x_max_rank, x_rank))

        if data_format == "NHWC":
            # In the 'NHWC' data format ('BN**C' actually), the last dimension is channel axis.
            x_channel = x_shape[-1]
            if x_channel != bias_channel:
                raise ValueError("For 'BiadAdd, bias_channel must be equal to x_channel, "
                                 "but got date format: {}, got bias_channel: {}, "
                                 "x_channel: {}.".format(data_format, bias_channel, x_channel))
            if bias_dim is None:
                bias_broadcast_shape = (1,) * (x_rank - bias_rank) + (bias_channel,)
            else:
                bias_broadcast_shape = (bias_batch,) + (1,) * (x_rank - bias_rank) + (bias_channel,)
        else:
            # In the 'NCHW' or 'NCDHW' data format ('BNC**' actually), the third dimension is channel axis.
            x_channel = x_shape[2]
            if x_channel != bias_channel:
                raise ValueError("For 'BiadAdd, bias_channel must be equal to x_channel, but got date format: "
                                 "{}, got bias_channel: {}, x_channel: {}."\
                                 .format(data_format, bias_channel, x_channel))
            bias_broadcast_shape = (bias_batch, 1, bias_channel)
            if x_rank == x_min_rank:
                return bias_broadcast_shape
            bias_broadcast_shape = bias_broadcast_shape + (1,) * (x_rank - x_min_rank)
        return bias_broadcast_shape

    def vmap_rule(input_bdim, bias_bdim):
        is_all_none, result = vmap_general_preprocess(prim, input_bdim, bias_bdim)
        if is_all_none:
            return result

        input_x, x_dim = input_bdim
        bias, bias_dim = bias_bdim
        input_x = _bdim_at_front(input_x, x_dim, axis_size)
        if bias_dim is not None:
            bias = _bdim_at_front(bias, bias_dim, axis_size)
        x_shape = F.shape(input_x)
        bias_shape = F.shape(bias)
        bias_broadcast_shape = _get_bias_broadcast_shape(x_shape, bias_shape, bias_dim, data_format)
        bias = F.reshape(bias, bias_broadcast_shape)
        out = add_op(input_x, bias)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(P.Dropout2D)
@vmap_rules_getters.register(P.Dropout3D)
def get_dropout_nd_vmap_rule(prim, axis_size):
    """VmapRule for 'DropoutND' operation."""

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        x = _bdim_at_front(x, x_dim, axis_size)
        output, mask = prim(x)
        return (output, 0), (mask, 0)

    return vmap_rule


@vmap_rules_getters.register(G.FastGeLUGrad)
@vmap_rules_getters.register(G.HShrinkGrad)
def get_fast_gelu_grad_vmap_rule(prim, axis_size):
    """VmapRule for common activation grad operation."""
    if isinstance(prim, str):
        prim_name = prim
        prim = Primitive(prim)
    else:
        prim_name = prim.name

    def vmap_rule(x_bdim, dy_bdim):
        x, x_dim = x_bdim
        dy, dy_dim = dy_bdim
        x_shape = F.shape(x)
        dy_shape = F.shape(dy)
        if x_dim == dy_dim and x_shape == dy_shape:
            out = prim(x, dy)
            return (out, x_dim)

        if F.rank(x):
            x = _bdim_at_front(x, x_dim, 1)
        if F.rank(dy):
            dy = _bdim_at_front(dy, dy_dim, 1)
        x_shape = F.shape(x)
        dy_shape = F.shape(dy)
        if x_shape != dy_shape:
            raise RuntimeError("For {} vmap, input x shape is supposed to be the same as input dy shape "
                               "after batch transforming, but got x_shape {}, dy_shape {}"
                               .format(prim_name, x_shape, dy_shape))
        out = prim(x, dy)
        return (out, 0)

    return vmap_rule


@vmap_rules_getters.register(NN.Pdist)
def get_pdist_vmap_rule(prim, axis_size):
    """VmapRule for `Pdist`"""
    if isinstance(prim, str):
        prim = Primitive(prim)
        prim.add_prim_attr('p', 2.0)

    def vmap_rule(x_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim)
        if is_all_none:
            return result
        x, x_dim = x_bdim
        x = _bdim_at_front(x, x_dim, axis_size)
        out = prim(x)
        return out, 0

    return vmap_rule


@vmap_rules_getters.register(P.KLDivLoss)
def get_kl_div_loss_vmap_rule(prim, axis_size):
    """VmapRule for `KLDivLoss` operation."""
    if isinstance(prim, str):
        prim = Primitive(prim)

    prim_reduction = prim.reduction
    if prim_reduction == "mean":
        kl_div_loss_op = P.KLDivLoss("none")
        reduce_op = P.ReduceMean()
    elif prim_reduction == "sum":
        kl_div_loss_op = P.KLDivLoss("none")
        reduce_op = P.ReduceSum()
    elif prim_reduction == "batchmean":
        kl_div_loss_op = P.KLDivLoss("none")
        reduce_op = P.ReduceSum()
        factor_op = P.Div()

    def vmap_rule(x_bdim, target_bdim):
        is_all_none, result = vmap_general_preprocess(prim, x_bdim, target_bdim)
        if is_all_none:
            return result

        x, x_dim = x_bdim
        target, target_dim = target_bdim
        x_ndim = F.rank(x)
        target_ndim = F.rank(target)
        max_rank = max(x_ndim, target_ndim)
        x = _bdim_at_front(x, x_dim, axis_size)
        target = _bdim_at_front(target, target_dim, axis_size)
        reduce_indexes = None
        factor = 1
        # if rank is larger than 1, we need to reduce result when reduction != 'none'
        if max_rank > 1:
            reduce_indexes = tuple(range(1, max_rank))
            factor = F.shape(x)[1]

        # elementwise style when reduction='none', otherwise reduce style
        if prim_reduction == "none":
            out = prim(x, target)
        elif prim_reduction in ("mean", "sum"):
            out = kl_div_loss_op(x, target)
            if reduce_indexes is not None:
                out = reduce_op(out, reduce_indexes)
        elif prim_reduction == "batchmean":
            out = kl_div_loss_op(x, target)
            if reduce_indexes is not None:
                out = reduce_op(out, reduce_indexes)
                out = factor_op(out, factor)
        else:
            raise RuntimeError("For KLDivLoss vmap, reduction should be one of "
                               "['none', 'mean', 'batchmean', 'sum'], but got '{}'".format(prim_reduction))
        return (out, 0)

    return vmap_rule


# Unary vmap
get_unop_vmap_rule = vmap_rules_getters.register(P.Elu)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.ReLU)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.ReLU6)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.SeLU)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.HSigmoid)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Softplus)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Softsign)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.SoftShrink)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.HShrink)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.GeLU)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.FastGeLU)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.HSwish)(get_unop_vmap_rule)
get_unop_vmap_rule = vmap_rules_getters.register(P.Tanh)(get_unop_vmap_rule)
# UnaryGrad vmap
get_unary_grad_vmap_rule = vmap_rules_getters.register(G.TanhGrad)(get_unary_grad_vmap_rule)
get_unary_grad_vmap_rule = vmap_rules_getters.register(G.SoftplusGrad)(get_unary_grad_vmap_rule)
