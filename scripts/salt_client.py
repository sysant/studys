#!/bin/python3
import salt.client
import argparse

def execute_salt_command(target, function, arguments, tgt_type):
    # 初始化本地客户端
    client = salt.client.LocalClient()
    # 执行命令并获取结果
    result = client.cmd(target, function, arguments, tgt_type=tgt_type)
    return result

def parse_arguments():
    parser = argparse.ArgumentParser(description='Execute any Salt command on minions.')
    parser.add_argument('target', type=str, help='Target minions (e.g., "win20*" for glob or "win2012,win2016" for list)')
    parser.add_argument('function', type=str, help='Salt function to execute (e.g., "test.ping")')
    parser.add_argument('arguments', type=str, nargs='*', help='Arguments for the Salt function (if any)')
    parser.add_argument('--tgt-type', type=str, default='glob', choices=['glob', 'list', 'grain'],
                        help='Type of target (default: glob). Use "list" for comma-separated minion list.')
    return parser.parse_args()

def main():
    args = parse_arguments()

    # 根据目标类型选择合适的处理方式
    if args.tgt_type == 'list':
        # win2012和win2016两台主机: salt_client.py "win2012,win2016" cmd.run "ipconfig" --tgt-type list
        target_minions = args.target.split(',')
        tgt_type = 'list'
    elif args.tgt_type == 'grain':
        # 内核为Linux所有主机: salt_client.py "kernel:Linux" cmd.run "ifconfig" --tgt-type grain 
        target_minions = args.target
        tgt_type = 'grain'
    else:
        # 所有win开头的主机: salt_client.py "win20*" cmd.run "ifconfig" --tgt-type grain 
        target_minions = args.target
        tgt_type = 'glob'

    result = execute_salt_command(target_minions, args.function, args.arguments, tgt_type)

    # 打印结果
    for minion, output in result.items():
        print(f"Minion: {minion}\nOutput: {output}\n")

if __name__ == '__main__':
    main()
