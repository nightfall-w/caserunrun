<template>
  <div class="workspace-config-container">
    <div v-if="hasPermission" class="main-content">
      <div class="page-header">
        <div class="header-main">
          <div class="header-left">
            <h1 class="page-title">工作空间配置管理</h1>
            <div class="header-description">
              <p>管理工作空间级别的配置项</p>
            </div>
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
          height="calc(100vh - 180px)"
          empty-text="暂无配置项数据"
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
                <el-tooltip :content="scope.row.desc" placement="top" :show-after="200">
                  <span class="desc-text">{{ scope.row.desc }}</span>
                </el-tooltip>
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
                  @click="openEditDialog(scope.row)"
                  class="action-button"
                  :icon="Edit" circle
                >
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

    <!-- 编辑对话框 -->
    <el-dialog
      v-if="hasPermission"
      :title="dialogTitle"
      v-model="dialogVisible"
      width="550px"
      :before-close="handleDialogClose"
      class="config-dialog custom-dialog"
      destroy-on-close
    >
      <div class="dialog-header">
        <h3 class="dialog-title">{{ dialogTitle }}</h3>
      </div>
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configFormRules"
        label-width="90px"
        class="config-form custom-form"
        size="small"
      >
        <el-form-item label="键名" prop="key">
          <el-input
            v-model="configForm.key"
            placeholder="请输入配置项键名"
            disabled
            class="custom-input"
          />
        </el-form-item>

        <el-form-item label="类型" prop="type">
          <el-select
            v-model="configForm.type"
            placeholder="请选择配置项类型"
            style="width: 100%"
            disabled
            class="custom-select"
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
            class="custom-textarea"
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
            class="custom-textarea"
          />
        </el-form-item>
      </el-form>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false" class="footer-button cancel-button">取消
        </el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitLoading"
          :disabled="configForm.required && !configForm.value"
          class="footer-button confirm-button"
        >
          保存
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>


<script setup>
import {ref, reactive, onMounted, computed} from 'vue'
import {ElMessage, ElMessageBox, ElTooltip} from 'element-plus'
import {Lock, Edit} from '@element-plus/icons-vue'
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
  padding: 10px;
  box-sizing: border-box;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.page-header {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 15px 20px;
  margin-bottom: 15px;
  border: 1px solid #ebeef5;
  flex-shrink: 0;
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
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
}

.header-description p {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #7f8c8d;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.back-btn {
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 600;
  height: 42px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.back-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
}

.config-table {
  border: none;
  flex: 1;
}

/* 表格头部样式 */
:deep(.table-header th) {
  background: #f8fafc !important;
  color: #2c3e50 !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  padding: 18px 0 !important;
  border-bottom: 1px solid rgba(235, 238, 245, 0.5) !important;
  position: relative;
  text-align: center !important;
}

:deep(.table-header th):first-child {
  border-top-left-radius: 12px;
}

:deep(.table-header th):last-child {
  border-top-right-radius: 12px;
}

:deep(.table-header th:hover) {
  background: #edf2f7 !important;
}

/* 表格行样式 */
:deep(.table-row td) {
  color: #34495e;
  transition: all 0.3s ease;
  font-size: 15px;
  text-align: center;
  position: relative;
  overflow: hidden;
  padding: 16px 0 !important;
  border-color: rgba(235, 238, 245, 0.5) !important;
  background-color: rgba(250, 250, 250, 0.5) !important;
}

:deep(.table-row:nth-child(even) td) {
  background-color: rgba(255, 255, 255, 0.7) !important;
}

:deep(.table-row td::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}

:deep(.table-row:hover td) {
  background-color: transparent !important;
  color: #2c3e50;
  transform: scale(1.02);
}

:deep(.table-row:hover td::before) {
  opacity: 1;
}

/* 标签样式 */
:deep(.type-tag),
:deep(.status-tag) {
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 24px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-weight: 600;
}

:deep(.type-tag:hover),
:deep(.status-tag:hover) {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 文本样式 */
.key-text {
  font-weight: 700;
  color: #667eea;
  font-size: 14px;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 20px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.value-cell {
  max-width: 200px;
  margin: 0 auto;
}

.value-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
  color: #2c3e50;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(102, 126, 234, 0.05);
}

.value-text:hover {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.15);
  transform: translateX(5px);
}

.desc-cell {
  max-width: 250px;
  margin: 0 auto;
}

.desc-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
  color: #606266;
  font-weight: 500;
  transition: all 0.3s ease;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(102, 126, 234, 0.05);
}

.desc-text:hover {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.15);
  transform: translateX(5px);
}

.time-text {
  color: #7f8c8d;
  font-size: 14px;
}

.action-cell {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.action-button {
  padding: 6px 10px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.action-button:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

/* 弹窗美化核心样式 */
:deep(.config-dialog) {
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  width: 550px !important;
}

:deep(.config-dialog .el-dialog__header) {
  display: none;
}

:deep(.config-dialog .dialog-header) {
  padding: 20px 25px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  margin: -20px -25px 20px -25px;
  border-radius: 12px 12px 0 0;
}

:deep(.config-dialog .dialog-title) {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.3px;
}

:deep(.config-dialog .config-form) {
  padding: 0 15px;
}

:deep(.config-dialog .el-form-item) {
  margin-bottom: 20px;
  transition: all 0.2s ease;
  border-radius: 10px;
  padding: 10px;
}

:deep(.config-dialog .el-form-item:hover) {
  transform: translateX(3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

:deep(.config-dialog .el-form-item__label) {
  font-size: 14px;
  padding: 0 10px 6px 0;
  text-align: right;
  color: #475569;
  font-weight: 500;
}

:deep(.config-dialog .el-form-item__label .el-form-item__label-required) {
  color: #ef4444;
  margin-right: 3px;
}

/* 输入框美化 */
:deep(.config-dialog .form-input .el-input__wrapper),
:deep(.config-dialog .form-select .el-select__wrapper),
:deep(.config-dialog .form-textarea .el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) inset;
  transition: all 0.25s ease;
  height: 42px;
}

:deep(.config-dialog .form-input .el-input__wrapper:hover),
:deep(.config-dialog .form-select .el-select__wrapper:hover),
:deep(.config-dialog .form-textarea .el-textarea__inner:hover) {
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.1);
}

:deep(.config-dialog .form-input .el-input__wrapper.is-focus),
:deep(.config-dialog .form-select .el-select__wrapper.is-focused),
:deep(.config-dialog .form-textarea .el-textarea__inner:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  outline: none;
}

:deep(.config-dialog .el-textarea__inner) {
  min-height: 90px !important;
  resize: vertical;
  line-height: 1.6;
  font-size: 14px;
  border-radius: 8px;
}

/* 底部按钮区域 */
:deep(.config-dialog .dialog-footer) {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 25px 25px;
  border-top: 1px solid #f0f2f5;
  background-color: #f8fafc;
  margin: 15px -25px -25px -25px;
  border-radius: 0 0 12px 12px;
}

:deep(.config-dialog .footer-button) {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.config-dialog .cancel-button) {
  border: 1px solid #e2e8f0;
  color: #475569;
  background-color: #ffffff;
}

:deep(.config-dialog .cancel-button:hover) {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

:deep(.config-dialog .confirm-button) {
  background-color: #667eea;
  border-color: #667eea;
  color: white;
}

:deep(.config-dialog .confirm-button:hover) {
  background-color: #5a6fd8;
  border-color: #5a6fd8;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

:deep(.config-dialog .confirm-button:active) {
  transform: translateY(0);
}

/* 表单验证错误样式优化 */
:deep(.el-form-item.is-error .el-input__wrapper),
:deep(.el-form-item.is-error .el-select__wrapper),
:deep(.el-form-item.is-error .el-textarea__inner) {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15) !important;
}

:deep(.el-form-item__error) {
  font-size: 12px;
  color: #ef4444;
  margin-top: 4px;
  padding-left: 2px;
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

/* 响应式调整 */
@media (max-width: 768px) {
  :deep(.config-dialog) {
    width: 95% !important;
  }

  :deep(.config-dialog .el-form-item__label) {
    text-align: left;
    padding-bottom: 5px;
    display: block;
  }
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


