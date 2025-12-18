import os
import xml.etree.ElementTree as ET


def parse_test_results(xml_dir):
    """
    解析指定目录下的TestNG测试结果XML文件，汇总测试用例执行情况。

    参数:
        xml_dir (str): 包含测试结果XML文件的目录路径。

    返回:
        dict: 测试结果摘要信息，包括总用例数、通过数、失败数、错误数以及每个测试用例的详细信息。
              结构如下：
              {
                  'total': int,           # 总测试用例数
                  'passed': int,          # 通过的测试用例数
                  'failed': int,          # 失败的测试用例数
                  'errors': int,          # 出现错误的测试用例数
                  'cases': [              # 所有测试用例详情列表
                      {
                          'name': str,         # 测试方法名
                          'classname': str,    # 所属类名
                          'time': str,         # 执行时间（秒）
                          'status': str,       # 状态 ('passed', 'failed', 'error')
                          'message': str,      # 错误/失败消息
                          'details': str,      # 错误/失败详细内容
                          'log': str,          # 系统输出日志(system-out)
                          'description': str,  # 描述信息（来自testng-results.xml）
                          'stack_trace': str,  # 完整堆栈跟踪信息
                          'testng_log': str    # TestNG原生日志内容
                      },
                      ...
                  ]
              }
    """

    summary = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'cases': []
    }

    # 存储从TEST-*.xml文件中提取的基础信息
    basic_case_info = {}

    # 第一步：解析TEST-*.xml文件，获取基础信息
    for file in os.listdir(xml_dir):
        if file.startswith('TEST-') and file.endswith('.xml'):
            tree = ET.parse(os.path.join(xml_dir, file))
            root = tree.getroot()

            for testcase in root.findall('.//testcase'):
                summary['total'] += 1

                # 获取系统输出日志
                system_out = testcase.find('.//system-out')
                log_output = system_out.text.strip() if system_out is not None and system_out.text else ''

                # 构建唯一标识符用于后续匹配
                case_name = testcase.attrib.get('name')
                classname = testcase.attrib.get('classname')
                case_id = f"{classname}.{case_name}"

                case = {
                    'name': case_name,
                    'classname': classname,
                    'time': testcase.attrib.get('time'),
                    'status': 'passed',
                    'message': '',
                    'details': '',
                    'log': log_output,
                    'description': '',  # 新增description字段
                    'stack_trace': '',  # 新增stack_trace字段
                    'testng_log': ''  # 新增testng_log字段用于存储testng原生日志
                }

                # 检查是否有失败或错误
                failure = testcase.find('failure')
                error = testcase.find('error')

                if failure is not None:
                    case['status'] = 'failed'
                    case['message'] = failure.attrib.get('message', '')
                    case['details'] = failure.text.strip() if failure.text else ''
                    summary['failed'] += 1
                elif error is not None:
                    case['status'] = 'error'
                    case['message'] = error.attrib.get('message', '')
                    case['details'] = error.text.strip() if error.text else ''
                    summary['errors'] += 1
                else:
                    summary['passed'] += 1

                # 将基础信息存储起来
                basic_case_info[case_id] = case
                summary['cases'].append(case)

    # 第二步：解析testng-results.xml文件，获取额外信息
    testng_results_file = os.path.join(xml_dir, 'testng-results.xml')
    if os.path.exists(testng_results_file):
        tree = ET.parse(testng_results_file)
        root = tree.getroot()

        # 先建立class到test-method的映射关系
        class_to_methods = {}
        for class_elem in root.findall('.//class'):
            classname = class_elem.attrib.get('name')
            if classname:
                class_to_methods[classname] = []
                for test_method in class_elem.findall('.//test-method'):
                    method_name = test_method.attrib.get('name')
                    if method_name:
                        class_to_methods[classname].append({
                            'method_name': method_name,
                            'element': test_method
                        })

        # 遍历所有test-method元素并补充详细信息
        for classname, methods in class_to_methods.items():
            for method_info in methods:
                method_name = method_info['method_name']
                test_method = method_info['element']

                case_id = f"{classname}.{method_name}"

                # 查找对应的基础信息
                if case_id in basic_case_info:
                    case_info = basic_case_info[case_id]
                    # 添加描述信息
                    case_info['description'] = test_method.attrib.get('description', '')

                    # 如果存在异常信息，则添加完整的堆栈跟踪
                    exception = test_method.find('.//exception')
                    if exception is not None:
                        full_stacktrace = exception.find('.//full-stacktrace')
                        if full_stacktrace is not None and full_stacktrace.text:
                            case_info['stack_trace'] = full_stacktrace.text.strip()

                    # 提取testng原生日志信息
                    reporter_output = test_method.find('.//reporter-output')
                    if reporter_output is not None:
                        lines = reporter_output.findall('.//line')
                        testng_logs = []
                        for line in lines:
                            if line.text:
                                testng_logs.append(line.text.strip())
                        if testng_logs:
                            case_info['testng_log'] = '\n'.join(testng_logs)

    return summary
