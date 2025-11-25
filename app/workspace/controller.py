"""
@FileName：controller.py
@Description：工作空间相关模型的增删改查操作
@Author：baojun.wang
"""
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_sync_db
from app.user.controller import get_user_by_username
from app.workspace.models import Workspace, MemberRole, WorkspaceMember
from utils.custom_logging import logger


class WorkspaceCRUD:
    """工作空间相关操作类"""

    def __init__(self, db: Session):
        self.db = db

    # Workspace 相关操作
    def create_workspace(
            self,
            workspace_name: str,
            workspace_desc: Optional[str],
            create_user: str,
            update_user: str,
            manager: List[str]
    ) -> Optional[Workspace]:
        """创建工作空间"""
        try:
            workspace = Workspace(
                workspace_name=workspace_name,
                workspace_desc=workspace_desc,
                create_user=create_user,
                update_user=update_user,
                manager=manager
            )
            self.db.add(workspace)
            self.db.commit()
            self.db.refresh(workspace)
            return workspace
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"创建工作空间失败: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建工作空间异常: {str(e)}")
            return None

    def get_workspace_by_id(self, workspace_id: int) -> Optional[Workspace]:
        """根据ID获取工作空间"""
        stmt = select(Workspace).where(Workspace.workspace_id == workspace_id)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_workspaces_with_count(
            self,
            workspace_name: Optional[str] = None,
            limit: int = 10,
            offset: int = 0
    ) -> Tuple[List[Workspace], int]:
        """获取工作空间列表及总数"""

        # 构建查询条件
        if workspace_name:
            # 根据名称模糊查询工作空间（包含查找）
            count_stmt = select(func.count()).select_from(Workspace).where(
                Workspace.workspace_name.like(f"%{workspace_name}%")
            )
            stmt = select(Workspace).where(
                Workspace.workspace_name.like(f"%{workspace_name}%")
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)
        else:
            # 查询所有工作空间
            count_stmt = select(func.count()).select_from(Workspace)
            stmt = select(Workspace).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)

        # 查询总数
        count_result = self.db.execute(count_stmt)
        total_count = count_result.scalar()

        # 查询当前页数据
        result = self.db.execute(stmt)
        workspaces = result.scalars().all()

        return workspaces, total_count

    # 在 controller.py 文件中添加以下方法到 WorkspaceCRUD 类中

    def get_my_workspaces_with_count(
            self,
            username: str,
            workspace_name: Optional[str] = None,
            limit: int = 10,
            offset: int = 0
    ) -> Tuple[List[Workspace], int]:
        """获取我所在的工作空间列表及总数"""

        # 先查询我所在的workspace_id列表
        member_subquery = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.username == username
        ).distinct()

        # 构建主查询
        if workspace_name:
            # 根据名称模糊查询我所在的工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                and_(
                    Workspace.workspace_id.in_(member_subquery),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            )
            stmt = select(Workspace).where(
                and_(
                    Workspace.workspace_id.in_(member_subquery),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)
        else:
            # 查询我所在的所有工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                Workspace.workspace_id.in_(member_subquery)
            )
            stmt = select(Workspace).where(
                Workspace.workspace_id.in_(member_subquery)
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)

        # 查询总数
        count_result = self.db.execute(count_stmt)
        total_count = count_result.scalar()

        # 查询当前页数据
        result = self.db.execute(stmt)
        workspaces = result.scalars().all()

        return workspaces, total_count

    def get_not_my_workspaces_with_count(
            self,
            username: str,
            workspace_name: Optional[str] = None,
            limit: int = 10,
            offset: int = 0
    ) -> Tuple[List[Workspace], int]:
        """获取我不在的工作空间列表及总数"""

        # 先查询我不在的workspace_id列表
        member_subquery = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.username == username
        ).distinct()

        # 构建主查询
        if workspace_name:
            # 根据名称模糊查询我不在的工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                and_(
                    ~Workspace.workspace_id.in_(member_subquery),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            )
            stmt = select(Workspace).where(
                and_(
                    ~Workspace.workspace_id.in_(member_subquery),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)
        else:
            # 查询我不在的所有工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                ~Workspace.workspace_id.in_(member_subquery)
            )
            stmt = select(Workspace).where(
                ~Workspace.workspace_id.in_(member_subquery)
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)

        # 查询总数
        count_result = self.db.execute(count_stmt)
        total_count = count_result.scalar()

        # 查询当前页数据
        result = self.db.execute(stmt)
        workspaces = result.scalars().all()

        return workspaces, total_count

    def get_my_manager_workspaces_with_count(
            self,
            username: str,
            workspace_name: Optional[str] = None,
            limit: int = 10,
            offset: int = 0
    ) -> Tuple[List[Workspace], int]:
        """获取我管理的工作空间列表及总数"""

        # 构建查询条件
        if workspace_name:
            # 根据名称模糊查询我管理的工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                and_(
                    func.json_contains(Workspace.manager, f'"{username}"'),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            )
            stmt = select(Workspace).where(
                and_(
                    func.json_contains(Workspace.manager, f'"{username}"'),
                    Workspace.workspace_name.like(f"%{workspace_name}%")
                )
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)
        else:
            # 查询我管理的所有工作空间
            count_stmt = select(func.count()).select_from(Workspace).where(
                func.json_contains(Workspace.manager, f'"{username}"')
            )
            stmt = select(Workspace).where(
                func.json_contains(Workspace.manager, f'"{username}"')
            ).order_by(Workspace.workspace_id.desc()).limit(limit).offset(offset)

        # 查询总数
        count_result = self.db.execute(count_stmt)
        total_count = count_result.scalar()

        # 查询当前页数据
        result = self.db.execute(stmt)
        workspaces = result.scalars().all()

        return workspaces, total_count

    def update_workspace(
            self,
            workspace_id: int,
            workspace_name: Optional[str] = None,
            workspace_desc: Optional[str] = None,
            update_user: str = None,
            manager: Optional[List[str]] = None
    ) -> bool:
        """更新工作空间"""
        try:
            stmt = update(Workspace).where(Workspace.workspace_id == workspace_id)
            values = {}

            if workspace_name is not None:
                values["workspace_name"] = workspace_name
            if workspace_desc is not None:
                values["workspace_desc"] = workspace_desc
            if update_user is not None:
                values["update_user"] = update_user
            if manager is not None:
                values["manager"] = manager

            if values:
                stmt = stmt.values(**values)
                self.db.execute(stmt)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新工作空间失败: {str(e)}")
            return False

    def delete_workspace(self, workspace_id: int) -> bool:
        """删除工作空间（会级联删除相关成员）"""
        try:
            # 先删除相关成员
            self.delete_members_by_workspace(workspace_id)

            # 再删除工作空间
            stmt = delete(Workspace).where(Workspace.workspace_id == workspace_id)
            self.db.execute(stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工作空间失败: {str(e)}")
            return False

    # MemberRole 相关操作
    def create_member_role(
            self,
            role_name: str,
            role_description: Optional[str] = None
    ) -> Optional[MemberRole]:
        """创建成员角色"""
        try:
            role = MemberRole(
                role_name=role_name,
                role_description=role_description
            )
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            return role
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"创建成员角色失败: {str(e)}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建成员角色异常: {str(e)}")
            return None

    def get_role_by_id(self, role_id: int) -> Optional[MemberRole]:
        """根据ID获取角色"""
        stmt = select(MemberRole).where(MemberRole.role_id == role_id)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_role_by_name(self, role_name: str) -> Optional[MemberRole]:
        """根据名称获取角色"""
        stmt = select(MemberRole).where(MemberRole.role_name == role_name)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_all_roles(self) -> List[MemberRole]:
        """获取所有角色"""
        stmt = select(MemberRole).where(MemberRole.role_name != MemberRole.ADMIN)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def update_role(
            self,
            role_id: int,
            role_name: Optional[str] = None,
            role_description: Optional[str] = None
    ) -> bool:
        """更新角色信息"""
        try:
            stmt = update(MemberRole).where(MemberRole.role_id == role_id)
            values = {}

            if role_name is not None:
                values["role_name"] = role_name
            if role_description is not None:
                values["role_description"] = role_description

            if values:
                stmt = stmt.values(**values)
                self.db.execute(stmt)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新角色失败: {str(e)}")
            return False

    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        try:
            # 检查是否有成员使用此角色
            member_count = self.count_members_by_role(role_id)
            if member_count > 0:
                logger.warning(f"角色ID {role_id} 仍有 {member_count} 个成员在使用，无法删除")
                return False

            stmt = delete(MemberRole).where(MemberRole.role_id == role_id)
            self.db.execute(stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除角色失败: {str(e)}")
            return False

    # WorkspaceMember 相关操作
    def add_member_to_workspace(
            self,
            workspace_id: int,
            username: str,
            role_id: int
    ) -> Optional[WorkspaceMember]:
        """添加成员到工作空间"""
        try:
            # 检查工作空间是否存在
            workspace = self.get_workspace_by_id(workspace_id)
            if not workspace:
                logger.error(f"工作空间 {workspace_id} 不存在")
                raise Exception(f"工作空间 {workspace_id} 不存在")

            # 检查角色是否存在
            role = self.get_role_by_id(role_id)
            if not role:
                logger.error(f"角色 {role_id} 不存在")
                raise Exception(f"角色ID {role_id} 不存在")

            # 检查用户在此workspace是否已经存在
            member = self.get_member_by_username_and_workspace(username, workspace_id)
            if member:
                logger.error(f"用户 {username} 已经在此工作空间 {workspace_id} 中")
                raise Exception(f"用户 {username} 已经在此工作空间 {workspace_id} 中")

            member = WorkspaceMember(
                workspace_id=workspace_id,
                username=username,
                role_id=role_id
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)
            return member
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"添加成员到工作空间失败: {str(e)}")
            raise Exception("添加成员到工作空间失败")
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加成员到工作空间异常: {str(e)}")
            raise Exception("添加成员到工作空间异常")

    def get_member_by_id(self, member_id: int) -> Optional[WorkspaceMember]:
        """根据ID获取成员"""
        stmt = select(WorkspaceMember).where(WorkspaceMember.id == member_id)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_member_by_username_and_workspace(self, username: str, workspace_id: int) -> Optional[WorkspaceMember]:
        """根据用户名与workspace获取成员"""
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.username == username,
            WorkspaceMember.workspace_id == workspace_id
        )
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_members_by_workspace_with_count(self, workspace_id: int, limit: int = 10, offset: int = 0) -> Tuple[
        List[WorkspaceMember], int]:
        """获取工作空间的成员及总数"""
        # 查询总数
        count_stmt = select(func.count()).select_from(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id)
        count_result = self.db.execute(count_stmt)
        total_count = count_result.scalar()

        # 查询当前页数据
        stmt = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id).limit(limit).offset(offset)
        result = self.db.execute(stmt)
        members = result.scalars().all()

        return members, total_count

    def get_members_by_role(self, role_id: int) -> List[WorkspaceMember]:
        """根据角色获取成员"""
        stmt = select(WorkspaceMember).where(WorkspaceMember.role_id == role_id)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def update_member(
            self,
            member_id: int,
            role_id: Optional[int] = None
    ) -> bool:
        """更新成员信息"""
        try:
            stmt = update(WorkspaceMember).where(WorkspaceMember.id == member_id)
            values = {}

            if role_id is not None:
                # 检查角色是否存在
                role = self.get_role_by_id(role_id)
                if not role:
                    logger.error(f"角色 {role_id} 不存在")
                    return False
                values["role_id"] = role_id

            if values:
                stmt = stmt.values(**values)
                self.db.execute(stmt)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新成员失败: {str(e)}")
            return False

    def remove_member_from_workspace(self, member_id: int) -> bool:
        """从工作空间移除成员"""
        try:
            stmt = delete(WorkspaceMember).where(WorkspaceMember.id == member_id)
            self.db.execute(stmt)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"移除成员失败: {str(e)}")
            return False

    def delete_members_by_workspace(self, workspace_id: int) -> int:
        """删除工作空间的所有成员"""
        try:
            stmt = delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除工作空间成员失败: {str(e)}")
            return 0

    def count_members_by_role(self, role_id: int) -> int:
        """统计使用某角色的成员数量"""
        stmt = select(WorkspaceMember).where(WorkspaceMember.role_id == role_id)
        result = self.db.execute(stmt)
        return len(result.scalars().all())

    # 关联查询操作
    def get_workspace_with_members(self, workspace_id: int) -> Optional[Dict]:
        """获取工作空间及其成员信息"""
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            return None

        members, total_count = self.get_members_by_workspace_with_count(workspace_id)

        # 获取成员角色信息
        member_details = []

        for member in members:
            role = self.get_role_by_id(member.role_id)
            userinfo = get_user_by_username(db=self.db, username=member.username)
            member_details.append({
                "member_id": member.id,
                "member_info": {
                    "username": userinfo.username,
                    "nickname": userinfo.nickname,
                    "email": userinfo.email,
                    "is_deleted": userinfo.is_deleted
                },
                "role": {
                    "role_id": role.role_id if role else None,
                    "role_name": role.role_name if role else None,
                    "role_description": role.role_description if role else None
                },
                "join_time": member.join_time,
                "create_time": member.create_time
            })

        return {
            "workspace": {
                "workspace_id": workspace.workspace_id,
                "workspace_name": workspace.workspace_name,
                "workspace_desc": workspace.workspace_desc,
                "create_user": workspace.create_user,
                "update_user": workspace.update_user,
                "manager": workspace.manager,
                "create_time": workspace.create_time,
                "update_time": workspace.update_time
            },
            "members": member_details
        }

    def get_member_with_details(self, member_id: int) -> Optional[Dict]:
        """获取成员详细信息（包含工作空间和角色信息）"""
        member = self.get_member_by_id(member_id)
        if not member:
            return None

        workspace = self.get_workspace_by_id(member.workspace_id)
        role = self.get_role_by_id(member.role_id)

        userinfo = get_user_by_username(db=self.db, username=member.username)
        return {
            "member": {
                "member_id": member.id,
                "member_info": {
                    "username": userinfo.username,
                    "nickname": userinfo.nickname,
                    "email": userinfo.email,
                    "is_deleted": userinfo.is_deleted
                },
                "join_time": member.join_time,
                "create_time": member.create_time,
                "update_time": member.update_time
            },
            "workspace": {
                "workspace_id": workspace.workspace_id if workspace else None,
                "workspace_name": workspace.workspace_name if workspace else None
            },
            "role": {
                "role_id": role.role_id if role else None,
                "role_name": role.role_name if role else None,
                "role_description": role.role_description if role else None
            }
        }

    def get_role_by_role_name(self, role_name):
        stmt = select(MemberRole).where(MemberRole.role_name == role_name)
        return self.db.execute(stmt).scalars().first()


# 依赖注入函数
def get_workspace_crud(db: get_sync_db) -> WorkspaceCRUD:
    """获取工作空间CRUD实例"""
    return WorkspaceCRUD(db)
