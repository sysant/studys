# version 1.0 by san at 2024-08-30
# python source code to pyc

import os
import compileall
import shutil
import re
import sys

# 将__pycache__目录中的pyc移动到原始py文件位置 ,并删除__pycache__目录
def replace_pyc_with_py(project_dir):
    pyc_pattern = re.compile(r'(.+)\.cpython-\d{2,3}\.pyc$')

    for root, dirs, files in os.walk(project_dir):
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')

            for file_name in os.listdir(pycache_dir):
                pyc_match = pyc_pattern.match(file_name)
                if pyc_match:
                    original_py_file_name = f"{pyc_match.group(1)}.pyc"
                    pyc_file_path = os.path.join(pycache_dir, file_name)
                    original_py_file_path = os.path.join(root, original_py_file_name)

                    # 将 .pyc 文件移动并替换原始 .py 文件
                    shutil.move(pyc_file_path, original_py_file_path)
                    print(f"Replaced {original_py_file_path} with {pyc_file_path}")

            # 删除空的 __pycache__ 目录
            if not os.listdir(pycache_dir):
                os.rmdir(pycache_dir)
                print(f"Deleted empty directory: {pycache_dir}")


# 编译并删除原始 .py 文件的函数
def process_directory(directory, exclude_py):
    print(f"Processing directory: {directory}")
    
    # 编译目录中的所有 Python 文件为 .pyc
    compileall.compile_dir(directory, force=True)
    
    # 删除目录中的所有 .py 文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file not in exclude_py:
                py_file_path = os.path.join(root, file)
                print(f"Deleting file: {py_file_path}")
                os.remove(py_file_path)

    # 在替换并删除所有 .py 文件后，处理 .pyc 文件替换
    replace_pyc_with_py(directory)

def list_subdirectories(directory):
    # 获取指定目录下的所有子目录
    subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return subdirs

if __name__ == "__main__":
    prodir = sys.argv[1]
    project_directory = f'{prodir}' 
    exclude_py = ['settings.py']
#    project_directory = os.path.dirname(os.path.abspath(__file__)) 
#    print("--------",project_directory)

    # 列出所有子目录
    directories = list_subdirectories(project_directory)
    print("Subdirectories:", directories)

    # 遍历每个子目录并进行处理
    for directory in directories:
        dir_path = os.path.join(project_directory, directory)
        if os.path.exists(dir_path):
            process_directory(dir_path, exclude_py)
        else:
            print(f"Directory does not exist: {directory}")

