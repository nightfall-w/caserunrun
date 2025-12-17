<template>
  <div class="workspace-config-container">
    <div v-if="hasPermission" class="main-content">
      <div class="page-header">
        <div class="header-main">
          <div class="header-left">
            <h1 class="page-title">工作空间配置管理</h1>
          </div>
          <div class="header-right">
            <el-button
              type="primary"
              @click="goToWorkspaceDetail"
              class="back-btn"
              size="small"
            >
              返回工作空间
            </el-button>
          </div>
        </div>
        <div class="header-description">
          <p>管理工作空间级别的配置项</p>
        </div>
      </div>

      <!-- 配置项表格 -->
      <div class="table-container">
        <el-table
          :data="configList"
          v-loading="loading"
          style="width: 100%"
          class="config-table"
          header-row-class-name="table-header"
          row-class-name="table-row"
          size="small"
        >
          <el-table-column prop="key" label="键名" min-width="150">
            <template #default="scope">
              <span class="key-text">{{ scope.row.key }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="值" min-width="180">
            <template #default="scope">
              <div class="value-cell">
                <span class="value-text">{{ scope.row.value }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="desc" label="描述" min-width="200">
            <template #default="scope">
              <div class="desc-cell">
                <span class="desc-text">{{ scope.row.desc }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="100" align="center">
            <template #default="scope">
              <el-tag :type="getTypeTagType(scope.row.type)" class="type-tag">
                {{ getConfigTypeLabel(scope.row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="required" label="必填" width="80" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.required ? 'success' : 'info'" class="status-tag">
                {{ scope.row.required ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="verified" label="通过验证" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.verified ? 'success' : 'danger'" class="status-tag">
                {{ scope.row.verified ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="update_time" label="更新时间" width="160" align="center">
            <template #default="scope">
              <span class="time-text">{{ formatTime(scope.row.update_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="scope">
              <div class="action-cell">
                <el-button
                  size="small"
                  type="primary"
                  link
                  @click="openEditDialog(scope.row)"
                  class="action-button"
                >
                  编辑
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div v-else class="no-permission-container">
      <div class="no-permission-content">
        <el-icon class="no-permission-icon">
          <Lock/>
        </el-icon>
        <h2>访问被拒绝</h2>
        <p>您没有权限访问此页面。</p>
        <el-button type="primary" @click="goToHome">返回首页</el-button>
      </div>
    </div>

    <!-- 固定在底部的分页 -->
    <div v-if="hasPermission" class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        size="small"
      />
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-if="hasPermission"
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      :before-close="handleDialogClose"
      class="config-dialog"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configFormRules"
        label-width="80px"
        class="config-form"
        size="small"
      >
        <el-form-item label="键名" prop="key">
          <el-input
            v-model="configForm.key"
            placeholder="请输入配置项键名"
            disabled
            class="form-input"
          />
        </el-form-item>

        <el-form-item label="类型" prop="type">
          <el-select
            v-model="configForm.type"
            placeholder="请选择配置项类型"
            style="width: 100%"
            disabled
            class="form-select"
          >
            <el-option label="字符串" value="STRING"/>
            <el-option label="数字" value="NUMBER"/>
            <el-option label="布尔值" value="BOOLEAN"/>
            <el-option label="字典" value="DICT"/>
            <el-option label="列表" value="LIST"/>
          </el-select>
        </el-form-item>

        <el-form-item
          label="值"
          prop="value"
          :required="configForm.required"
        >
          <el-input
            v-model="configForm.value"
            type="textarea"
            placeholder="请输入配置项值"
            :rows="3"
            @input="handleValueInput"
            class="form-textarea"
          />
          <div class="value-preview-container">
            <div class="value-preview"
                 v-if="valuePreview && (configForm.required || configForm.value)">
              <div class="preview-label">值预览:</div>
              <div class="preview-content">
                <pre>{{ valuePreview }}</pre>
              </div>
              <div class="preview-type"
                   :class="{ 'success': isValueTypeValid, 'error': !isValueTypeValid }">
                类型检查: {{ valueTypeCheckMessage }}
              </div>
            </div>
            <div class="value-preview" v-else-if="!configForm.required && !configForm.value">
              <div class="preview-type">
                非必填项，值可以为空
              </div>
            </div>
            <div class="value-preview" v-else-if="configForm.required && !configForm.value">
              <div class="preview-type error">
                必填项，值不能为空
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="描述" prop="desc">
          <el-input
            v-model="configForm.desc"
            type="textarea"
            placeholder="请输入配置项描述"
            :rows="4"
            class="form-textarea"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false"
                     class="footer-button cancel-button"
                     size="small">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitLoading"
            :disabled="configForm.required && !configForm.value"
            class="footer-button confirm-button"
            size="small"
          >
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>


<script setup>
import {ref, reactive, onMounted, computed} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Lock} from '@element-plus/icons-vue'
import {useRouter, useRoute} from 'vue-router'
import {
  getWorkspaceConfigList,
  updateWorkspaceConfig,
  checkGitLabToken
} from '@/network/api.js'

const router = useRouter()
const route = useRoute()

// 权限控制
const hasPermission = ref(true)

// 数据状态
const configList = ref([])
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)

// 值预览相关
const valuePreview = ref('')
const isValueTypeValid = ref(true)
const valueTypeCheckMessage = ref('')

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 表单
const configFormRef = ref()
const configForm = reactive({
  id: '',
  key: '',
  value: '',
  desc: '',
  type: 'STRING',
  required: false
})

// 表单验证规则
const configFormRules = {
  key: [
    {required: true, message: '请输入键名', trigger: 'blur'}
  ],
  value: computed(() => {
    return configForm.required
      ? [{required: true, message: '请输入值', trigger: 'blur'}]
      : [{required: false}]
  }),
  desc: [
    {required: true, message: '请输入描述', trigger: 'blur'}
  ],
  type: [
    {required: true, message: '请选择类型', trigger: 'change'}
  ]
}

// 对话框标题
const dialogTitle = computed(() => {
  return '编辑配置项'
})

// 组件挂载时获取数据
onMounted(() => {
  fetchConfigList()
})

// 获取配置列表
const fetchConfigList = async () => {
  loading.value = true
  try {
    const res = await getWorkspaceConfigList({
      workspace_id: route.params.id,
      page_num: pagination.currentPage,
      page_size: pagination.pageSize
    })

    if (res.code === 0) {
      configList.value = res.data.configs || []
      pagination.total = res.data.total || 0
    } else {
      ElMessage.error(res.message || '获取配置列表失败')
    }
  } catch (error) {
    if (error.message === '无权限访问') {
      hasPermission.value = false
    } else {
      ElMessage.error('获取配置列表失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '-'
  return new Date(timeString).toLocaleString('zh-CN')
}

// 获取配置类型标签
const getConfigTypeLabel = (type) => {
  const typeMap = {
    'STRING': '字符串',
    'NUMBER': '数字',
    'BOOLEAN': '布尔值',
    'DICT': '字典',
    'LIST': '列表'
  }
  return typeMap[type] || type
}

// 获取标签类型
const getTypeTagType = (type) => {
  const typeMap = {
    'STRING': '',
    'NUMBER': 'success',
    'BOOLEAN': 'warning',
    'DICT': 'info',
    'LIST': 'primary'
  }
  return typeMap[type] || ''
}

// 打开编辑对话框
const openEditDialog = (row) => {
  Object.assign(configForm, {
    id: row.id,
    key: row.key,
    value: row.value,
    desc: row.desc,
    type: row.type,
    required: row.required
  })
  if (row.required || row.value) {
    updateValuePreview(row.value, row.type)
  }
  dialogVisible.value = true
}

// 处理对话框关闭
const handleDialogClose = (done) => {
  ElMessageBox.confirm('确定要关闭对话框吗？未保存的更改将会丢失。')
    .then(() => {
      done()
    })
    .catch(() => {
      // 用户取消关闭
    })
}

// 处理值输入
const handleValueInput = (newValue) => {
  if (configForm.required || newValue) {
    updateValuePreview(newValue, configForm.type)
  }
}

// 检查字符串是否包含中文引号或英文引号
const checkStringQuotes = (value) => {
  const chineseQuotes = /[“”‘’]/;
  const englishQuotes = /["']/;

  if (chineseQuotes.test(value)) {
    return '错误: 字符串不能包含中文引号（“”‘’）';
  }

  if (englishQuotes.test(value)) {
    return '错误: 字符串不能包含英文引号（\'"）';
  }

  return null;
}

// 更新值预览
const updateValuePreview = (value, type) => {
  valuePreview.value = value || ''

  if (!value) {
    isValueTypeValid.value = true;
    valueTypeCheckMessage.value = '非必填项，值可以为空';
    return;
  }

  try {
    switch (type) {
      case 'STRING':
        const quoteError = checkStringQuotes(value);
        if (quoteError) {
          isValueTypeValid.value = false;
          valueTypeCheckMessage.value = quoteError;
        } else {
          isValueTypeValid.value = true;
          valueTypeCheckMessage.value = '字符串类型 ✓';
        }
        break;
      case 'NUMBER':
        const num = Number(value);
        if (isNaN(num)) {
          isValueTypeValid.value = false;
          valueTypeCheckMessage.value = '错误: 不是有效的数字';
        } else {
          isValueTypeValid.value = true;
          valueTypeCheckMessage.value = `数字类型 ✓ 解析为: ${num}`;
        }
        break;
      case 'BOOLEAN':
        if (value === 'true' || value === 'false') {
          isValueTypeValid.value = true;
          valueTypeCheckMessage.value = `布尔类型 ✓ 解析为: ${value === 'true'}`;
        } else {
          isValueTypeValid.value = false;
          valueTypeCheckMessage.value = '错误: 布尔值必须是 "true" 或 "false"';
        }
        break;
      case 'DICT':
      case 'LIST':
        JSON.parse(value);
        isValueTypeValid.value = true;
        valueTypeCheckMessage.value = `${type === 'DICT' ? '字典' : '列表'}类型 ✓`;
        break;
      default:
        isValueTypeValid.value = true;
        valueTypeCheckMessage.value = '未知类型';
    }
  } catch (e) {
    isValueTypeValid.value = false;
    if (type === 'DICT' || type === 'LIST') {
      valueTypeCheckMessage.value = `错误: 无效的JSON格式 - ${e.message}`;
    } else {
      valueTypeCheckMessage.value = `错误: 类型不匹配 - ${e.message}`;
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  // 如果是必填项但没有值，则不允许提交
  if (configForm.required && !configForm.value) {
    ElMessage.error('此配置项为必填项，值不能为空');
    return;
  }

  if ((configForm.required || configForm.value) && !isValueTypeValid.value) {
    ElMessage.error('值类型不匹配，请修正后再提交');
    return;
  }

  try {
    await configFormRef.value.validate();
    submitLoading.value = true;

    const res = await updateWorkspaceConfig({
      workspace_id: route.params.id,
      config_id: configForm.id,
      key: configForm.key,
      value: configForm.value,
      desc: configForm.desc,
      type: configForm.type,
      required: configForm.required
    });

    if (res.code === 0) {
      ElMessage.success('更新成功');
      dialogVisible.value = false;
      fetchConfigList();

      // 如果是GITLAB_API_URL或PRIVATE_TOKEN配置项，检查GitLab连接是否有效
      if (configForm.key === 'GITLAB_API_URL' || configForm.key === 'PRIVATE_TOKEN') {
        await checkGitLabConnection();
      }
    } else {
      ElMessage.error(res.message || '更新失败');
    }
  } catch (error) {
    if (error.message === '无权限访问') {
      hasPermission.value = false
    } else {
      ElMessage.error('更新失败: ' + error.message)
    }
  } finally {
    submitLoading.value = false
  }
}

// 检查GitLab连接是否有效
const checkGitLabConnection = async () => {
  try {
    // 获取GITLAB_API_URL和PRIVATE_TOKEN的值
    let gitlabUrl = '';
    let token = '';

    // 从当前配置列表中查找这两个配置项的值
    const gitlabUrlConfig = configList.value.find(config => config.key === 'GITLAB_API_URL');
    const tokenConfig = configList.value.find(config => config.key === 'PRIVATE_TOKEN');

    // 使用新保存的值或现有值
    if (configForm.key === 'GITLAB_API_URL') {
      gitlabUrl = configForm.value;
    } else if (gitlabUrlConfig) {
      gitlabUrl = gitlabUrlConfig.value;
    }

    if (configForm.key === 'PRIVATE_TOKEN') {
      token = configForm.value;
    } else if (tokenConfig) {
      token = tokenConfig.value;
    }

    // 查找配置项的ID用于更新verified字段
    const gitlabUrlConfigId = gitlabUrlConfig ? gitlabUrlConfig.id : null;
    const tokenConfigId = tokenConfig ? tokenConfig.id : null;

    // 如果两个配置项都有值，则检查连接
    if (gitlabUrl && token && gitlabUrlConfigId && tokenConfigId) {
      try {
        const checkRes = await checkGitLabToken({
          gitlab_url: gitlabUrl,
          token: token
        });

        if (checkRes.code === 0 && checkRes.data) {
          // 连接有效，更新verified字段为true
          await updateWorkspaceConfig({
            workspace_id: route.params.id,
            config_id: gitlabUrlConfigId,
            verified: true
          });

          await updateWorkspaceConfig({
            workspace_id: route.params.id,
            config_id: tokenConfigId,
            verified: true
          });

          // 重新获取配置列表以更新verified状态
          await fetchConfigList();

          // 连接有效
          ElMessageBox.alert(
            `<div style="display: flex; align-items: center; gap: 10px;">
              <img src="${checkRes.data.avatar_url}" style="width: 40px; height: 40px; border-radius: 50%;" />
              <div>
                GitLab连接有效！<br/>用户名: ${checkRes.data.username}<br/>姓名: ${checkRes.data.name}
              </div>
            </div>`,
            '连接检查结果',
            {
              type: 'success',
              dangerouslyUseHTMLString: true,
              confirmButtonText: '确定'
            }
          );
        } else {
          // 连接无效，更新verified字段为false
          await updateWorkspaceConfig({
            workspace_id: route.params.id,
            config_id: gitlabUrlConfigId,
            verified: false
          });

          await updateWorkspaceConfig({
            workspace_id: route.params.id,
            config_id: tokenConfigId,
            verified: false
          });

          // 重新获取配置列表以更新verified状态
          await fetchConfigList();

          // 连接无效
          ElMessageBox.alert(
            'GitLab连接无效，请检查配置！',
            '连接检查结果',
            {
              type: 'error',
              confirmButtonText: '确定'
            }
          );
        }
      } catch (error) {
        // 请求过程中出错，也更新verified字段为false
        await updateWorkspaceConfig({
          workspace_id: route.params.id,
          config_id: gitlabUrlConfigId,
          verified: false
        });

        await updateWorkspaceConfig({
          workspace_id: route.params.id,
          config_id: tokenConfigId,
          verified: false
        });

        // 重新获取配置列表以更新verified状态
        await fetchConfigList();

        // 检查过程中出错
        ElMessageBox.alert(
          '检查GitLab连接时发生错误，请检查配置！',
          '连接检查结果',
          {
            type: 'error',
            confirmButtonText: '确定'
          }
        );
      }
    } else {
      // 配置不完整，更新verified字段为false
      if (gitlabUrlConfigId) {
        await updateWorkspaceConfig({
          workspace_id: route.params.id,
          config_id: gitlabUrlConfigId,
          verified: false
        });
      }

      if (tokenConfigId) {
        await updateWorkspaceConfig({
          workspace_id: route.params.id,
          config_id: tokenConfigId,
          verified: false
        });
      }

      // 重新获取配置列表以更新verified状态
      await fetchConfigList();

      ElMessageBox.alert(
        '配置不完整，请同时配置GITLAB_API_URL和PRIVATE_TOKEN！',
        '连接检查结果',
        {
          type: 'warning',
          confirmButtonText: '确定'
        }
      );
    }
  } catch (error) {
    ElMessage.error('检查GitLab连接时发生错误: ' + error.message);
  }
}

// 分页相关
const handleSizeChange = (val) => {
  pagination.pageSize = val;
  pagination.currentPage = 1;
  fetchConfigList();
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val;
  fetchConfigList();
}

// 返回工作空间详情
const goToWorkspaceDetail = () => {
  router.push(`/workspace/${route.params.id}`)
}

// 返回首页
const goToHome = () => {
  router.push('/')
}
</script>


<style scoped>
.workspace-config-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  padding: 5px 5px 0 5px;
  box-sizing: border-box;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.page-header {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 10px 15px;
  margin-bottom: 10px;
  border: 1px solid #ebeef5;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-description p {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #918c8c;
}

.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.back-btn {
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 12px;
  padding: 6px 10px;
}

.table-container {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  height: calc(100% - 120px);
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
}

.config-table {
  border: none;
  flex: 1;
}

:deep(.table-header th) {
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e0 100%) !important;
  color: #1e293b !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  padding: 10px 0 !important;
  border-bottom: 1px solid #cbd5e1 !important;
  position: relative;
}

:deep(.table-row td) {
  padding: 8px 0 !important;
  font-size: 12px;
}

:deep(.table-row:hover td) {
  background-color: #f8fafc !important;
}

.type-tag,
.status-tag {
  margin: 0;
  border: none;
  font-weight: 500;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.key-text {
  font-weight: 500;
  color: #303133;
}

.value-cell {
  max-width: 200px;
}

.value-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #606266;
}

.desc-cell {
  max-width: 250px;
}

.desc-text {
  display: block;
  color: #606266;
  white-space: normal;
  word-break: break-all;
  line-height: 1.4;
}

.time-text {
  color: #909399;
  font-size: 12px;
}

.action-cell {
  display: flex;
  justify-content: center;
  gap: 5px;
}

.action-button {
  font-size: 12px;
  padding: 3px 6px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.action-button:hover {
  background-color: #e3f2fd;
  color: #1976d2 !important;
}

.pagination-container {
  background: white;
  padding: 10px 15px;
  border-top: 1px solid #ebeef5;
  box-shadow: 0 -1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: center;
  position: sticky;
  bottom: 0;
  z-index: 100;
  border-radius: 0 0 6px 6px;
  border: 1px solid #ebeef5;
  margin-top: 10px;
}

.config-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.config-dialog :deep(.el-dialog__header) {
  background-color: #f5f7fa;
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

.config-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.config-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.config-form {
  padding: 0;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
}

.value-preview-container {
  width: 100%;
  margin-top: 10px;
}

.value-preview {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid #e4e7ed;
}

.preview-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #606266;
}

.preview-content {
  background-color: white;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 8px;
  max-height: 100px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
}

.preview-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 12px;
  color: #303133;
}

.preview-type {
  font-weight: 500;
  color: #909399;
}

.preview-type.success {
  color: #67c23a;
}

.preview-type.error {
  color: #f56c6c;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0;
}

.footer-button {
  padding: 8px 20px;
  border-radius: 4px;
}

.cancel-button {
  border: 1px solid #dcdfe6;
  color: #606266;
}

.confirm-button {
  background-color: #409eff;
  border-color: #409eff;
}

.no-permission-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f8f9fa;
}

.no-permission-content {
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.no-permission-icon {
  font-size: 64px;
  color: #f56c6c;
  margin-bottom: 20px;
}

.no-permission-content h2 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
}

.no-permission-content p {
  margin: 0 0 20px 0;
  color: #606266;
  font-size: 16px;
}
</style>
