from simplesqlite.model import Integer, Model, Text

from .._const import Tc


class Filter(Model):
    device = Text(attr_name=Tc.Param.DEVICE, not_null=True)
    filter_id = Text(attr_name=Tc.Param.FILTER_ID)
    flowid = Text(attr_name=Tc.Param.FLOW_ID)
    protocol = Text(attr_name=Tc.Param.PROTOCOL)
    priority = Integer(attr_name=Tc.Param.PRIORITY)
    src_network = Text(attr_name=Tc.Param.SRC_NETWORK)
    dst_network = Text(attr_name=Tc.Param.DST_NETWORK)
    src_port = Integer(attr_name=Tc.Param.SRC_PORT)
    dst_port = Integer(attr_name=Tc.Param.DST_PORT)

    classid = Text(attr_name=Tc.Param.CLASS_ID)
    handle = Integer(attr_name=Tc.Param.HANDLE)


class Qdisc(Model):
    device = Text(attr_name=Tc.Param.DEVICE, not_null=True)
    direct_qlen = Integer()
    parent = Text(attr_name=Tc.Param.PARENT)
    handle = Text(attr_name=Tc.Param.HANDLE)
    delay = Text()
    delay_distro = Text(attr_name="delay-distro")
    loss = Text()
    duplicate = Text()
    corrupt = Text()
    reorder = Text()
    rate = Text()
