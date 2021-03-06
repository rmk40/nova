# Copyright (c) 2011 OpenStack, LLC.
# Copyright (c) 2012 Justin Santa Barbara
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nova import flags
from nova.openstack.common import cfg
from nova.openstack.common import log as logging
from nova.scheduler import filters


LOG = logging.getLogger(__name__)

cpu_allocation_ratio_opt = cfg.FloatOpt('cpu_allocation_ratio',
        default=16.0,
        help='Virtual CPU to Physical CPU allocation ratio')

FLAGS = flags.FLAGS
FLAGS.register_opt(cpu_allocation_ratio_opt)


class CoreFilter(filters.BaseHostFilter):
    """CoreFilter filters based on CPU core utilization."""

    def host_passes(self, host_state, filter_properties):
        """Return True if host has sufficient CPU cores."""
        instance_type = filter_properties.get('instance_type')
        if host_state.topic != FLAGS.compute_topic or not instance_type:
            return True

        if not host_state.vcpus_total:
            # Fail safe
            LOG.warning(_("VCPUs not set; assuming CPU collection broken"))
            return True

        instance_vcpus = instance_type['vcpus']
        vcpus_total = host_state.vcpus_total * FLAGS.cpu_allocation_ratio

        # Only provide a VCPU limit to compute if the virt driver is reporting
        # an accurate count of installed VCPUs. (XenServer driver does not)
        if vcpus_total > 0:
            host_state.limits['vcpu'] = vcpus_total

        return (vcpus_total - host_state.vcpus_used) >= instance_vcpus
