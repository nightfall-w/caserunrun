/*
 * @Descripttion: 接口统一管理文件
 * @version:
 * @Author: wangbaojun
 * @Date: 2025-06-02 10:00:00
 */

import request from './axios';

/**
 * 获取角色列表
 */
export function getRoleList() {
  return request.get('/api/v1/workspace/role/list');
}

/**
 * 注册
 */
export function register(params) {
  return request.post('/api/v1/user/register', params);
}

/**
 * 登录
 */
export function login(params) {
  return request.post('/api/v1/user/login', params);
}


/**
 * 获取我加入的工作空间列表
 */
export function getMyWorkspaces(params) {
  return request.post('/api/v1/workspace/my/list', params)
}

/**
 * 获取我未加的工作空间列表
 */
export function getMyUnWorkspaces(params) {
  return request.post('/api/v1/workspace/not-my/list', params)
}


/**
 * 获取我管理的工作空间列表
 */
export function getMyManageWorkspaces(params) {
  return request.post('/api/v1/workspace/my/manage/list', params)
}

/**
 * 创建工作空间
 * @param params
 */
export function createWorkspace(params) {
  return request.post('/api/v1/workspace/create', params)
}

/**
 * 更新工作空间
 * @param params
 */
export function updateWorkspace(params) {
  return request.put('/api/v1/workspace/update', params)
}

/**
 * 删除工作空间
 * @param params
 */
export function deleteWorkspace(params) {
  return request.delete('/api/v1/workspace/delete', params)
}

/**
 * 获取工作空间详情
 */
export function getWorkspaceDetail(params) {
  return request.get('/api/v1/workspace/detail', params)
}

/**
 * 获取工作空间成员详情
 */
export function getWorkspaceMemberDetail(params) {
  return request.get('/api/v1/workspace/member/detail', params)
}

/**
 * 申请加入工作空间
 */
export function joinWorkspace(params) {
  return request.post('/api/v1/workspace/member/join', params)
}

/**
 * 获取角色列表
 * @returns {Promise<AxiosResponse<any>>}
 */
export function getRolesList() {
  return request.get('/api/v1/workspace/role/list')
}

/**
 * 获取用户列表
 * @returns {Promise<AxiosResponse<any>>}
 */
export function getUserList(params) {
  return request.post('/api/v1/user/users/list', params)
}

/**
 * 创建系统配置
 * @param params
 */
export function createSystemConfig(params) {
  return request.post('/api/v1/setting/system-config/create', params)
}

/**
 * 获取系统配置详情
 * @param params
 */
export function getSystemConfigDetail(params) {
  return request.get('/api/v1/setting/system-config/detail', params)
}

/**
 * 获取系统配置列表
 * @param params
 */
export function getSystemConfigList(params) {
  return request.post('/api/v1/setting/system-config/list', params)
}

/**
 * 更新系统配置
 * @param params
 */
export function updateSystemConfig(params) {
  return request.put('/api/v1/setting/system-config/update', params)
}

/**
 * 删除系统配置
 * @param params
 */
export function deleteSystemConfig(params) {
  return request.delete('/api/v1/setting/system-config/delete', params)
}

/**
 * 创建工作空间配置
 * @param params
 */
export function createWorkspaceConfig(params) {
  return request.post('/api/v1/setting/workspace-config/create', params)
}

/**
 * 获取工作空间配置详情
 * @param params
 */
export function getWorkspaceConfigDetail(params) {
  return request.get('/api/v1/setting/workspace-config/detail', params)
}

/**
 * 获取工作空间配置列表
 * @param params
 */
export function getWorkspaceConfigList(params) {
  return request.post('/api/v1/setting/workspace-config/list', params)
}

/**
 * 更新工作空间配置
 * @param params
 */
export function updateWorkspaceConfig(params) {
  return request.put('/api/v1/setting/workspace-config/update', params)
}

/**
 * 删除工作空间配置
 * @param params
 */
export function deleteWorkspaceConfig(params) {
  return request.delete('/api/v1/setting/workspace-config/delete', params)
}

/**
 * 修改超级管理员
 */
export function updateSuperAdmin(params) {
  return request.post('/api/v1/user/super-admin/update', params);
}


/**
 * 获取额外管理员列表
 */
export function getExtraAdminList() {
  return request.get('/api/v1/user/super-admin/list');
}

/**
 * 绑定用例源
 */
export function bindCaseSource(params) {
  return request.post('/api/v1/case_source/bind', params);
}

/**
 * 更新用例源
 */
export function updateCaseSource(params) {
  return request.post('/api/v1/case_source/update', params);
}

/**
 * 获取用例源列表
 */
export function getCaseSourceList(params) {
  return request.post('/api/v1/case_source/list', params);
}

/**
 * 删除用例源
 */
export function deleteCaseSource(params) {
  return request.post('/api/v1/case_source/delete', params);
}

/**
 * 检查GitLabToken
 */
export function checkGitLabToken(params) {
  return request.post('/api/v1/case_source/checkToken', params);
}

/**
 * 获取GitLabToken配置信息
 */
export function getGitTokenVerifiedInfo(params) {
  return request.get('/api/v1/setting/gitTokenVerified/info', params);
}

/**
 * 获取workspace下的测试用例
 */
export function getTestCaseList(params) {
  return request.post('/api/v1/testcase/list', params);
}

/**
 * 获取用例内容与详情
 */
export function getTestCaseContentDetail(params) {
  return request.get('/api/v1/testcase/queryCaseContentDetail', params);
}

/**
 * 获取项目文件列表
 */
export function getProjectFileTree(params) {
  return request.get('/api/v1/testcase/getProjectFileTree', params);
}

/**
 * 获取python列表
 */
export function getPythonList() {
  return request.get('/api/v1/virtual-env/python-versions');
}

/**
 * 获取jdk列表
 */
export function getJavaList() {
  return request.get('/api/v1/virtual-env/java-versions');
}

/**
 * 创建虚拟环境
 */
export function createPythonVirtualEnv(params, timeout = 120000) {
  return request.post('/api/v1/virtual-env/create_python_virtual_environment', params, {timeout});
}

/**
 * 创建java虚拟环境
 */
export function createJavaVirtualEnv(params, timeout = 180000) {
  return request.post('/api/v1/virtual-env/create_java_virtual_environment', params, {timeout});
}

/**
 * 获取指定文件的内容
 */
export function getFileContent(params) {
  return request.get('/api/v1/case_source/queryFileContent', params);
}

/**
 * 获取默认的maven配置
 */
export function getDefaultMavenConfig() {
  return request.get('/api/v1/virtual-env/get_default_maven_setting');
}
