#!/usr/bin/python

import argparse
import os
import subprocess
import shutil


class BenchmarkPipeline:
    def __init__(self,
                 _intel_models,
                 _public_models,
                 _statistics_path,
                 _precision,
                 _binaries_path,
                 _libraries_path,
                 _android_ndk_path,
                 _android_abi):
        self.intel_models = _intel_models
        self.public_models = _public_models
        self.stat_path = _statistics_path
        if os.path.exists(self.stat_path):
            shutil.rmtree(self.stat_path)
            os.mkdir(self.stat_path)
        self.log_path = os.path.join(self.stat_path, "log_info")
        os.mkdir(self.log_path)
        self.bench_app_log_path = os.path.join(self.stat_path, "benchmark_app_info")
        os.mkdir(self.bench_app_log_path)
        self.precision = _precision
        self.binaries_path = _binaries_path
        self.libraries_path = _libraries_path
        self.android_ndk_path = _android_ndk_path
        self.android_abi = _android_abi
        self.home_dir = "/data/local/tmp"
        self.cmd_line = ['/usr/bin/adb']
        self.dl_models = {}
        self.app_name = "benchmark_app"
        self.adb_model_path = None
        self.curr_stat_dir = None

    @staticmethod
    def run_cmd(cmd, postfix, path_to_save):
        cmd_line = " ".join(str(item) for item in cmd)
        stdout_path = os.path.join(path_to_save, postfix + ".txt")
        stderr_path = os.path.join(path_to_save, "stderr_" + postfix + ".txt")
        with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
            process = subprocess.Popen(cmd_line, shell=True, stdout=out, stderr=err)
            process.wait()

    def clear_environment(self, rm_dir=None):
        cmd_line = self.cmd_line.copy()
        cmd_line.append('shell')
        cmd_line.append('\"')
        cmd_line.append('rm -rf')
        if rm_dir is None:
            rm_dir = self.home_dir + '/*'
        cmd_line.append(rm_dir)
        cmd_line.append('\"')
        self.run_cmd(cmd_line,
                     self.clear_environment.__name__,
                     self.log_path)
        print("--- Cleared environment: ", rm_dir)
        return True

    def check_environment(self):
        cmd_line = self.cmd_line.copy()
        cmd_line.append('shell')
        cmd_line.append('\"')
        cmd_line.append('ls -l')
        cmd_line.append(self.home_dir)
        cmd_line.append('\"')
        self.run_cmd(cmd_line,
                     self.clear_environment.__name__,
                     self.log_path)
        print("Checked environment")
        return True

    def get_list_models(self):
        result_list = []
        for type_models in [self.intel_models, self.public_models]:
            list_models = os.listdir(type_models)
            for name_model in list_models:
                for precision in self.precision:
                    full_path_model = os.path.join(type_models, name_model, precision)
                    if os.path.isdir(full_path_model):
                        self.dl_models[name_model] = full_path_model
                        result_list.append(name_model)

        return result_list

    def send_bin_and_lib(self):
        cmd_line = self.cmd_line.copy()
        cmd_line.append("push --sync")

        app_path = os.path.join(self.binaries_path, self.app_name)
        if os.path.isfile(app_path):
            cmd_line.append(app_path)
        else:
            return False
        if os.path.isdir(self.libraries_path):
            cmd_line.append(self.libraries_path)
        else:
            return False
        cmd_line.append(self.home_dir)
        self.run_cmd(cmd_line,
                     self.clear_environment.__name__ + "_openvino",
                     self.log_path)

        print("--- Sent bin: ", app_path)
        print("--- Sent libs: ", self.libraries_path)
        print("Sent OpenVINO™ files")

        ndk_cxx_lib_rel_path = "sources/cxx-stl/llvm-libc++/libs/" + self.android_abi + "/libc++_shared.so"
        ndk_cxx_lib_abs_path = os.path.join(self.android_ndk_path, ndk_cxx_lib_rel_path)

        if os.path.isfile(ndk_cxx_lib_abs_path):
            cmd_line = self.cmd_line.copy()
            cmd_line.append("push --sync")
            cmd_line.append(ndk_cxx_lib_abs_path)
            cmd_line.append(os.path.join(self.home_dir, os.path.basename(self.libraries_path)))
        else:
            return False
        self.run_cmd(cmd_line,
                     self.clear_environment.__name__ + "_android_ndk",
                     self.log_path)

        print("Sent Android NDK libs: ", ndk_cxx_lib_abs_path)
        return True

    def send_model(self, local_model_name):
        model_path = self.dl_models[local_model_name]
        self.adb_model_path = os.path.join(self.home_dir, os.path.basename(model_path))
        self.clear_environment(self.adb_model_path)
        cmd_line = self.cmd_line.copy()
        cmd_line.append("push")
        cmd_line.append(model_path)
        cmd_line.append(self.home_dir)
        self.run_cmd(cmd_line,
                     self.clear_environment.__name__ + "_" + local_model_name,
                     self.log_path)
        print("--- Sent model: ", model_path)

    def run_model(self, local_model_name):
        cmd_line = self.cmd_line.copy()
        cmd_line.append("shell")
        cmd_line.append('\"')
        # LD_LIBRARY_PATH=...
        lib_path = os.path.join(self.home_dir, 'lib')
        cmd_line.append('LD_LIBRARY_PATH=' + lib_path)
        # ./.../benchmark_app
        app_path = os.path.join(self.home_dir, self.app_name)
        cmd_line.append(app_path)
        # -m .../model.xml
        local_model_path = os.path.join(self.adb_model_path, local_model_name + '.xml')
        cmd_line.append('-m')
        cmd_line.append(local_model_path)
        # -niter 10
        cmd_line.append('-niter 10')
        # -api sync
        cmd_line.append('-api sync')
        # -report_type detailed_counters
        cmd_line.append('-report_type detailed_counters')
        # -report_folder /data/local/tmp"
        cmd_line.append('-report_folder')
        cmd_line.append(self.home_dir)

        cmd_line.append('\"')
        print("--- Run to benchmark model: ", self.bench_app_log_path)
        self.run_cmd(cmd_line,
                     local_model_name,
                     self.bench_app_log_path)
        print("--- Finished to benchmark model")

    def get_per_layer_stat(self, local_model_name):
        cmd_line = self.cmd_line.copy()
        cmd_line.append("pull")
        perf_report_name = "benchmark_detailed_counters_report.csv"
        cmd_line.append(os.path.join(self.home_dir, perf_report_name))
        self.curr_stat_dir = os.path.join(self.stat_path, os.path.basename(self.dl_models[local_model_name]))
        if not os.path.exists(self.curr_stat_dir):
            os.mkdir(self.curr_stat_dir)
        cmd_line.append(self.curr_stat_dir)
        self.run_cmd(cmd_line,
                     self.get_per_layer_stat.__name__,
                     self.log_path)

        cmd_line = ["mv"]
        _, file_extension = os.path.splitext(perf_report_name)
        cmd_line.append(os.path.join(self.curr_stat_dir, perf_report_name))
        cmd_line.append(os.path.join(self.curr_stat_dir, local_model_name + file_extension))
        self.run_cmd(cmd_line,
                     self.get_per_layer_stat.__name__,
                     self.log_path)

        print("--- Store results: ", self.curr_stat_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenVINO™ Toolkit Android ARM benchmark statistics')
    parser.add_argument('--intel_models_path',
                        help='Path to OpenVINO™ Intel pre-trained models',
                        required=True)
    parser.add_argument('--public_models_path',
                        help='Path to OpenVINO™ public pre-trained models',
                        required=True)
    parser.add_argument('--collect_statistics',
                        help='Path to collect files of benchmark statistics',
                        required=True)
    parser.add_argument('--precision',
                        help='OpenVINO™ IR precision',
                        required=True,
                        nargs='+', default=[])
    parser.add_argument('--binaries_path',
                        help='Path to OpenVINO™ binary files (benchmark_app)',
                        required=True)
    parser.add_argument('--libraries_path',
                        help='Path to OpenVINO™ libraries (*.a, *.so)',
                        required=True)
    parser.add_argument('--android_ndk_path',
                        help='Path to Android NDK',
                        required=True)
    parser.add_argument('--android_abi',
                        help='Path to Android NDK',
                        required=True,
                        choices=['arm64-v8a'])
    parser.add_argument('--clear',
                        action='store_true',
                        help='Clear device temporary directory')
    args = parser.parse_args()

    print("Started OpenVINO™ Toolkit Android ARM benchmark statistics")

    bench_pipe = BenchmarkPipeline(args.intel_models_path,
                                   args.public_models_path,
                                   args.collect_statistics,
                                   args.precision,
                                   args.binaries_path,
                                   args.libraries_path,
                                   args.android_ndk_path,
                                   args.android_abi)
    if args.clear:
        bench_pipe.clear_environment()
        bench_pipe.check_environment()
    if not bench_pipe.send_bin_and_lib():
        print("Problem with send OpenVINO™ binary files and libraries")
    list_models_name = bench_pipe.get_list_models()
    for model_name in list_models_name:
        print("Name model: ", model_name)
        bench_pipe.send_model(model_name)
        bench_pipe.run_model(model_name)
        bench_pipe.get_per_layer_stat(model_name)
