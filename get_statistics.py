#!/usr/bin/python

import argparse
import os


class BenchmarkPipeline:
    home_dir = "/data/local/tmp"
    cmd_line = ['/usr/bin/adb']
    dl_models = {}

    def __init__(self,
                 _intel_models,
                 _public_models,
                 _statistics,
                 _precision,
                 _binaries_path,
                 _libraries_path):
        self.intel_models = _intel_models
        self.public_models = _public_models
        self.statistics = _statistics
        self.precision = _precision
        self.binaries_path = _binaries_path
        self.libraries_path = _libraries_path

    @staticmethod
    def run_cmd(cmd):
        cmd_line = " ".join(str(item) for item in cmd)
        os.system(cmd_line)

    def clear_environment(self):
        cmd_line = self.cmd_line.copy()
        cmd_line.append('shell')
        cmd_line.append('\"')
        cmd_line.append('rm -rf')
        cmd_line.append(self.home_dir + '/*')
        cmd_line.append('\"')
        self.run_cmd(cmd_line)
        print("--- Cleared environment")
        return True

    def check_environment(self):
        cmd_line = self.cmd_line.copy()
        cmd_line.append('shell')
        cmd_line.append('\"')
        cmd_line.append('ls -l')
        cmd_line.append(self.home_dir)
        cmd_line.append('\"')
        self.run_cmd(cmd_line)
        print("--- Checked environment")
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

    def send_bin_and_lib(self, app_name):
        cmd_line = self.cmd_line.copy()
        cmd_line.append("push")

        app_path = os.path.join(self.binaries_path, app_name)
        if os.path.isfile(app_path):
            cmd_line.append(app_path)
        else:
            return False
        if os.path.isdir(self.libraries_path):
            cmd_line.append(self.libraries_path)
        else:
            return False
        cmd_line.append(self.home_dir)
        cmd_line.append('$> /dev/null')
        self.run_cmd(cmd_line)
        print("--- Sent bin: ", app_path)
        print("--- Sent libs: ", self.libraries_path)
        return True

    def send_model(self, model_path):
        cmd_line = self.cmd_line.copy()
        cmd_line.append("push")
        cmd_line.append(model_path)
        cmd_line.append(self.home_dir)
        cmd_line.append('$> /dev/null')
        self.run_cmd(cmd_line)
        print("--- Sent model: ", model_path)


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
    args = parser.parse_args()

    print("Started OpenVINO™ Toolkit Android ARM benchmark statistics")

    bench_pipe = BenchmarkPipeline(args.intel_models_path,
                                   args.public_models_path,
                                   args.collect_statistics,
                                   args.precision,
                                   args.binaries_path,
                                   args.libraries_path)
    bench_pipe.clear_environment()
    bench_pipe.check_environment()
    if not bench_pipe.send_bin_and_lib('benchmark_app'):
        print("Problem with send OpenVINO™ binary files and libraries")
    list_models_name = bench_pipe.get_list_models()
    for model_name in list_models_name:
        bench_pipe.send_model(bench_pipe.dl_models[model_name])

