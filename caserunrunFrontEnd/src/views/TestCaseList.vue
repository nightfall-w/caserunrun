<template>
  <div class="test-case-list-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>测试用例列表</h1>
      <p>查看和管理您的测试用例</p>
    </div>

    <!-- 搜索和过滤条件 -->
    <div class="filter-container">
      <el-row :gutter="8" class="filter-row">
        <!-- 项目选择 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="4">
          <el-select
            v-model="searchForm.git_project_id"
            placeholder="请选择项目"
            clearable
            size="small" style="width: 100%"
            @change="handleSearch"
          >
            <el-option
              v-for="project in projectOptions"
              :key="project.value"
              :label="project.label"
              :value="project.value"
            />
          </el-select>
        </el-col>

        <!-- 用例类型 -->
        <el-col :xs="24" :sm="12" :md="4" :lg="2">
          <el-select
            v-model="searchForm.case_type"
            placeholder="用例类型"
            clearable
            size="small" style="width: 100%"
            @change="handleSearch"
          >
            <el-option label="Pytest" value="pytest"/>
            <el-option label="TestNG" value="testng"/>
          </el-select>
        </el-col>

        <!-- 测试类型 -->
        <el-col :xs="24" :sm="12" :md="4" :lg="2">
          <el-select
            v-model="searchForm.specific_type"
            placeholder="测试类型"
            clearable
            size="small" style="width: 100%"
            @change="handleSearch"
          >
            <el-option label="Web" :value="10"/>
            <el-option label="H5" :value="11"/>
            <el-option label="接口" :value="12"/>
          </el-select>
        </el-col>

        <!-- 用例等级 -->
        <el-col :xs="24" :sm="12" :md="4" :lg="2">
          <el-select
            v-model="searchForm.case_level"
            placeholder="用例等级"
            clearable
            size="small" style="width: 100%"
            @change="handleSearch"
          >
            <el-option label="S0" :value="0"/>
            <el-option label="S1" :value="1"/>
            <el-option label="S2" :value="2"/>
            <el-option label="S3" :value="3"/>
          </el-select>
        </el-col>

        <!-- 用例名称 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="4">
          <el-input
            v-model="searchForm.case_name"
            placeholder="用例名称"
            clearable
            size="small"
            @keyup.enter="handleSearch"
          />
        </el-col>

        <!-- 用例路径 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="3">
          <el-input
            v-model="searchForm.case_path"
            placeholder="用例路径"
            clearable
            size="small"
            @keyup.enter="handleSearch"
          />
        </el-col>

        <!-- 作者 -->
        <el-col :xs="24" :sm="12" :md="4" :lg="3">
          <el-input
            v-model="searchForm.case_author"
            placeholder="作者"
            clearable
            size="small"
            @keyup.enter="handleSearch"
          />
        </el-col>

        <!-- 按钮区 -->
        <el-col :xs="24" :sm="12" :md="5" :lg="4">
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch" :loading="loading" size="small"
                       class="search-btn">
              <el-icon :size="14" class="icon">
                <Search/>
              </el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset" size="small" class="reset-btn">
              <el-icon :size="14" class="icon">
                <Refresh/>
              </el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 测试用例列表 -->
    <div class="table-container">
      <el-table
        :data="testCaseList"
        v-loading="loading"
        element-loading-text="加载中..."
        style="width: 100%"
        class="test-case-table"
        header-row-class-name="table-header"
        row-class-name="table-row"
        :default-sort="{ prop: 'create_time', order: 'descending' }"
        :cell-style="cellStyle"
        :row-style="{ transition: 'all 0.25s ease' }"
        border
      >
        <el-table-column prop="id" label="ID" width="180">
          <template #default="scope">
            <span class="id-text">{{ scope.row.git_project_name }}-{{ scope.row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="case_type" label="用例类型" width="90">
          <template #default="scope">
            <el-tag
              :type="scope.row.case_type === 'pytest' ? 'primary' : 'success'"
              class="case-type-tag"
            >
              {{ scope.row.case_type === 'pytest' ? 'Pytest' : 'TestNG' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="specific_type" label="测试类型" width="90">
          <template #default="scope">
            <el-tag
              :type="getSpecificTypeTagType(scope.row.specific_type)"
              class="specific-type-tag"
            >
              {{ getSpecificTypeName(scope.row.specific_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="case_name" label="用例名称" min-width="180">
          <template #default="scope">
            <el-tooltip :content="scope.row.case_name" placement="top">
              <span class="case-name-text">{{ scope.row.case_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="case_path" label="用例路径" min-width="180">
          <template #default="scope">
            <el-tooltip :content="scope.row.case_path" placement="top">
              <span class="case-name-text">{{ getFileNameFromPath(scope.row.case_path) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="case_author" label="作者" width="130">
          <template #default="scope">
            <el-tooltip
              v-if="scope.row.case_author.nickname"
              :content="`${scope.row.case_author.nickname}(${scope.row.case_author.username})`"
              placement="top"
            >
              <span class="author-text">{{ scope.row.case_author.nickname }}</span>
            </el-tooltip>
            <span v-else class="author-text">{{ scope.row.case_author.username }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="case_level" label="等级" width="70">
          <template #default="scope">
            <el-tag
              :type="getCaseLevelTagType(scope.row.case_level)"
              class="level-tag"
            >
              {{ `S${scope.row.case_level}` }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="update_time" label="上次同步" width="160">
          <template #default="scope">
            <span class="time-text">{{ formatTime(scope.row.update_time) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="70" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              link
              @click="openDetailDrawer(scope.row)"
              class="operation-btn"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page_num"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          class="pagination"
          size="small"
        />
      </div>
    </div>

    <!-- 用例详情抽屉（完全重构版） -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="用例详情"
      direction="rtl"
      :size="drawerWidth"
      :with-header="true"
      :resizable="true"
      class="detail-drawer"
    >
      <!-- 抽屉内容区 -->
      <div class="drawer-content">
        <!-- 顶部信息栏 -->
        <div class="detail-header">
          <div class="detail-title">
            <h2>{{ selectedTestCase?.case_name || '未选择用例' }}</h2>
            <p class="sub-title">ID: {{ selectedTestCase?.id || '-' }} | 上次同步:
              {{ formatTime(selectedTestCase?.update_time) }}</p>
          </div>
          <div class="detail-tags">
            <el-tag
              :type="selectedTestCase?.case_type === 'pytest' ? 'primary' : 'success'"
              class="tag-type"
            >
              {{ selectedTestCase?.case_type === 'pytest' ? 'Python (Pytest)' : 'Java (TestNG)' }}
            </el-tag>
            <el-tag
              :type="getSpecificTypeTagType(selectedTestCase?.specific_type)"
              class="tag-type"
            >
              {{ getSpecificTypeName(selectedTestCase?.specific_type) }}
            </el-tag>
            <el-tag
              :type="getCaseLevelTagType(selectedTestCase?.case_level)"
              class="tag-priority"
            >
              S{{ selectedTestCase?.case_level !== undefined ? selectedTestCase?.case_level : '-' }}
            </el-tag>
          </div>
        </div>

        <div class="detail-grid">
          <!-- 左侧信息面板 -->
          <div class="info-panel">
            <div class="panel-card">
              <h3 class="panel-title">
                <el-icon :size="18" class="panel-icon">
                  <InfoFilled/>
                </el-icon>
                基础信息
              </h3>
              <div class="info-list">
                <div class="info-item">
                  <div class="info-label">
                    <el-icon>
                      <Document/>
                    </el-icon>
                    <span>项目名称</span>
                  </div>
                  <div class="info-value">{{ selectedTestCase?.git_project_name || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <el-icon>
                      <Collection/>
                    </el-icon>
                    <span>用例名称</span>
                  </div>
                  <div class="info-value">{{ selectedTestCase?.case_name || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <el-icon>
                      <Folder/>
                    </el-icon>
                    <span>用例路径</span>
                  </div>
                  <div class="info-value mono-text">{{ selectedTestCase?.case_path || '-' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <el-icon>
                      <User/>
                    </el-icon>
                    <span>作者</span>
                  </div>
                  <div class="info-value" v-if="selectedTestCase?.case_author.nickname">
                    <el-tooltip
                      :content="`${selectedTestCase?.case_author.nickname}(${selectedTestCase?.case_author.username})`"
                      placement="top"
                    >
                      <span class="author-text">{{ selectedTestCase?.case_author.nickname }}</span>
                    </el-tooltip>
                  </div>
                  <div class="info-value" v-else>{{
                      selectedTestCase?.case_author.username
                    }}
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">
                    <el-icon>
                      <Coin/>
                    </el-icon>
                    <span>commit_id</span>
                  </div>
                  <div class="info-value">{{ selectedTestCase?.case_commit_id || '-' }}</div>
                </div>
              </div>
            </div>

            <!-- 额外信息卡片 -->
            <div class="panel-card mt-4">
              <h3 class="panel-title">
                <el-icon :size="18" class="panel-icon">
                  <Memo/>
                </el-icon>
                测试信息
              </h3>
              <div class="stat-grid">
                <div class="stat-item">
                  <div class="stat-label">执行次数</div>
                  <div class="stat-value">42</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">通过率</div>
                  <div class="stat-value success">96%</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">最近结果</div>
                  <div class="stat-value warning">跳过</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧代码面板 -->
          <div class="code-panel">
            <div class="panel-card code-card">
              <div class="code-header">
                <h3 class="panel-title">
                  <el-icon :size="18" class="panel-icon">
                    <Document/>
                  </el-icon>
                  代码预览
                </h3>
                <div class="code-actions">
                  <span class="code-language">
                    {{ selectedTestCase?.case_type === 'pytest' ? 'Python' : 'Java' }}
                  </span>
                  <el-button
                    size="small"
                    type="primary"
                    @click="copyCode"
                    :disabled="!testCaseContent || testCaseContent.includes('加载中')"
                    class="copy-btn"
                  >
                    <el-icon :size="16">
                      <CopyDocument/>
                    </el-icon>
                    复制代码
                  </el-button>
                </div>
              </div>
              <div class="code-content-wrapper">
                <pre v-if="!testCaseContent.includes('加载中')">
                  <code
                    class="code-content"
                    :class="selectedTestCase?.case_type === 'pytest' ? 'language-python' : 'language-java'"
                    ref="codeRef"
                  >{{ testCaseContent || '无代码内容' }}</code>
                </pre>
                <div v-else class="code-loading">
                  <el-icon class="loading-spinner is-loading">
                    <Loading/>
                  </el-icon>
                  <p>加载代码中...</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 抽屉底部按钮 -->
      <template #footer>
        <div class="drawer-actions">
          <el-button
            type="default"
            @click="detailDrawerVisible = false"
            class="btn-secondary"
          >
            关闭
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import {nextTick, onBeforeMount, onMounted, reactive, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {ElMessage, ElNotification} from 'element-plus'
import {
  Coin,
  CopyDocument,
  Document,
  Document as Collection,
  Folder,
  InfoFilled,
  Loading,
  Memo,
  Refresh,
  Search,
  User
} from '@element-plus/icons-vue'
import {getCaseSourceList, getTestCaseContentDetail, getTestCaseList} from '@/network/api.js'
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import java from 'highlight.js/lib/languages/java';
import 'highlight.js/styles/a11y-dark.css';
// 注册语言
hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);

// 路由参数
const route = useRoute()

// 数据状态
const testCaseList = ref([])
const loading = ref(false)
const detailDrawerVisible = ref(false)
const selectedTestCase = ref(null)
const projectOptions = ref([])
const testCaseContent = ref('')
const codeRef = ref(null)
const drawerWidth = ref('80%')

// 搜索表单
const searchForm = reactive({
  git_project_id: '',
  case_type: '',
  specific_type: '',
  case_name: '',
  case_author: '',
  case_level: '',
  case_path: ''
})

// 分页参数
const pagination = reactive({
  page_num: 1,
  page_size: 10,
  total: 0
})

// 计算抽屉宽度（响应式处理）
onBeforeMount(() => {
  const updateDrawerWidth = () => {
    if (window.innerWidth < 1200) {
      drawerWidth.value = '90%'
    } else {
      drawerWidth.value = '80%'
    }
  }

  updateDrawerWidth()
  window.addEventListener('resize', updateDrawerWidth)

  return () => {
    window.removeEventListener('resize', updateDrawerWidth)
  }
})

// 单元格样式函数
const cellStyle = ({rowIndex}) => {
  return {
    padding: '12px 0',
    borderColor: '#f0f0f0',
    backgroundColor: rowIndex % 2 === 0 ? '#ffffff' : '#fafafa'
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProjectOptions()
  fetchTestCaseList()
})

// 监听用例名称和作者输入框的变化，自动触发搜索
watch(
  () => searchForm.case_name,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      handleSearch()
    }
  }
)

watch(
  () => searchForm.case_author,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      handleSearch()
    }
  }
)

watch(
  () => searchForm.case_path,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      handleSearch()
    }
  }
)

// 获取项目选项列表
const fetchProjectOptions = async () => {
  try {
    const params = {
      workspaceId: route.params.id
    }

    const res = await getCaseSourceList(params)

    if (res.code === 0) {
      projectOptions.value = res.data.map(item => ({
        value: item.caseSourceValue?.projectId,
        label: `${item.caseSourceValue?.projectId}-${item.caseProjectName}`
      }))

      projectOptions.value = projectOptions.value.filter(option => option.value)

      // 去重处理
      const uniqueOptions = []
      const seenValues = new Set()
      projectOptions.value.forEach(option => {
        if (!seenValues.has(option.value)) {
          seenValues.add(option.value)
          uniqueOptions.push(option)
        }
      })
      projectOptions.value = uniqueOptions
    } else {
      ElMessage.error(res.message || '获取项目列表失败')
    }
  } catch (error) {
    ElMessage.error('获取项目列表失败: ' + error.message)
  }
}

// 获取测试用例列表
const fetchTestCaseList = async () => {
  loading.value = true
  try {
    const params = {
      workspace_id: route.params.id,
      git_project_id: searchForm.git_project_id,
      case_type: searchForm.case_type,
      specific_type: searchForm.specific_type,
      case_name: searchForm.case_name,
      case_author: searchForm.case_author,
      case_level: searchForm.case_level,
      case_path: searchForm.case_path,
      page_num: pagination.page_num,
      page_size: pagination.page_size
    }

    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await getTestCaseList(params)

    if (res.code === 0) {
      testCaseList.value = res.data.items || []
      pagination.total = res.data.total || 0
    } else {
      ElMessage.error(res.message || '获取测试用例列表失败')
    }
  } catch (error) {
    ElMessage.error('获取测试用例列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page_num = 1
  fetchTestCaseList()
}

// 重置搜索条件
const handleReset = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = ''
  })
  pagination.page_num = 1
  fetchTestCaseList()
}

// 分页大小改变
const handleSizeChange = (val) => {
  pagination.page_size = val
  pagination.page_num = 1
  fetchTestCaseList()
}

// 当前页改变
const handleCurrentChange = (val) => {
  pagination.page_num = val
  fetchTestCaseList()
}

// 打开详情抽屉
const openDetailDrawer = async (row) => {
  selectedTestCase.value = row
  testCaseContent.value = '加载中...'
  detailDrawerVisible.value = true

  try {
    const res = await getTestCaseContentDetail({
      case_uuid: row.case_uuid,
      case_commit_id: row.case_commit_id
    })

    if (res.code === 0) {
      testCaseContent.value = res.data.case_content || '无内容'

      nextTick(() => {
        if (codeRef.value) {
          codeRef.value.classList.remove('hljs')
          codeRef.value.removeAttribute('data-highlighted')
          hljs.highlightElement(codeRef.value)
        }
      })
    } else {
      testCaseContent.value = '获取内容失败: ' + (res.message || '未知错误')
    }
  } catch (error) {
    testCaseContent.value = '获取内容失败: ' + error.message
  }
}

// 复制代码
const copyCode = () => {
  navigator.clipboard.writeText(testCaseContent.value).then(() => {
    ElNotification({
      title: '成功',
      message: '代码已复制到剪贴板',
      type: 'success',
      duration: 2000
    })
  }).catch(() => {
    ElNotification({
      title: '失败',
      message: '复制失败，请手动复制',
      type: 'error',
      duration: 2000
    })
  })
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
  return typeMap[type] || 'info'
}

// 获取用例等级标签类型
const getCaseLevelTagType = (level) => {
  const levelMap = {
    0: 'danger',    // S0
    1: 'warning', // S1
    2: 'primary', // S2
    3: 'info'  // S3
  }
  return levelMap[level] || 'info'
}

// 从路径中提取文件名
const getFileNameFromPath = (path) => {
  if (!path) return '-'
  // 获取最后一个斜杠后的部分作为文件名
  return path.split('/').pop() || path
}

</script>

<style scoped>
/* 基础容器样式 */
.test-case-list-container {
  padding: 5px;
  background-color: #f5f7fa;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
}

.page-header {
  background: white;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #ebeef5;
  flex-shrink: 0;
}

.page-header h1 {
  margin: 0 0 5px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #918c8c;
  font-size: 12px;
}

/* 筛选区样式 */
.filter-container {
  background: white;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.filter-row {
  margin-bottom: 0;
}

:deep(.el-col-lg-3 .el-select),
:deep(.el-col-md-4 .el-select) {
  width: 100% !important;
}

:deep(.el-col-lg-3 .el-input__inner),
:deep(.el-col-md-4 .el-input__inner) {
  padding: 0 10px;
  font-size: 12px;
}

.filter-actions {
  display: flex;
  gap: 1px;
  height: 100%;
  align-items: center;
  padding-left: 20px;
}

.search-btn {
  flex: 1;
  background: #409eff;
  border-color: #409eff;
  transition: all 0.2s ease;
}

.search-btn:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.reset-btn {
  flex: 1;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background: #f0f2f5;
}

.icon {
  margin-right: 4px;
}

/* 表格容器 */
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.test-case-table {
  border: none;
  flex: 1;
  overflow: auto;
  font-size: 13px;
  border-collapse: separate;
}

/* 表头样式 */
:deep(.table-header th) {
  background: linear-gradient(180deg, #e2e8f0 0%, #cbd5e0 100%) !important;
  color: #1e293b !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  padding: 10px 0 !important;
  border-bottom: 1px solid #cbd5e1 !important;
  position: relative;
}

/* 简化hover效果，使用box-shadow替代伪元素 */
:deep(.table-header th:hover) {
  box-shadow: inset 0 -2px 0 #679ae5;
}

/* 表格行样式 */
.table-row td {
  color: #334155;
  transition: all 0.25s ease;
  font-size: 13px;
}

.table-row:hover td {
  background-color: #f0f7ff !important;
  color: #1e40af;
}

.id-text {
  font-weight: 400;
  color: #1e40af;
  font-size: 11px;
}

.case-name-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
  color: #0a67e1;
  font-weight: 400;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 2px;
}

.case-name-text:hover {
  color: #04288c;
  background-color: rgba(59, 130, 246, 0.1);
}

.time-text {
  color: #64748b;
  font-size: 12px;
}

/* 标签样式 */
:deep(.case-type-tag),
:deep(.specific-type-tag),
:deep(.level-tag) {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

:deep(.case-type-tag) {
  background-color: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

:deep(.specific-type-tag) {
  background-color: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

:deep(.case-type-tag:hover),
:deep(.specific-type-tag:hover),
:deep(.level-tag:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

/* 操作按钮 */
.operation-btn {
  color: #3b82f6 !important;
  padding: 3px 5px !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  transition: all 0.2s ease !important;
  border-radius: 4px !important;
}

.operation-btn:hover {
  color: #1d4ed8 !important;
  background-color: rgba(59, 130, 246, 0.1) !important;
}

/* 分页样式 */
.pagination-container {
  padding: 15px 20px;
  background: white;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.02);
}

:deep(.pagination) {
  font-size: 13px;
}

:deep(.el-pagination__sizes .el-input .el-input__inner),
:deep(.el-pagination__jump .el-input .el-input__inner) {
  font-size: 13px;
  padding: 5px 10px;
  border-radius: 4px;
  border-color: #e2e8f0;
}

:deep(.el-pagination button) {
  border-radius: 4px;
  transition: all 0.2s ease;
}

:deep(.el-pagination button:hover) {
  background-color: #f0f7ff;
  color: #409eff;
  border-color: #bfdbfe;
}

/* 响应式布局 - 筛选区 */
@media (max-width: 1200px) {
  .filter-container {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .filter-container {
    padding: 10px;
  }

  .filter-row {
    display: flex;
    flex-wrap: wrap;
  }
}

/* 抽屉样式（完全重构） */
.detail-drawer {
  --el-drawer-bg-color: #f8fafc;
  --el-drawer-border-radius: 12px 0 0 12px;
}

:deep(.detail-drawer .el-drawer__header) {
  display: none; /* 隐藏默认标题栏 */
}

:deep(.detail-drawer .el-drawer__body) {
  padding: 24px;
  overflow: hidden;
}

.drawer-content {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 0; /* 移除原来的间隙 */
}

/* 顶部信息栏 */
.detail-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0; /* 减少底部边距 */
}

.detail-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
}

.sub-title {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #64748b;
}

.detail-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

:deep(.tag-type) {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 6px;
  background-color: rgba(64, 158, 255, 0.1);
  color: #3b82f6;
  border: none;
  transition: all 0.2s ease;
}

:deep(.tag-type:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

:deep(.tag-priority) {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  transition: all 0.2s ease;
}

/* 主要内容区网格布局 */
.detail-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  flex: 1;
  overflow: hidden;
  margin-top: 10px; /* 减少顶部边距 */
}

/* 面板通用样式 */
.panel-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0; /* 防止卡片被压缩 */
}

.panel-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.panel-title {
  margin: 0;
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon {
  color: #3b82f6;
}

.mt-4 {
  margin-top: 16px;
  flex-shrink: 0; /* 防止测试信息卡片被压缩 */
}

/* 左侧信息面板 */
.info-panel {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding-right: 8px;
  max-height: 100%;
}

.info-list {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 8px;
  background-color: #f8fafc;
  transition: all 0.3s ease;
  border: 1px solid #eaeaea;
}

.info-item:hover {
  background-color: #f0f9ff;
  border-color: #bae6fd;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.info-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label .el-icon {
  font-size: 14px;
  color: #3b82f6;
}

.info-value {
  font-size: 14px;
  color: #1e293b;
  word-break: break-all;
  line-height: 1.2;
  font-weight: 500;
}


.mono-text {
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.05);
  padding: 2px 4px;
  border-radius: 4px;
}

/* 统计信息网格 */
.stat-grid {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.stat-value.success {
  color: #10b981;
}

.stat-value.warning {
  color: #f59e0b;
}

/* 右侧代码面板 */
.code-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  margin-top: 0; /* 移除顶部边距 */
}

.code-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  background-color: #181818;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.code-card .panel-title {
  background: linear-gradient(to right, #1e293b, #0f172a);
  color: #e2e8f0;
  border-bottom: 1px solid #334155;
  padding: 12px 10px; /* 减少垂直内边距 */
}


.code-card .panel-icon {
  color: #94a3b8;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px; /* 添加左右内边距 */
}

.code-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.code-language {
  font-size: 13px;
  color: #94a3b8;
  background-color: #334155;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Fira Code', monospace;
}

.copy-btn {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
  transition: all 0.2s;
  padding: 6px 12px; /* 调整内边距 */
  border-radius: 6px;
  margin-right: 10px; /* 添加右边距 */
}

.copy-btn:hover {
  background-color: #2563eb;
  border-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 代码内容区域 */
.code-content-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0 15px 15px 15px; /* 减少内边距 */
  position: relative;
}


.code-content {
  display: block;
  padding: 5px 15px 15px 15px; /* 减少内边距 */
  overflow-x: auto;
  font-family: "Fira Code",
  "JetBrains Mono",
  "Consolas",
  "Menlo",
  "Monaco",
  "Courier New",
  monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #f3f4f6;
  opacity: 0.95;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  white-space: pre;
  min-width: fit-content;
  margin: 0;
}

.hljs-comment {
  color: #dadde5; /* 注释颜色 */
}

/* 代码加载状态 */
.code-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  gap: 12px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 底部按钮区域 */
:deep(.detail-drawer .el-drawer__footer) {
  padding: 10px 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background-color: #ffffff;
  border-radius: 0 0 0 12px;
}

.drawer-actions {
  display: flex;
  gap: 12px;
  width: 100%;
  justify-content: flex-end;
}

.btn-secondary {
  padding: 8px 20px;
  font-size: 14px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background-color: #f1f5f9;
  transform: translateY(-2px);
}


/* 响应式调整 */
@media (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: 280px 1fr;
  }
}

@media (max-width: 992px) {
  .detail-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .info-panel {
    max-height: 360px;
  }
}

@media (max-width: 768px) {
  :deep(.detail-drawer .el-drawer__body) {
    padding: 16px;
  }

  .detail-title h2 {
    font-size: 18px;
  }

  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }

  .stat-item:nth-child(3) {
    grid-column: span 2;
  }
}
</style>
