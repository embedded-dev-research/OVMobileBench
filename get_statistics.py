#!/usr/bin/python

import argparse
import os


def clear_environment(cmd_line):
    cmd_line.append('\"rm -rf /data/local/tmp/*\"')
    os.system(" ".join(cmd_line))
    print("--- Cleared environment")
    return True


def check_environment(cmd_line):
    cmd_line.append('\"ls -l /data/local/tmp\"')
    os.system(" ".join(cmd_line))
    print("--- Checked environment")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenVINO™ Toolkit Android ARM benchmark statistics')
    parser.add_argument('--intel_models_path',
                        help='Path to OpenVINO™ Intel pre-trained models',
                        required=True)
    parser.add_argument('--public_models_path',
                        help='Path to OpenVINO™ public pre-trained models',
                        required=True)
    parser.add_argument('--collect_statistics', help='Path to collect files of benchmark statistics',
                        required=True)
    parser.add_argument('--precision', help='Path to collect files of benchmark statistics',
                        required=True,
                        choices=['FP32'])
    args = parser.parse_args()
    intel_models = args.intel_models_path
    public_models = args.public_models_path
    statistics = args.collect_statistics
    precision = args.precision

    command_line_list = ['/usr/bin/adb']

    print("Started OpenVINO™ Toolkit Android ARM benchmark statistics")
    env_cmd_line = command_line_list.copy()
    env_cmd_line.append("shell")
    if not clear_environment(env_cmd_line.copy()):
        exit()
    if not check_environment(env_cmd_line.copy()):
        exit()
