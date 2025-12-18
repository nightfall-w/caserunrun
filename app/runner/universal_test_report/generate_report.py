"""
@FileName：generate_report.py
@Description：
@Author：baojun.wang
@Time：2025/10/14 14:21
"""
import argparse
import datetime

from app.runner.universal_test_report.parser import parse_test_results
from jinja2 import Environment, FileSystemLoader
import os


def generate_report(xml_dir: str, report_html_path: str):
    """
    生成HTML测试报告

    该函数解析XML格式的测试结果文件，使用Jinja2模板引擎渲染HTML报告，
    并将生成的报告保存到指定输出目录中。

    参数:
        xml_dir (str): 包含XML测试结果文件的目录路径
        output_dir (str): 生成HTML报告的输出目录路径

    返回值:
        None
    """
    # 解析XML测试结果并添加生成时间戳
    results, file_name = parse_test_results(xml_dir)
    results['generated_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 使用Jinja2模板引擎加载并渲染报告模板
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('templates/report_template.html')
    html_content = template.render(results=results)

    # 创建输出目录并写入HTML报告文件
    os.makedirs(os.path.dirname(report_html_path), exist_ok=True)
    with open(report_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Report generated at {report_html_path}")
    return True


if __name__ == "__main__":
    # 配置命令行参数解析器
    parser = argparse.ArgumentParser(description="Generate HTML report from XML test results")
    parser.add_argument('--input', required=True, help='Path to XML report folder')
    parser.add_argument('--output', required=True, help='Path to output HTML folder')
    args = parser.parse_args()
    generate_report(args.input, args.output)
