<template>
  <div class="case-source-manage-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-main">
        <div class="header-left">
          <h1 class="page-title">用例源管理</h1>
        </div>
        <div class="header-right">
          <div class="header-actions">
            <el-button
              type="primary"
              @click="checkGitTokenStatus"
              :loading="tokenStatusLoading"
              class="refresh-token-btn"
              size="small"
            >
              <el-icon>
                <Refresh/>
              </el-icon>
              刷新凭证
            </el-button>
            <el-button
              type="success"
              @click="openCreateDialog"
              class="add-source-btn"
              size="small"
            >
              <el-icon>
                <Plus/>
              </el-icon>
              添加用例源
            </el-button>
          </div>
        </div>
      </div>
      <div class="token-status-bar" v-if="tokenStatusChecked">
        <div class="token-status-item system-token"
             :class="{ 'valid': systemTokenValid, 'invalid': !systemTokenValid }">
          <el-icon class="token-status-icon">
            <SuccessFilled v-if="systemTokenValid"/>
            <CircleClose v-else/>
          </el-icon>
          <span class="token-status-text">系统凭证：{{
              systemTokenValid ? '有效' : '无效'
            }}</span>
        </div>
        <div v-if="hasWorkspaceToken" class="token-status-item workspace-token"
             :class="{ 'valid': workspaceTokenValid, 'invalid': !workspaceTokenValid }">
          <el-icon class="token-status-icon">
            <SuccessFilled v-if="workspaceTokenValid"/>
            <CircleClose v-else/>
          </el-icon>
          <span class="token-status-text">工作空间凭证：{{
              workspaceTokenValid ? '有效' : '无效'
            }}</span>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <!-- 用例源列表卡片 -->
      <div class="source-list-card">
        <div class="card-header">
          <h2 class="card-title">用例源列表</h2>
          <div class="card-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索项目名称或描述"
              clearable
              class="search-input"
              size="small"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon>
                  <Search/>
                </el-icon>
              </template>
            </el-input>
          </div>
        </div>

        <el-table
          :data="filteredCaseSourceList"
          v-loading="loading"
          style="width: 100%"
          class="source-table"
          header-row-class-name="table-header"
          row-class-name="table-row"
          height="calc(100vh - 180px)"
        >
          <el-table-column prop="specificType" label="测试类型" width="90" align="center">
            <template #default="scope">
              <el-tag :type="getSpecificTypeTagType(scope.row.specificType)" class="type-tag">
                {{ getSpecificTypeName(scope.row.specificType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="caseType" label="用例类型" width="90" align="center">
            <template #default="scope">
              <el-tag :type="getCaseTypeTagType(scope.row.caseType)" class="type-tag">
                {{ getCaseTypeName(scope.row.caseType) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="caseSourceValue.projectId" label="项目ID" width="80"
                           align="center"/>
          <el-table-column prop="caseProjectName" label="项目名称" min-width="120"/>
          <el-table-column prop="caseSourceValue.caseDir" label="用例目录" min-width="100">
            <template #default="scope">
              {{
                scope.row.caseSourceValue.caseDir ? scope.row.caseSourceValue.caseDir : '项目根目录'
              }}
            </template>
          </el-table-column>
          <el-table-column prop="tokenType" label="凭证类型" width="110" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.tokenType === 'system' ? 'primary' : 'success'"
                      class="token-tag">
                {{ scope.row.tokenType === 'system' ? '系统凭证' : '工作空间凭证' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="desc" label="描述" min-width="140"/>
          <el-table-column prop="desc" label="虚拟环境" min-width="140">
            <template #default="scope">
              <el-tag v-if="scope.row.venvName" class="env-tag">
                {{ scope.row.venvName }}
              </el-tag>
              <el-tag v-else type="danger">
                未配置
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="150" align="center">
            <template #default="scope">
              <span class="time-text">{{ formatTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="scope">
              <div class="action-cell">
                <el-button
                  size="small"
                  type="primary"
                  link
                  @click="openEditDialog(scope.row)"
                  class="action-button edit-btn"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  link
                  @click="openVirtualEnvDrawer(scope.row)"
                  class="action-button env-btn"
                  v-if="scope.row.caseType === 'pytest'"
                >
                  配置虚拟环境
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click="handleDeleteCaseSource(scope.row)"
                  class="action-button delete-btn"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <div v-if="!loading && filteredCaseSourceList.length === 0" class="empty-state">
          <el-icon class="empty-icon">
            <Document/>
          </el-icon>
          <p class="empty-text">暂无用例源数据</p>
          <el-button type="primary" @click="openCreateDialog" class="empty-button" size="small">
            <el-icon>
              <Plus/>
            </el-icon>
            添加第一个用例源
          </el-button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="550px"
      :before-close="handleDialogClose"
      class="source-dialog custom-dialog"
      destroy-on-close
    >
      <div class="dialog-header">
        <h3 class="dialog-title">{{ dialogTitle }}</h3>
      </div>
      <el-form
        ref="sourceFormRef"
        :model="sourceForm"
        :rules="sourceFormRules"
        label-width="90px"
        class="source-form custom-form"
        size="small"
      >
        <el-form-item label="测试类型" prop="specificType">
          <el-select
            v-model="sourceForm.specificType"
            placeholder="请选择测试类型"
            style="width: 100%"
            class="custom-select"
          >
            <el-option
              v-for="item in specificTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="用例类型" prop="caseType">
          <el-select
            v-model="sourceForm.caseType"
            placeholder="请选择用例类型"
            style="width: 100%"
            class="custom-select"
          >
            <el-option
              v-for="item in caseTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="项目ID" prop="caseSourceValue.projectId">
          <el-input
            v-model.number="sourceForm.caseSourceValue.projectId"
            placeholder="请输入GitLab项目ID"
            class="custom-input"
          />
        </el-form-item>

        <el-form-item label="Git 凭证" prop="tokenType">
          <el-select
            v-model="sourceForm.tokenType"
            placeholder="请选择Git凭证类型"
            style="width: 100%"
            class="custom-select"
            :disabled="!systemTokenValid && !workspaceTokenValid"
          >
            <el-option
              v-if="systemTokenValid"
              label="系统 Git 凭证"
              value="system"
            />
            <el-option
              v-if="workspaceTokenValid && hasWorkspaceToken"
              label="工作空间 Git 凭证"
              value="workspace"
            />
          </el-select>
          <div class="token-hint" v-if="!systemTokenValid && !workspaceTokenValid">
            无有效的Git凭证，请先配置有效的Git凭证
          </div>
        </el-form-item>

        <el-form-item label="用例目录" prop="caseSourceValue.caseDir">
          <template v-if="sourceForm.caseType === 'testng'">
            <div class="testng-path-input">
              <span class="path-prefix">src/test/java/</span>
              <el-input
                v-model="testngPathSuffix"
                placeholder="请输入子目录（可选）"
                class="custom-input path-suffix-input"
                @input="updateTestngPath"
              />
            </div>
            <div class="full-path-hint"
                 v-if="sourceForm.caseType === 'testng' && testngPathSuffix">
              完整路径: <b class="path-preview">{{ fullPathForTestNG }}</b>
            </div>
            <div v-else-if="sourceForm.caseType === 'testng' && !testngPathSuffix"
                 class="input-hint">
              TestNG类型目录前缀固定为src/test/java/，可添加子目录
            </div>
          </template>
          <template v-else-if="sourceForm.caseType === 'pytest'">
            <el-input
              v-model="pytestPath"
              placeholder="请输入用例目录"
              class="custom-input"
              @input="updatePytestPath"
            />
            <div class="full-path-hint" v-if="pytestPath">
              完整路径: <b class="path-preview">{{ fullPathForPytest }}</b>
            </div>
            <div class="input-hint" v-else>
              例如：case/order/return_order（从项目根目录开始）
            </div>
          </template>
          <template v-else>
            <el-input
              v-model="sourceForm.caseSourceValue.caseDir"
              placeholder="请输入用例目录"
              class="custom-input"
            />
            <div class="input-hint">例如：case/order/return_order（从项目根目录开始）</div>
          </template>
        </el-form-item>

        <el-form-item label="描述" prop="desc">
          <el-input
            v-model="sourceForm.desc"
            type="textarea"
            placeholder="请输入描述信息"
            class="custom-textarea"
            :rows="3"
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
          class="footer-button confirm-button"
        >
          保存
        </el-button>
      </div>
    </el-dialog>

    <!-- 虚拟环境抽屉 -->
    <el-drawer
      v-model="virtualEnvDrawerVisible"
      direction="rtl"
      size="50%"
      class="virtual-env-drawer"
    >
      <template #header>
        <div class="drawer-header">
          <h2 class="drawer-title">创建虚拟环境</h2>
          <p class="drawer-subtitle">为 "{{ currentCaseSource?.caseProjectName }}"
            配置Python虚拟环境</p>
        </div>
      </template>

      <div class="drawer-content">
        <el-steps :active="activeStep" finish-status="success" class="env-setup-steps">
          <el-step title="选择Python版本"/>
          <el-step title="选择依赖文件"/>
          <el-step title="确认配置"/>
        </el-steps>

        <div class="step-content">
          <!-- 步骤1: 选择Python版本 -->
          <div v-show="activeStep === 0" class="step-panel">
            <div class="step-title">
              <h3>选择Python版本</h3>
              <p>请选择用于创建虚拟环境的Python版本</p>
            </div>

            <el-form
              ref="step1FormRef"
              :model="virtualEnvForm"
              :rules="step1Rules"
              class="step-form"
            >
              <el-form-item prop="pythonVersion">
                <el-select
                  v-model="virtualEnvForm.pythonVersion"
                  placeholder="请选择Python版本"
                  style="width: 100%"
                  size="large"
                  class="python-version-select"
                >
                  <el-option
                    v-for="version in pythonVersions"
                    :key="version"
                    :label="`Python ${version}`"
                    :value="version"
                  >
                    <span class="version-option-label">Python {{ version }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-form>

            <div class="version-info" v-if="virtualEnvForm.pythonVersion">
              <el-card class="version-card">
                <div class="version-card-header">
                  <el-icon class="version-icon">
                    <Promotion/>
                  </el-icon>
                  <h4>Python {{ virtualEnvForm.pythonVersion }}</h4>
                </div>
                <p class="version-description">
                  将使用此版本创建独立的Python虚拟环境，确保测试运行的隔离性和一致性。
                </p>
              </el-card>
            </div>
          </div>

          <!-- 步骤2: 选择依赖文件 -->
          <div v-show="activeStep === 1" class="step-panel">
            <div class="step-title">
              <h3>选择依赖文件</h3>
              <p>请选择项目中的依赖文件，例：requirements.txt</p>
            </div>

            <el-form
              ref="step2FormRef"
              :model="virtualEnvForm"
              :rules="step2Rules"
              class="step-form"
            >
              <el-form-item prop="requirementsPath">
                <el-tree-select
                  v-model="virtualEnvForm.requirementsPath"
                  :data="projectFileTree"
                  node-key="path"
                  :props="treeProps"
                  check-strictly
                  :default-expand-all="false"
                  style="width: 100%"
                  placeholder="请选择依赖包列表文件"
                  size="large"
                  class="file-tree-select"
                />
              </el-form-item>
            </el-form>

            <div class="file-preview-actions" v-if="virtualEnvForm.requirementsPath">
              <el-button
                type="primary"
                link
                @click="previewFileContent(virtualEnvForm.requirementsPath)"
                :loading="filePreviewLoading"
                class="preview-button"
              >
                <el-icon>
                  <View/>
                </el-icon>
                预览文件内容
              </el-button>
            </div>

            <div class="file-preview-container" v-if="filePreviewVisible">
              <el-card class="preview-card">
                <div class="preview-card-header">
                  <h4>{{ selectedFilePath }}</h4>
                  <el-tag type="info" size="small">依赖文件</el-tag>
                </div>
                <div class="preview-content-wrapper">
                  <pre class="file-content-preview">{{ fileContent }}</pre>
                </div>
                <div class="preview-card-footer" v-if="fileContent">
                  <span class="line-count">共 {{ fileContent.split('\n').length }} 行</span>
                </div>
              </el-card>
            </div>
          </div>

          <!-- 步骤3: 确认配置 -->
          <div v-show="activeStep === 2 || activeStep === 3" class="step-panel">
            <div class="step-title">
              <h3>确认配置</h3>
              <p>请确认以下虚拟环境配置信息</p>
            </div>

            <!-- 配置信息展示 -->
            <el-descriptions :column="2" border class="config-descriptions">
              <el-descriptions-item label="项目名称">{{
                  currentCaseSource?.caseProjectName
                }}
              </el-descriptions-item>
              <el-descriptions-item label="Python版本">Python {{
                  virtualEnvForm.pythonVersion
                }}
              </el-descriptions-item>
              <el-descriptions-item label="依赖文件">{{
                  virtualEnvForm.requirementsPath
                }}
              </el-descriptions-item>
              <el-descriptions-item label="虚拟环境名" class-name="summary-path">
                {{ currentCaseSource.workspaceId }}_{{
                  currentCaseSource?.caseSourceValue.projectId
                }}_{{
                  currentCaseSource?.caseProjectName
                }}_py{{ virtualEnvForm.pythonVersion.replace(/\./g, '_') }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 成功时显示的提示信息 -->
            <el-alert
              v-if="!virtualEnvCreationError && !virtualEnvCreationSuccess"
              title="创建虚拟环境"
              description="确认配置无误后，点击'创建虚拟环境'按钮开始创建。此过程可能需要几分钟时间，请耐心等待。"
              type="info"
              show-icon
              class="creation-info"
            />

            <!-- 失败时显示的错误信息 -->
            <div v-else-if="virtualEnvCreationError" class="error-container">
              <el-card class="error-card">
                <div class="error-card-header">
                  <h4>虚拟环境创建失败</h4>
                  <el-tag type="danger" size="small">错误详情</el-tag>
                </div>
                <div class="error-content-wrapper">
                  <pre class="error-content-preview">{{ virtualEnvCreationErrorMessage }}</pre>
                </div>
              </el-card>
            </div>

            <!-- 成功时显示的日志信息 -->
            <div v-else-if="virtualEnvCreationSuccess" class="success-container">
              <el-card class="success-card">
                <div class="success-card-header">
                  <h4>虚拟环境创建成功</h4>
                  <el-tag type="success" size="small">执行日志</el-tag>
                </div>
                <div class="success-content-wrapper">
                  <pre class="success-content-preview">{{ virtualEnvCreationSuccessMessage }}</pre>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="handleCancelVirtualEnv" class="footer-button cancel-button">
            取消
          </el-button>
          <div class="navigation-buttons">
            <el-button
              v-if="activeStep > 0"
              @click="prevStep"
              class="footer-button prev-button"
            >
              上一步
            </el-button>
            <el-button
              v-if="activeStep < 2"
              type="primary"
              @click="nextStep"
              class="footer-button next-button"
            >
              下一步
            </el-button>
            <el-button
              v-if="activeStep === 2"
              type="success"
              @click="handleCreateVirtualEnv"
              :loading="virtualEnvSubmitLoading"
              class="footer-button confirm-button"
            >
              <el-icon>
                <Check/>
              </el-icon>
              创建虚拟环境
            </el-button>
            <el-button
              v-if="[2, 3].includes(activeStep) && virtualEnvCreationSuccess"
              type="success"
              @click="handleFinish"
              class="footer-button confirm-button"
            >
              <el-icon>
                <Check/>
              </el-icon>
              完成
            </el-button>
          </div>
        </div>
      </template>
    </el-drawer>


  </div>
</template>


<script setup>
import {computed, nextTick, onMounted, reactive, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  bindCaseSource,
  createPythonVirtualEnv,
  deleteCaseSource,
  getCaseSourceList,
  getFileContent,
  getGitTokenVerifiedInfo,
  getProjectFileTree,
  getPythonList,
  updateCaseSource
} from '@/network/api.js'
import {
  Check,
  CircleClose,
  Document,
  Plus,
  Promotion,
  Refresh,
  Search,
  SuccessFilled,
  View
} from '@element-plus/icons-vue'

const route = useRoute()

// 数据状态
const caseSourceList = ref([])
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)

// 搜索关键词
const searchKeyword = ref('')

// Token状态相关
const tokenStatusLoading = ref(false)
const tokenStatusChecked = ref(false)
const systemTokenValid = ref(false)
const workspaceTokenValid = ref(false)
const hasWorkspaceToken = ref(false)

// 表单
const sourceFormRef = ref()
const sourceForm = reactive({
  id: undefined,
  specificType: undefined,
  caseType: undefined,
  tokenType: undefined,
  caseSourceValue: {
    projectId: undefined,
    caseDir: ''
  },
  desc: ''
})

// TestNG路径后缀
const testngPathSuffix = ref('')

// Pytest路径
const pytestPath = ref('')

// 保存原始数据用于比较
const originalSourceData = ref(null)

// 虚拟环境相关
const virtualEnvDrawerVisible = ref(false)
const activeStep = ref(0)
const step1FormRef = ref()
const step2FormRef = ref()
const virtualEnvSubmitLoading = ref(false)
const currentCaseSource = ref(null)
const pythonVersions = ref([])
const pythonVersionsLoading = ref(false)
const projectFileTree = ref([])
const filePreviewVisible = ref(false)
const filePreviewLoading = ref(false)
const selectedFilePath = ref('')
const fileContent = ref('')
const virtualEnvCreationError = ref(false) // 新增：虚拟环境创建错误状态
const virtualEnvCreationErrorMessage = ref('') // 新增：虚拟环境创建错误信息
const virtualEnvCreationSuccess = ref(false) // 新增：虚拟环境创建成功状态
const virtualEnvCreationSuccessMessage = ref('') // 新增：虚拟环境创建成功信息


const treeProps = {
  label: 'label',
  children: 'children',
  isLeaf: 'isLeaf'
}

const virtualEnvForm = reactive({
  pythonVersion: '',
  requirementsPath: ''
})

// 测试类型选项
const specificTypeOptions = [
  {label: 'Web', value: 10},
  {label: 'H5', value: 11},
  {label: '接口', value: 12}
]

// 用例类型选项
const caseTypeOptions = [
  {label: 'TestNG', value: 'testng'},
  {label: 'Pytest', value: 'pytest'}
]

// 表单验证规则
const sourceFormRules = {
  specificType: [
    {required: true, message: '请选择测试类型', trigger: 'change'}
  ],
  caseType: [
    {required: true, message: '请选择用例类型', trigger: 'change'}
  ],
  tokenType: [
    {required: true, message: '请选择Git凭证类型', trigger: 'change'}
  ],
  'caseSourceValue.projectId': [
    {required: true, message: '请输入项目ID', trigger: 'blur'},
    {type: 'number', message: '项目ID必须为数字', trigger: 'blur'}
  ],
  'caseSourceValue.caseDir': [],
  desc: [
    {required: true, message: '请输入描述信息', trigger: 'blur'}
  ]
}

const step1Rules = {
  pythonVersion: [
    {required: true, message: '请选择Python版本', trigger: 'change'}
  ]
}

const step2Rules = {
  requirementsPath: [
    {required: true, message: '请选择requirements.txt文件', trigger: 'change'}
  ]
}

// 对话框标题
const dialogTitle = computed(() => {
  return sourceForm.id ? '编辑用例源' : '添加用例源'
})

// 过滤后的用例源列表
const filteredCaseSourceList = computed(() => {
  if (!searchKeyword.value) {
    return caseSourceList.value
  }

  const keyword = searchKeyword.value.toLowerCase()
  return caseSourceList.value.filter(item =>
    (item.caseProjectName && item.caseProjectName.toLowerCase().includes(keyword)) ||
    (item.desc && item.desc.toLowerCase().includes(keyword))
  )
})

// 计算TestNG完整路径
const fullPathForTestNG = computed(() => {
  if (sourceForm.caseType !== 'testng') return ''

  // 确保后缀不以/开头
  let suffix = testngPathSuffix.value
  if (suffix.startsWith('/')) {
    suffix = suffix.substring(1)
  }

  // 确保路径以/结尾（如果不是空的话）
  if (suffix && !suffix.endsWith('/')) {
    suffix = suffix + '/'
  }

  return `src/test/java/${suffix}`
})

// 计算Pytest完整路径
const fullPathForPytest = computed(() => {
  if (sourceForm.caseType !== 'pytest') return ''

  // 去掉开头的斜杠（如果有的话）
  let path = pytestPath.value
  if (path.startsWith('/')) {
    path = path.substring(1)
  }

  return path
})

// 组件挂载时获取数据
onMounted(() => {
  fetchCaseSourceList()
  checkGitTokenStatus()
})

// 获取用例源列表
const fetchCaseSourceList = async () => {
  loading.value = true
  try {
    const params = {
      workspaceId: route.params.id
    }

    const res = await getCaseSourceList(params)

    if (res.code === 0) {
      caseSourceList.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取用例源列表失败')
    }
  } catch (error) {
    ElMessage.error('获取用例源列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑在computed中实现
}

// 检查Git Token状态
const checkGitTokenStatus = async () => {
  tokenStatusLoading.value = true
  try {
    const res = await getGitTokenVerifiedInfo({
      workspace_id: route.params.id
    })

    if (res.code === 0) {
      systemTokenValid.value = res.data.system_config_result
      workspaceTokenValid.value = res.data.workspace_config_result
      hasWorkspaceToken.value = true
      tokenStatusChecked.value = true
    } else {
      ElMessage.error(res.message || '获取Token状态失败')
    }
  } catch (error) {
    ElMessage.error('获取Token状态失败: ' + error.message)
  } finally {
    tokenStatusLoading.value = false
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '-'
  return new Date(timeString).toLocaleString('zh-CN')
}

// 获取测试类型名称
const getSpecificTypeName = (type) => {
  const typeMap = {
    10: 'Web',
    11: 'H5',
    12: '接口'
  }
  return typeMap[type] || type
}

// 获取测试类型标签类型
const getSpecificTypeTagType = (type) => {
  const typeMap = {
    10: 'primary',
    11: 'success',
    12: 'warning'
  }
  return typeMap[type] || ''
}

// 获取用例类型名称
const getCaseTypeName = (type) => {
  const typeMap = {
    'testng': 'TestNG',
    'pytest': 'Pytest'
  }
  return typeMap[type] || type
}

// 获取用例类型标签类型
const getCaseTypeTagType = (type) => {
  const typeMap = {
    'testng': 'primary',
    'pytest': 'success'
  }
  return typeMap[type] || ''
}

// 监听用例类型变化
watch(() => sourceForm.caseType, (newVal, oldVal) => {
  if (newVal === 'testng') {
    // 从其他类型切换到TestNG
    // 提取当前路径中src/test/java/后的部分作为后缀
    sourceForm.caseSourceValue.caseDir = 'src/test/java/'
    if (sourceForm.caseSourceValue.caseDir.startsWith('src/test/java/')) {
      testngPathSuffix.value = sourceForm.caseSourceValue.caseDir.substring('src/test/java/'.length)
    } else {
      testngPathSuffix.value = ''
    }
    pytestPath.value = ''
  } else if (newVal === 'pytest') {
    // 从其他类型切换到Pytest
    sourceForm.caseSourceValue.caseDir = ''
    pytestPath.value = sourceForm.caseSourceValue.caseDir
    testngPathSuffix.value = ''

  } else if (oldVal === 'testng' || oldVal === 'pytest') {
    // 从TestNG或Pytest切换到其他类型
    sourceForm.caseSourceValue.caseDir = ''
    testngPathSuffix.value = ''
    pytestPath.value = ''
  }
})

// 更新Pytest路径
const updatePytestPath = (value) => {
  // 去掉开头的斜杠（如果有的话）
  let path = value
  if (path.startsWith('/')) {
    path = path.substring(1)
  }

  pytestPath.value = path
  sourceForm.caseSourceValue.caseDir = path
}

// 更新TestNG路径
const updateTestngPath = (value) => {
  // 去掉开头的斜杠（如果有的话）
  let suffix = value
  if (suffix.startsWith('/')) {
    suffix = suffix.substring(1)
  }

  // 确保路径以/结尾（如果不是空的话）
  if (suffix && !suffix.endsWith('/')) {
    suffix = suffix + '/'
  }

  sourceForm.caseSourceValue.caseDir = 'src/test/java/' + suffix
}

// 打开创建对话框
const openCreateDialog = () => {
  // 检查Token状态是否有效
  if (!systemTokenValid.value && !workspaceTokenValid.value) {
    ElMessageBox.alert(
      '系统Token和工作空间Token均无效，请先配置有效的GitLab Token后再添加用例源。',
      'Token无效',
      {
        type: 'warning',
        confirmButtonText: '确定'
      }
    )
    return
  }

  // 重置表单
  Object.assign(sourceForm, {
    id: undefined,
    specificType: undefined,
    caseType: undefined,
    tokenType: systemTokenValid.value ? 'system' : (workspaceTokenValid.value ? 'workspace' : undefined),
    caseSourceValue: {
      projectId: undefined,
      caseDir: ''
    },
    desc: ''
  })
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (row) => {
  Object.assign(sourceForm, {
    id: row.id,
    specificType: row.specificType,
    caseType: row.caseType,
    tokenType: row.tokenType,
    caseSourceValue: {
      projectId: row.caseSourceValue?.projectId,
      caseDir: row.caseSourceValue?.caseDir || ''
    },
    desc: row.desc
  })

  // 如果是TestNG类型，设置后缀
  if (row.caseType === 'testng' && row.caseSourceValue?.caseDir.startsWith('src/test/java/')) {
    testngPathSuffix.value = row.caseSourceValue.caseDir.substring('src/test/java/'.length)
    pytestPath.value = ''
  } else if (row.caseType === 'pytest') {
    // 如果是Pytest类型，设置路径
    pytestPath.value = row.caseSourceValue?.caseDir || ''
    testngPathSuffix.value = ''
  } else {
    testngPathSuffix.value = ''
    pytestPath.value = ''
  }

  // 保存原始数据用于后续比较
  originalSourceData.value = JSON.parse(JSON.stringify(sourceForm))
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

// 提交表单
const handleSubmit = async () => {
  try {
    await sourceFormRef.value.validate()

    // 检查关键字段是否有变更
    if (sourceForm.id && originalSourceData) {
      const changedFields = []

      if (sourceForm.specificType !== originalSourceData.value.specificType) {
        changedFields.push('测试类型')
      }

      if (sourceForm.caseType !== originalSourceData.value.caseType) {
        changedFields.push('用例类型')
      }

      if (sourceForm.caseSourceValue.projectId !== originalSourceData.value.caseSourceValue.projectId) {
        changedFields.push('项目ID')
      }

      if (sourceForm.tokenType !== originalSourceData.value.tokenType) {
        changedFields.push('Git凭证')
      }

      if (sourceForm.caseSourceValue.caseDir !== originalSourceData.value.caseSourceValue.caseDir) {
        changedFields.push('用例目录')
      }

      if (changedFields.length > 0) {
        try {
          await ElMessageBox.confirm(
            `您已修改了以下关键信息：${changedFields.join('、')}，这些变更将导致用例重新同步，是否确认保存？`,
            '关键信息变更确认',
            {
              type: 'warning',
              confirmButtonText: '确认',
              cancelButtonText: '取消'
            }
          )
        } catch {
          // 用户取消操作
          return
        }
      }
    }

    submitLoading.value = true

    let res
    if (sourceForm.id) {
      // 编辑
      res = await updateCaseSource({
        id: sourceForm.id,
        workspaceId: route.params.id,
        specificType: sourceForm.specificType,
        caseType: sourceForm.caseType,
        tokenType: sourceForm.tokenType,
        caseSourcePlatform: 'GitLab',
        caseSourceValue: sourceForm.caseSourceValue,
        desc: sourceForm.desc
      })
    } else {
      // 创建
      res = await bindCaseSource({
        workspaceId: route.params.id,
        specificType: sourceForm.specificType,
        caseType: sourceForm.caseType,
        tokenType: sourceForm.tokenType,
        caseSourcePlatform: 'GitLab',
        caseSourceValue: sourceForm.caseSourceValue,
        desc: sourceForm.desc
      })
    }

    if (res.code === 0) {
      ElMessage.success(sourceForm.id ? '更新成功' : '添加成功')
      dialogVisible.value = false
      fetchCaseSourceList()
    } else {
      ElMessage.error(res.message || (sourceForm.id ? '更新失败' : '添加失败'))
    }
  } catch (error) {
    ElMessage.error((sourceForm.id ? '更新失败' : '添加失败') + ': ' + error.message)
  } finally {
    submitLoading.value = false
  }
}

// 删除用例源
const handleDeleteCaseSource = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用例源 "${row.caseProjectName}" 吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )

    const res = await deleteCaseSource({id: row.id, workspaceId: route.params.id})

    if (res.code === 0) {
      ElMessage.success('删除成功')
      fetchCaseSourceList()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 打开虚拟环境抽屉
const openVirtualEnvDrawer = async (row) => {
  currentCaseSource.value = row
  virtualEnvDrawerVisible.value = true
  activeStep.value = 0

  // 重置表单
  virtualEnvForm.pythonVersion = ''
  virtualEnvForm.requirementsPath = ''
  projectFileTree.value = []
  filePreviewVisible.value = false
  fileContent.value = ''
  selectedFilePath.value = ''
  virtualEnvCreationError.value = false
  virtualEnvCreationErrorMessage.value = ''
  virtualEnvCreationSuccess.value = false
  virtualEnvCreationSuccessMessage.value = ''
  // 重置表单验证状态
  nextTick(() => {
    if (step1FormRef.value) {
      step1FormRef.value.resetFields()
    }
    if (step2FormRef.value) {
      step2FormRef.value.resetFields()
    }
  })
  // 获取Python版本列表
  await fetchPythonVersions()

  // 获取项目文件树
  await fetchProjectFileTree(row.caseSourceValue.projectId)
}

// 获取Python版本列表
const fetchPythonVersions = async () => {
  pythonVersionsLoading.value = true
  try {
    const res = await getPythonList()
    if (res.code === 0) {
      pythonVersions.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取Python版本列表失败')
    }
  } catch (error) {
    ElMessage.error('获取Python版本列表失败: ' + error.message)
  } finally {
    pythonVersionsLoading.value = false
  }
}

// 获取项目文件树
const fetchProjectFileTree = async (projectId) => {
  try {
    const res = await getProjectFileTree({
      workspace_id: route.params.id,
      git_project_id: projectId
    })
    if (res.code === 0) {
      projectFileTree.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取项目文件树失败')
    }
  } catch (error) {
    ElMessage.error('获取项目文件树失败: ' + error.message)
  }
}

// 预览文件内容
const previewFileContent = async (filePath) => {
  filePreviewLoading.value = true
  filePreviewVisible.value = false
  try {
    const params = {
      workspace_id: route.params.id,
      git_project_id: currentCaseSource.value.caseSourceValue.projectId,
      file_path: filePath
    }

    const res = await getFileContent(params)
    if (res.code === 0) {
      selectedFilePath.value = filePath
      fileContent.value = res.data?.content || ''
      filePreviewVisible.value = true
    } else {
      ElMessage.error(res.message || '获取文件内容失败')
    }
  } catch (error) {
    ElMessage.error('获取文件内容失败: ' + error.message)
  } finally {
    filePreviewLoading.value = false
  }
}

// 下一步
const nextStep = async () => {
  if (activeStep.value === 0) {
    try {
      await step1FormRef.value.validate()
      activeStep.value++
    } catch (error) {
      ElMessage.error('请先选择Python版本')
    }
  } else if (activeStep.value === 1) {
    try {
      await step2FormRef.value.validate()
      activeStep.value++
    } catch (error) {
      ElMessage.error('请先选择requirements.txt文件')
    }
  }
}

// 上一步
const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
    // 清除错误和成功状态
    if (activeStep.value < 2) {
      virtualEnvCreationError.value = false
      virtualEnvCreationErrorMessage.value = ''
      virtualEnvCreationSuccess.value = false
      virtualEnvCreationSuccessMessage.value = ''
    }
  }
}

// 取消虚拟环境创建
const handleCancelVirtualEnv = () => {
  virtualEnvDrawerVisible.value = false
  activeStep.value = 0

  // 重置表单验证状态
  if (step1FormRef.value) {
    step1FormRef.value.resetFields()
  }
  if (step2FormRef.value) {
    step2FormRef.value.resetFields()
  }
}

// 创建虚拟环境
const handleCreateVirtualEnv = async () => {
  try {
    virtualEnvSubmitLoading.value = true

    const params = {
      case_source_id: currentCaseSource.value.id,
      workspace_id: route.params.id,
      python_version: virtualEnvForm.pythonVersion,
      project_name: currentCaseSource.value.caseProjectName,
      git_project_id: currentCaseSource.value.caseSourceValue.projectId,
      requirements_path: virtualEnvForm.requirementsPath
    }

    const res = await createPythonVirtualEnv(params)

    if (res.code === 0) {
      virtualEnvCreationSuccess.value = true
      virtualEnvCreationError.value = false
      virtualEnvCreationSuccessMessage.value = res.data.log || '虚拟环境创建成功'
      // 更新步骤状态，使最后一步显示为完成状态
      activeStep.value = 3
    } else {
      virtualEnvCreationError.value = true
      virtualEnvCreationSuccess.value = false
      virtualEnvCreationErrorMessage.value = res.message || '虚拟环境创建失败'
    }
  } catch (error) {
    ElMessage.error('虚拟环境创建失败: ' + error.message)
  } finally {
    virtualEnvSubmitLoading.value = false
  }
}

// 完成按钮点击事件
const handleFinish = () => {
  virtualEnvDrawerVisible.value = false
  activeStep.value = 0
  fetchCaseSourceList() // 刷新用例源列表
}
</script>


<style scoped>
.case-source-manage-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  padding: 5px;
  box-sizing: border-box;
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

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.refresh-token-btn,
.add-source-btn {
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 12px;
  padding: 6px 10px;
}

.refresh-token-btn:hover,
.add-source-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.refresh-token-btn {
  background-color: #679ae5;
  border-color: #679ae5;
  color: #ffffff;
}

.add-source-btn {
  background-color: #67c23a;
  border-color: #67c23a;
  color: #ffffff;
}

.token-status-bar {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f2f5;
}

.token-status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.token-status-item.valid {
  color: #67c23a;
}

.token-status-item.valid .token-status-icon {
  color: #67c23a;
}

.token-status-item.invalid {
  color: #f56c6c;
}

.token-status-item.invalid .token-status-icon {
  color: #f56c6c;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

.source-list-card {
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #edf2f7;
  background-color: #f8f9fa;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.preview-card-footer {
  margin-top: 20px;
}

.search-input {
  width: 180px;
}

.source-table {
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
.token-tag {
  margin: 0;
  border: none;
  font-weight: 500;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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

.edit-btn:hover {
  background-color: #e3f2fd;
  color: #1976d2 !important;
}

.env-btn:hover {
  background-color: #fff3e0;
  color: #f57c00 !important;
}

.delete-btn:hover {
  background-color: #ffebee;
  color: #d32f2f !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 20px;
  color: #a0aec0;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 10px;
  color: #cbd5e0;
}

.empty-text {
  font-size: 13px;
  margin-bottom: 14px;
  color: #909399;
}

.empty-button {
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 12px;
  padding: 6px 10px;
}

/* 弹窗美化核心样式 */
:deep(.source-dialog) {
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  width: 550px !important;
}

:deep(.source-dialog .el-dialog__header) {
  display: none;
}

:deep(.source-dialog .dialog-header) {
  padding: 18px 24px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  margin: -20px -20px 20px -20px;
  border-radius: 12px 12px 0 0;
}

:deep(.source-dialog .dialog-title) {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.3px;
}

:deep(.source-dialog .source-form) {
  padding: 0 10px;
}

:deep(.source-dialog .el-form-item) {
  margin-bottom: 20px;
  transition: all 0.2s ease;
}

:deep(.source-dialog .el-form-item:hover) {
  transform: translateX(3px);
}

:deep(.source-dialog .el-form-item__label) {
  font-size: 14px;
  padding: 0 10px 6px 0;
  text-align: right;
  color: #475569;
  font-weight: 500;
}

:deep(.source-dialog .el-form-item__label .el-form-item__label-required) {
  color: #ef4444;
  margin-right: 3px;
}

/* 输入框美化 */
:deep(.source-dialog .custom-input .el-input__wrapper),
:deep(.source-dialog .custom-select .el-select__wrapper),
:deep(.source-dialog .custom-textarea .el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) inset;
  transition: all 0.25s ease;
  height: 36px;
}

:deep(.source-dialog .custom-input .el-input__wrapper:hover),
:deep(.source-dialog .custom-select .el-select__wrapper:hover),
:deep(.source-dialog .custom-textarea .el-textarea__inner:hover) {
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.1);
}

:deep(.source-dialog .custom-input .el-input__wrapper.is-focus),
:deep(.source-dialog .custom-select .el-select__wrapper.is-focused),
:deep(.source-dialog .custom-textarea .el-textarea__inner:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  outline: none;
}

:deep(.source-dialog .el-textarea__inner) {
  min-height: 90px !important;
  resize: vertical;
  line-height: 1.6;
  font-size: 14px;
}

/* TestNG路径输入框 */
:deep(.source-dialog .testng-path-input) {
  display: flex;
  align-items: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
  transition: all 0.25s ease;
  font-size: 14px;
}

:deep(.source-dialog .testng-path-input:hover) {
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.1);
}

:deep(.source-dialog .testng-path-input:focus-within) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

:deep(.source-dialog .path-prefix) {
  padding: 0 12px;
  background: #f1f5f9;
  color: #64748b;
  border-right: 1px solid #e2e8f0;
  white-space: nowrap;
  font-size: 14px;
  height: 36px;
  display: flex;
  align-items: center;
}

:deep(.source-dialog .path-suffix-input) {
  flex: 1;
  width: 100%;
}

:deep(.source-dialog .path-suffix-input .el-input__wrapper) {
  border: none !important;
  box-shadow: none !important;
  height: 36px;
}

:deep(.source-dialog .path-suffix-input .el-input__inner) {
  height: 36px;
  border-radius: 0;
  font-size: 14px;
  padding-left: 12px;
}

/* 提示文本样式 */
:deep(.source-dialog .full-path-hint),
:deep(.source-dialog .input-hint) {
  font-size: 13px;
  color: #64748b;
  margin-top: 6px;
  line-height: 1.5;
  padding-left: 2px;
}

:deep(.source-dialog .path-preview) {
  color: #1e40af;
  font-weight: 500;
  font-family: 'Fira Code', monospace;
}

/* 底部按钮区域 */
:deep(.source-dialog .dialog-footer) {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 18px 20px 20px;
  border-top: 1px solid #f0f2f5;
  margin-top: 15px;
  background-color: #f8fafc;
  margin: 15px -20px -20px -20px;
  border-radius: 0 0 12px 12px;
}

:deep(.source-dialog .footer-button) {
  padding: 8px 22px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.source-dialog .cancel-button) {
  border: 1px solid #e2e8f0;
  color: #475569;
  background-color: #ffffff;
}

:deep(.source-dialog .cancel-button:hover) {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

:deep(.source-dialog .confirm-button) {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

:deep(.source-dialog .confirm-button:hover) {
  background-color: #2563eb;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
}

:deep(.source-dialog .confirm-button:active) {
  transform: translateY(0);
}

/* 错误提示 */
:deep(.source-dialog .token-hint) {
  font-size: 13px;
  color: #ef4444;
  margin-top: 6px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.source-dialog .token-hint:before) {
  content: "!";
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #ef4444;
  color: white;
  font-size: 12px;
  text-align: center;
  line-height: 16px;
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

/* 虚拟环境抽屉样式 */
:deep(.virtual-env-drawer) {
  border-radius: 16px 0 0 16px !important;
  overflow: hidden;
  box-shadow: -5px 0 30px rgba(0, 0, 0, 0.1) !important;
}

:deep(.virtual-env-drawer .el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f2f5;
}

.drawer-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drawer-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.drawer-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  font-weight: 400;
}

.drawer-content {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
}

.env-setup-steps {
  margin-bottom: 30px;
}

.step-content {
  flex: 1;
  overflow-y: auto;
}

.step-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-title {
  margin-bottom: 24px;
}

.step-title h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.step-title p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.python-version-select,
.file-tree-select {
  font-size: 16px;
}

.version-option-label {
  font-size: 16px;
  font-weight: 500;
}

.version-info {
  margin-top: 20px;
}

.version-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.version-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.version-icon {
  font-size: 24px;
  color: #3b82f6;
}

.version-card h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.version-description {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

.preview-button {
  font-size: 14px;
  padding: 8px 16px;
}

.file-preview-container {
  margin-top: 20px;
}

.preview-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.preview-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.preview-content-wrapper {
  overflow-y: auto;
}

.file-content-preview {
  margin: 0;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 8px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  color: #334155;
}

.config-descriptions {
  margin-bottom: 24px;
  border-radius: 8px;
}

.config-descriptions :deep(.el-descriptions__header) {
  margin-bottom: 0;
}

.config-descriptions :deep(.el-descriptions__title) {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.config-descriptions :deep(.el-descriptions__label) {
  font-weight: 500;
  color: #64748b;
  width: 100px;
}

.config-descriptions :deep(.el-descriptions__content) {
  color: #1e293b;
  font-weight: 500;
}

.config-descriptions :deep(.summary-path) {
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.creation-info {
  border-radius: 12px;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid #f0f2f5;
  background-color: #f8fafc;
}

.navigation-buttons {
  display: flex;
  gap: 12px;
}

:deep(.drawer-footer .footer-button) {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.drawer-footer .cancel-button) {
  border: 1px solid #e2e8f0;
  color: #475569;
  background-color: #ffffff;
}

:deep(.drawer-footer .cancel-button:hover) {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

:deep(.drawer-footer .prev-button) {
  border: 1px solid #e2e8f0;
  color: #475569;
  background-color: #ffffff;
}

:deep(.drawer-footer .prev-button:hover) {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

:deep(.drawer-footer .next-button) {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

:deep(.drawer-footer .next-button:hover) {
  background-color: #2563eb;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
}

:deep(.drawer-footer .confirm-button) {
  background-color: #10b981;
  border-color: #10b981;
  color: white;
}

:deep(.drawer-footer .confirm-button:hover) {
  background-color: #059669;
  border-color: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);
}

/* 响应式调整 */
@media (max-width: 768px) {
  :deep(.source-dialog) {
    width: 95% !important;
  }

  :deep(.source-dialog .el-form-item__label) {
    text-align: left;
    padding-bottom: 5px;
    display: block;
  }

  :deep(.virtual-env-drawer) {
    width: 100% !important;
  }
}

.error-container {
  margin-top: 20px;
}

.error-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.error-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.error-card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #dc2626;
}

.error-content-wrapper {
  overflow-y: auto;
  background-color: #fef2f2;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #fecaca;
}

.error-content-preview {
  margin: 0;
  padding: 8px 12px;
  background-color: #ffffff;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  color: #991b1b;
  overflow-y: auto;
}

.success-container {
  margin-top: 20px;
}

.success-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.success-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.success-card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #166534;
}

.success-content-wrapper {
  overflow-y: auto;
  background-color: #f0fdf4;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #bbf7d0;
}

.success-content-preview {
  margin: 0;
  padding: 8px 12px;
  background-color: #ffffff;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  color: #166534;
  overflow-y: auto;
}
</style>
