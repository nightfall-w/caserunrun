"""
@FileName：orm_tools.py
@Description：
@Author：baojun.wang
@Time：2025/10/28 18:51
"""
from sqlalchemy import inspect


def model_to_dict(instance, exclude=None):
    """
    将 SQLAlchemy 模型实例转换为字典
    :param instance: SQLAlchemy 模型实例
    :param exclude: 要排除的字段列表
    :return: 字典形式的模型数据
    """
    if exclude is None:
        exclude = []

    # 获取模型的所有列
    insp = inspect(instance)
    attr_names = [c_attr.key for c_attr in insp.mapper.column_attrs]

    # 构造字典，排除指定字段
    result = {}
    for attr_name in attr_names:
        if attr_name not in exclude:
            result[attr_name] = getattr(instance, attr_name)

    return result
