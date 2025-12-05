# -*- coding: utf-8 -*-
import logging
import os

from dotenv import load_dotenv
from funboost.utils.simple_data_class import DataClassBase
from nb_log import nb_log_config_default

load_dotenv()


class BrokerConnConfig(DataClassBase):
    """
    中间件连接配置
    此文件按需修改，例如你使用redis中间件作为消息队列，可以不用管rabbitmq mongodb kafka啥的配置。
    但有3个功能例外，如果你需要使用rpc模式或者分布式控频或者任务过滤功能，无论设置使用何种消息队列中间件都需要把redis连接配置好，
    如果@boost装饰器设置is_using_rpc_mode为True或者 is_using_distributed_frequency_control为True或do_task_filtering=True则需要把redis连接配置好，默认是False不强迫用户安装redis。
    """

    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_USERNAME = ''
    REDIS_PASSWORD = ''
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = 7  # redis消息队列所在db，请不要在这个db放太多其他键值对，以及方便你自己可视化查看你的redis db，框架里面有的功能会scan扫描unacked的键名，使用单独的db。
    REDIS_DB_FILTER_AND_RPC_RESULT = 8  # 如果函数做任务参数过滤 或者使用rpc获取结果，使用这个db，因为这个db的键值对多，和redis消息队列db分开
    REDIS_SSL = False  # 是否使用ssl加密,默认是False
    REDIS_URL = f'{"rediss" if REDIS_SSL else "redis"}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'


class FunboostCommonConfig(DataClassBase):
    # nb_log包的第几个日志模板，内置了7个模板，可以在你当前项目根目录下的nb_log_config.py文件扩展模板。
    # NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = 11  # 7是简短的不可跳转，5是可点击跳转的，11是可显示ip 进程 线程的模板,也可以亲自设置日志模板不传递数字。
    NB_LOG_FORMATER_INDEX_FOR_CONSUMER_AND_PUBLISHER = logging.Formatter(
        f'%(asctime)s-({nb_log_config_default.computer_ip},{nb_log_config_default.computer_name})-[p%(process)d_t%(thread)d] - %(name)s - "%(filename)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(task_id)s - %(message)s',
        "%Y-%m-%d %H:%M:%S", )  # 这个是带task_id的日志模板,日志可以显示task_id,方便用户串联起来排查某一个任务消息的所有日志.

    TIMEZONE = 'Asia/Shanghai'  # 时区

    # 以下配置是修改funboost的一些命名空间和启动时候的日志级别,新手不熟练就别去屏蔽日志了
    SHOW_HOW_FUNBOOST_CONFIG_SETTINGS = False  # 如果你单纯想屏蔽 "分布式函数调度框架会自动导入funboost_config模块当第一次运行脚本时候，函数调度框架会在你的python当前项目的根目录下 ...... "  这句话,
    FUNBOOST_PROMPT_LOG_LEVEL = logging.INFO  # funboost启动时候的相关提示语,用户可以设置这个命名空间的日志级别来调整
    KEEPALIVETIMETHREAD_LOG_LEVEL = logging.INFO  # funboost的作者发明的可缩小自适应线程池,用户对可变线程池的线程创建和销毁线程完全无兴趣,可以提高日志级别.
