#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: EPL-2.0
#

import os
import sys

from common.base_model_init import BaseModelInitializer
from common.base_model_init import set_env_var


class ModelInitializer(BaseModelInitializer):
    def run_inference_sanity_checks(self, args, custom_args):
        if not args.input_graph:
            sys.exit("Please provide a path to the frozen graph directory"
                     " via the '--in-graph' flag.")
        if not args.data_location and self.args.accuracy_only:
            sys.exit("Please provide a path to the data directory via the "
                     "'--data-location' flag.")
        if args.socket_id == -1 and args.num_cores == -1:
            print("***Warning***: Running inference on all cores could degrade"
                  " performance. Pass a '--socket-id' to specify running on a"
                  " single socket instead.\n")

    def __init__(self, args, custom_args, platform_util):
        super(ModelInitializer, self).__init__(args, custom_args, platform_util)

        self.run_inference_sanity_checks(self.args, self.custom_args)
        self.set_kmp_vars()
        self.set_num_inter_intra_threads()

        set_env_var("OMP_NUM_THREADS", self.args.num_intra_threads)

        self.model_dir = os.path.join(self.args.intelai_models, self.args.mode, self.args.precision)

        # get benchmark command
        benchmark_script = os.path.join(self.model_dir, "infer_detections.py")

        # get command with numactl
        self.run_cmd = self.get_numactl_command(self.args.socket_id)
        self.run_cmd += "{0} {1}".format(self.python_exe, benchmark_script)
        self.run_cmd += " --input-graph {0}".format(self.args.input_graph)
        self.run_cmd += " --batch-size {0}".format(args.batch_size)
        self.run_cmd += " --inter-op-parallelism-threads {0}".format(self.args.num_inter_threads)
        self.run_cmd += " --intra-op-parallelism-threads {0}".format(self.args.num_intra_threads)

        if self.args.accuracy_only:
            self.run_cmd += " --accuracy-only "
            self.run_cmd += " --data-location {0}".format(self.args.data_location)

    def run(self):
        print(self.run_cmd)
        old_python_path = os.environ["PYTHONPATH"]
        os.environ["PYTHONPATH"] = os.path.join(self.args.model_source_dir, "research")
        self.run_command(self.run_cmd)
        os.environ["PYTHONPATH"] = old_python_path
