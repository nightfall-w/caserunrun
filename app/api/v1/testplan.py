"""
@FileName：testplan.py
@Description：测试计划API接口
@Author：baojun.wang
@Time：2025/12/1 18:12
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_middleware import get_current_user
from app.core.database import get_sync_db
from app.core.orm_tools import model_to_dict
from app.core.response import api_response, HttpErrcode
from app.testplan.models import CaseType
from app.user.controller import get_nickname_by_username
from app.user.request_models import CurrentUser
from app.testplan.controller import get_test_plan_crud
from app.testplan.request_models import (
    CreateTestPlanRequest,
    UpdateTestPlanRequest,
    TestPlanListRequest,
    AddTestCaseRequest,
    RemoveTestCaseRequest, BatchAddTestCaseRequest, TriggerTestPlanRequest, TestTasksListRequest, TestTaskDetailRequest
)
from utils.custom_logging import logger

router = APIRouter(prefix="/testplan", tags=["测试计划管理"])


@router.post("/create")
def create_test_plan(
        request: CreateTestPlanRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """创建测试计划"""
    crud = get_test_plan_crud(db)

    try:
        test_plan = crud.create_test_plan(
            workspace_id=request.workspace_id,
            plan_name=request.plan_name,
            description=request.description,
            test_environment=request.test_environment,
            execution_mode=request.execution_mode,
            enable_schedule=request.enable_schedule,
            schedule_cron_expression=request.schedule_cron_expression,
            enable_notification=request.enable_notification,
            wecom_webhooks=request.wecom_webhooks,
            lark_webhooks=request.lark_webhooks,
            dingtalk_webhooks=request.dingtalk_webhooks,
            creator=userinfo.username
        )

        return api_response(
            code=HttpErrcode.SUCCESS,
            data={
                "test_plan_id": test_plan.id,
                "plan_name": test_plan.plan_name,
                "description": test_plan.description,
                "test_environment": test_plan.test_environment,
                "execution_mode": test_plan.execution_mode,
                "create_time": test_plan.create_time
            }
        )
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"创建测试计划失败: {str(e)}")


@router.get("/detail/{test_plan_id}")
def get_test_plan_detail(
        test_plan_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """获取测试计划详情"""
    crud = get_test_plan_crud(db)
    test_plan = crud.get_test_plan_by_id(test_plan_id)

    if not test_plan:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="测试计划不存在")

    # 获取关联的测试用例
    associated_test_cases, invalid_test_cases = crud.get_test_cases_by_plan_id(test_plan_id)

    data = {
        "test_plan_id": test_plan.id,
        "plan_name": test_plan.plan_name,
        "description": test_plan.description,
        "test_environment": test_plan.test_environment,
        "execution_mode": test_plan.execution_mode,
        "enable_schedule": test_plan.enable_schedule,
        "schedule_task_id": test_plan.schedule_task_id,
        "enable_notification": test_plan.enable_notification,
        "wecom_webhooks": test_plan.wecom_webhooks,
        "lark_webhooks": test_plan.lark_webhooks,
        "dingtalk_webhooks": test_plan.dingtalk_webhooks,
        "total_case_count": test_plan.total_case_count,
        "running_task_count": test_plan.running_task_count,
        "pending_task_count": test_plan.pending_task_count,
        "create_time": test_plan.create_time,
        "update_time": test_plan.update_time,
        "associated_test_cases": associated_test_cases,
        "invalid_test_cases": invalid_test_cases
    }

    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.put("/update")
def update_test_plan(
        request: UpdateTestPlanRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """更新测试计划"""
    crud = get_test_plan_crud(db)
    test_plan = crud.get_test_plan_by_id(request.test_plan_id)

    if not test_plan:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="测试计划不存在")

    success = crud.update_test_plan(
        test_plan_id=request.test_plan_id,
        plan_name=request.plan_name,
        description=request.description,
        test_environment=request.test_environment,
        execution_mode=request.execution_mode,
        updater=userinfo.username,
        enable_schedule=request.enable_schedule,
        schedule_cron_expression=request.schedule_cron_expression,
        enable_notification=request.enable_notification,
        wecom_webhooks=request.wecom_webhooks,
        lark_webhooks=request.lark_webhooks,
        dingtalk_webhooks=request.dingtalk_webhooks
    )

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="更新测试计划失败")

    return api_response(code=HttpErrcode.SUCCESS, message="更新成功")


@router.delete("/delete/{test_plan_id}")
def delete_test_plan(
        test_plan_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """删除测试计划"""
    crud = get_test_plan_crud(db)
    test_plan = crud.get_test_plan_by_id(test_plan_id)

    if not test_plan:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="测试计划不存在")

    success = crud.delete_test_plan(test_plan_id)
    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="删除测试计划失败")

    return api_response(code=HttpErrcode.SUCCESS, message="删除成功")


@router.post("/list")
def list_test_plans(
        request: TestPlanListRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """获取测试计划列表"""
    crud = get_test_plan_crud(db)
    limit = request.page_size
    offset = (request.page_num - 1) * request.page_size

    test_plans, total = crud.get_test_plans_with_count(
        workspace_id=request.workspace_id,
        plan_name=request.plan_name,
        creator=request.creator,
        limit=limit,
        offset=offset
    )

    # for tp in test_plans:
    #     crud.update_plan_cases_count(tp.id)

    data = {
        "test_plans": [
            {
                "test_plan_id": tp.id,
                "plan_name": tp.plan_name,
                "description": tp.description,
                "test_environment": tp.test_environment,
                "execution_mode": tp.execution_mode,
                "total_case_count": tp.total_case_count,
                "creator": {"username": tp.create_user,
                            "nickname": get_nickname_by_username(db=db, username=tp.create_user)},
                "create_time": tp.create_time,
                "update_time": tp.update_time,
                "enable_schedule": tp.enable_schedule,
                "enable_notification": tp.enable_notification,
                "wecom_webhooks": tp.wecom_webhooks,
                "lark_webhooks": tp.lark_webhooks,
                "dingtalk_webhooks": tp.dingtalk_webhooks,
                "schedule_cron_expression": tp.schedule_cron_expression
            }
            for tp in test_plans
        ],
        "total": total
    }

    return api_response(code=HttpErrcode.SUCCESS, data=data)


@router.post("/case/add")
def add_test_case_to_plan(
        request: AddTestCaseRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """添加测试用例到测试计划"""
    crud = get_test_plan_crud(db)

    if request.case_type == CaseType.PYTEST:
        success = crud.add_pytest_case_to_plan(request.test_plan_id, request.case_uuid)
    elif request.case_type == "testng":
        success = crud.add_testng_case_to_plan(request.test_plan_id, request.case_uuid)
    else:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="不支持的用例类型")

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="添加测试用例失败")

    return api_response(code=HttpErrcode.SUCCESS, message="添加成功")


@router.post("/case/batch_add")
def batch_add_test_cases_to_plan(
        request: BatchAddTestCaseRequest,  # 新增批量添加请求模型
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """批量添加测试用例到测试计划"""
    crud = get_test_plan_crud(db)

    success_count = 0
    failed_cases = []

    for case_info in request.cases:
        try:
            if case_info.case_type == CaseType.PYTEST:
                success = crud.add_pytest_case_to_plan(request.test_plan_id, case_info.case_uuid)
            elif case_info.case_type == CaseType.TESTNG:
                success = crud.add_testng_case_to_plan(request.test_plan_id, case_info.case_uuid)
            else:
                failed_cases.append({
                    "case_uuid": case_info.case_uuid,
                    "case_type": case_info.case_type,
                    "reason": "不支持的用例类型"
                })
                continue

            if success:
                success_count += 1
            else:
                failed_cases.append({
                    "case_uuid": case_info.case_uuid,
                    "case_type": case_info.case_type,
                    "reason": "添加失败"
                })
        except Exception as e:
            failed_cases.append({
                "case_uuid": case_info.case_uuid,
                "case_type": case_info.case_type,
                "reason": str(e)
            })

    if failed_cases:
        message = f"成功添加{success_count}个用例，{len(failed_cases)}个用例添加失败"
        return api_response(
            code=HttpErrcode.SUCCESS,
            message=message,
            data={"failed_cases": failed_cases}
        )

    return api_response(code=HttpErrcode.SUCCESS, message=f"成功批量添加{success_count}个测试用例")


@router.delete("/case/clear/{test_plan_id}")
def clear_test_cases_from_plan(
        test_plan_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """清空测试计划中的所有测试用例"""
    crud = get_test_plan_crud(db)
    test_plan = crud.get_test_plan_by_id(test_plan_id)

    if not test_plan:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="测试计划不存在")

    try:
        # 清空用例关联
        crud.clear_cases_from_plan(test_plan_id)

        return api_response(code=HttpErrcode.SUCCESS, message="已清空测试计划中的所有测试用例")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"清空测试用例失败: {str(e)}")


@router.delete("/case/clearInvalid/{test_plan_id}")
def clear_test_cases_from_plan(
        test_plan_id: int,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """清空测试计划中的所有测试用例"""
    crud = get_test_plan_crud(db)
    test_plan = crud.get_test_plan_by_id(test_plan_id)

    if not test_plan:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="测试计划不存在")

    try:
        # 清空用例关联
        crud.clear_invalid_cases_from_plan(test_plan_id)

        return api_response(code=HttpErrcode.SUCCESS, message="已清空测试计划中的所有测试用例")
    except Exception as e:
        return api_response(code=HttpErrcode.EXCEPTION, message=f"清空测试用例失败: {str(e)}")


@router.post("/case/remove")
def remove_test_case_from_plan(
        request: RemoveTestCaseRequest,
        db: Session = Depends(get_sync_db),
        userinfo: CurrentUser = Depends(get_current_user)
):
    """从测试计划移除测试用例"""
    crud = get_test_plan_crud(db)

    if request.case_type == CaseType.PYTEST:
        success = crud.remove_pytest_case_from_plan(request.test_plan_id, request.case_uuid)
    elif request.case_type == CaseType.TESTNG:
        success = crud.remove_testng_case_from_plan(request.test_plan_id, request.case_uuid)
    else:
        return api_response(code=HttpErrcode.PARAMS_ERROR, message="不支持的用例类型")

    if not success:
        return api_response(code=HttpErrcode.EXCEPTION, message="移除测试用例失败")

    return api_response(code=HttpErrcode.SUCCESS, message="移除成功")


@router.post("/trigger")
def trigger_test_plan(request: TriggerTestPlanRequest, db: Session = Depends(get_sync_db),
                      userinfo: CurrentUser = Depends(get_current_user)):
    """
    触发测试任务
    """
    test_plan_id = request.test_plan_id
    crud = get_test_plan_crud(db)
    try:
        crud.trigger_testplan(test_plan_id=test_plan_id, trigger_user=userinfo.username)
    except Exception as e:
        logger.error(f"触发测试计划失败: {str(e)}")
        return api_response(code=HttpErrcode.EXCEPTION, message=f"触发失败测试计划失败")
    return api_response(code=HttpErrcode.SUCCESS, message="触发成功")


@router.post("/tasks/list")
def get_test_tasks(request: TestTasksListRequest, db: Session = Depends(get_sync_db)):
    """
    查询测试任务列表
    """
    crud = get_test_plan_crud(db)
    try:
        test_tasks, total = crud.get_test_tasks_with_count(workspace_id=request.workspace_id,
                                                           test_plan_id=request.test_plan_id, page=request.page_num,
                                                           size=request.page_size)
        nickname_cache = {}
        test_tasks_list = []
        for task in test_tasks:
            if task.create_user not in nickname_cache:
                nickname_cache[task.create_user] = get_nickname_by_username(db=db, username=task.create_user)
            nickname = nickname_cache[task.create_user]
            task_info = model_to_dict(task)
            task_info['creator'] = {"username": task.create_user, "nickname": nickname}
            test_tasks_list.append(task_info)

        return api_response(data={"total": total, "test_tasks": test_tasks_list})
    except Exception as e:
        logger.error(f"查询测试任务列表失败: {str(e)}")
        return api_response(code=HttpErrcode.EXCEPTION, message=f"查询失败", data=None)


@router.post("/tasks/detail")
def get_test_task_detail(request: TestTaskDetailRequest, db: Session = Depends(get_sync_db)):
    """
    查询测试任务详情
    """
    crud = get_test_plan_crud(db)
    try:
        task, jobs = crud.get_task_detail(task_id=request.task_id)
        nickname = get_nickname_by_username(db=db, username=task.create_user)
        task_info = model_to_dict(task)
        task_info['creator'] = {"username": task.create_user, "nickname": nickname}
        task_info['jobs'] = [model_to_dict(job) for job in jobs]
        return api_response(data=task_info)
    except Exception as e:
        logger.error(f"查询测试任务详情失败: {str(e)}")
        return api_response(code=HttpErrcode.EXCEPTION, message=f"查询失败", data=None)
