"""
@FileName：controller.py
@Description：系统配置和工作空间配置控制器
@Author：baojun.wang
@Time：2025/11/7 21:22
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.case_source.models import TokenType
from app.setting.models import SystemConfigModel, WorkspaceConfigModel
from utils.commonlib import get_host_ip


class SettingCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_system_config(self, key: str, value: str, desc: str, type: str, allowed_to_delete: bool = True,
                             required: bool = False) -> \
            Optional[SystemConfigModel]:
        """
        创建系统配置项
        """
        try:
            config = SystemConfigModel(
                key=key,
                value=value,
                desc=desc,
                type=type,
                allowed_to_delete=allowed_to_delete,
                required=required
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError:
            self.db.rollback()
            return None

    def get_system_config_by_key(self, key: str) -> Optional[SystemConfigModel]:
        """
        根据key获取系统配置项
        """
        return self.db.query(SystemConfigModel).filter(SystemConfigModel.key == key).first()

    def get_system_config_by_id(self, config_id: int) -> Optional[SystemConfigModel]:
        """
        根据ID获取系统配置项
        """
        return self.db.query(SystemConfigModel).filter(SystemConfigModel.id == config_id).first()

    def get_all_system_configs(self, page: int = 1, size: int = 20) -> Tuple[List[SystemConfigModel], int]:
        """
        获取所有系统配置项
        """
        query = self.db.query(SystemConfigModel)
        total = query.count()
        configs = query.offset((page - 1) * size).limit(size).all()
        return configs, total

    def update_system_config(self, config_id: int, **kwargs) -> bool:
        """
        更新系统配置项
        """
        try:
            config = self.db.query(SystemConfigModel).filter(SystemConfigModel.id == config_id).first()
            if not config:
                return False

            for key, value in kwargs.items():
                if hasattr(config, key) and key != 'id':
                    setattr(config, key, value)

            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False

    def delete_system_config(self, config_id: int) -> bool:
        """
        删除系统配置项
        """
        try:
            config = self.db.query(SystemConfigModel).filter(SystemConfigModel.id == config_id).first()
            if not config:
                return False

            # 不允许删除不允许删除的配置项
            if not config.allowed_to_delete:
                return False

            self.db.delete(config)
            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False

    def create_workspace_config(self, workspace_id: int, key: str, value: str, desc: str, type: str,
                                allowed_to_delete: bool = True, required: bool = False) -> Optional[
        WorkspaceConfigModel]:
        """
        创建工作空间配置项
        """
        try:
            config = WorkspaceConfigModel(
                workspace_id=workspace_id,
                key=key,
                value=value,
                desc=desc,
                type=type,
                allowed_to_delete=allowed_to_delete,
                required=required
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except SQLAlchemyError:
            self.db.rollback()
            return None

    def get_workspace_config_by_key(self, workspace_id: int, key: str) -> Optional[WorkspaceConfigModel]:
        """
        根据工作空间ID和key获取配置项
        """
        return self.db.query(WorkspaceConfigModel).filter(
            WorkspaceConfigModel.workspace_id == workspace_id,
            WorkspaceConfigModel.key == key
        ).first()

    def get_workspace_config_by_id(self, config_id: int) -> Optional[WorkspaceConfigModel]:
        """
        根据ID获取工作空间配置项
        """
        return self.db.query(WorkspaceConfigModel).filter(WorkspaceConfigModel.id == config_id).first()

    def get_workspace_configs(self, workspace_id: int, page: int = 1, size: int = 20) -> \
            Tuple[List[WorkspaceConfigModel], int]:
        """
        获取指定工作空间的所有配置项
        """
        query = self.db.query(WorkspaceConfigModel).filter(WorkspaceConfigModel.workspace_id == workspace_id)
        total = query.count()
        configs = query.offset((page - 1) * size).limit(size).all()
        return configs, total

    def update_workspace_config(self, config_id: int, **kwargs) -> bool:
        """
        更新工作空间配置项
        """
        try:
            config = self.db.query(WorkspaceConfigModel).filter(WorkspaceConfigModel.id == config_id).first()
            if not config:
                return False

            for key, value in kwargs.items():
                if hasattr(config, key) and key != 'id':
                    setattr(config, key, value)

            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False

    def delete_workspace_config(self, config_id: int) -> bool:
        """
        删除工作空间配置项
        """
        try:
            config = self.db.query(WorkspaceConfigModel).filter(WorkspaceConfigModel.id == config_id).first()
            if not config:
                return False

            # 不允许删除不允许删除的配置项
            if not config.allowed_to_delete:
                return False

            self.db.delete(config)
            self.db.commit()
            return True
        except SQLAlchemyError:
            self.db.rollback()
            return False

    def get_gitlab_credentials(self, token_type: str, workspace_id: int):
        """
        根据token类型获取GitLab凭证信息

        Args:
            db: 数据库会话
            token_type: token类型 (system/workspace)
            workspace_id: 工作空间ID

        Returns:
            tuple: (gitlab_url, token) 或抛出异常
        """
        if token_type == TokenType.SYSTEM.value:
            gitlab_url_config = self.get_system_config_by_key("GITLAB_API_URL")
            token_config = self.get_system_config_by_key("PRIVATE_TOKEN")
            if not gitlab_url_config or not token_config:
                raise ValueError("系统Git配置不完整")
            return gitlab_url_config.value, token_config.value
        else:
            gitlab_url_config = self.get_workspace_config_by_key(workspace_id, "GITLAB_API_URL")
            token_config = self.get_workspace_config_by_key(workspace_id, "PRIVATE_TOKEN")
            if not gitlab_url_config or not token_config:
                raise ValueError("工作空间Git配置不完整")
            return gitlab_url_config.value, token_config.value

    def get_server_domain(self):
        service_domain_config = self.get_system_config_by_key("SERVER_DOMAIN")
        return service_domain_config.value if service_domain_config else get_host_ip()


def get_setting_crud(db: Session) -> SettingCRUD:
    """
    获取配置CRUD实例
    """
    return SettingCRUD(db)
