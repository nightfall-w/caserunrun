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
            size="default"
            @change="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <FolderOpened/>
              </el-icon>
            </template>
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
            size="default"
            @change="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <Files/>
              </el-icon>
            </template>
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
            size="default"
            @change="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <Monitor/>
              </el-icon>
            </template>
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
            size="default"
            @change="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <Star/>
              </el-icon>
            </template>
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
            size="default"
            @keyup.enter="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <Search/>
              </el-icon>
            </template>
          </el-input>
        </el-col>

        <!-- 用例路径 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="3">
          <el-input
            v-model="searchForm.case_path"
            placeholder="用例路径"
            clearable
            size="default"
            @keyup.enter="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <Document/>
              </el-icon>
            </template>
          </el-input>
        </el-col>

        <!-- 作者 -->
        <el-col :xs="24" :sm="12" :md="4" :lg="3">
          <el-input
            v-model="searchForm.case_author"
            placeholder="作者"
            clearable
            size="default"
            @keyup.enter="handleSearch"
            class="filter-input"
          >
            <template #prefix>
              <el-icon>
                <User/>
              </el-icon>
            </template>
          </el-input>
        </el-col>

        <!-- 按钮区 -->
        <el-col :xs="24" :sm="12" :md="5" :lg="4">
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch" :loading="loading" size="default"
                       class="search-btn">
              <el-icon :size="16" class="icon">
                <Search/>
              </el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset" size="default" class="reset-btn">
              <el-icon :size="16" class="icon">
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
        <el-table-column prop="case_type" label="用例类型" width="90">
          <template #default="scope">
            <el-tag :type="scope.row.case_type === 'pytest' ? 'primary' : 'success'"
                    class="case-type-tag">
              {{ scope.row.case_type === 'pytest' ? 'Pytest' : 'TestNG' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="specific_type" label="测试类型" width="90">
          <template #default="scope">
            <el-tag :type="getSpecificTypeTagType(scope.row.specific_type)"
                    class="specific-type-tag">
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
            <el-tag :type="getCaseLevelTagType(scope.row.case_level)" class="level-tag">
              {{ `S${scope.row.case_level}` }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="update_time" label="上次同步" width="170">
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
        />
      </div>
    </div>

    <!-- 用例详情抽屉（通过组件引入） -->
    <TestCaseDetailDrawer
      :visible="detailDrawerVisible"
      @update:visible="detailDrawerVisible = $event"
      :test-case="selectedTestCase"
      :test-case-content="testCaseContent"
      @close="handleCloseDrawer"
    />
  </div>
</template>

<script setup>
import {onMounted, reactive, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {ElMessage} from 'element-plus'
import {
  Document,
  Files,
  FolderOpened,
  Monitor,
  Refresh,
  Search,
  Star,
  User
} from '@element-plus/icons-vue'
import {getCaseSourceList, getTestCaseContentDetail, getTestCaseList} from '@/network/api.js'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import 'highlight.js/styles/a11y-dark.css'
import TestCaseDetailDrawer from '@/components/TestCaseDetailDrawer.vue'

// 注册语言
hljs.registerLanguage('python', python)
hljs.registerLanguage('java', java)

// 路由参数
const route = useRoute()

// 数据状态
const testCaseList = ref([])
const loading = ref(false)
const detailDrawerVisible = ref(false)
const selectedTestCase = ref(null)
const projectOptions = ref([])
const testCaseContent = ref('')

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
  page_size: 20,
  total: 0
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

// 监听输入框变化自动触发搜索
watch(
  () => searchForm.case_name,
  (newVal, oldVal) => {
    if (newVal !== oldVal) handleSearch()
  }
)

watch(
  () => searchForm.case_author,
  (newVal, oldVal) => {
    if (newVal !== oldVal) handleSearch()
  }
)

watch(
  () => searchForm.case_path,
  (newVal, oldVal) => {
    if (newVal !== oldVal) handleSearch()
  }
)

// 获取项目选项列表
const fetchProjectOptions = async () => {
  try {
    const params = {workspaceId: route.params.id}
    const res = await getCaseSourceList(params)
    if (res.code === 0) {
      projectOptions.value = res.data.map(item => ({
        value: item.caseSourceValue?.projectId,
        label: `${item.caseSourceValue?.projectId}-${item.caseProjectName}`
      }))
      projectOptions.value = projectOptions.value.filter(option => option.value)
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
const handleSizeChange = val => {
  pagination.page_size = val
  pagination.page_num = 1
  fetchTestCaseList()
}

// 当前页改变
const handleCurrentChange = val => {
  pagination.page_num = val
  fetchTestCaseList()
}

// 打开详情抽屉的方法
const openDetailDrawer = async row => {
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
    } else {
      testCaseContent.value = '获取内容失败: ' + (res.message || '未知错误')
    }
  } catch (error) {
    testCaseContent.value = '获取内容失败: ' + error.message
  }
}

// 关闭抽屉回调
const handleCloseDrawer = () => {
  detailDrawerVisible.value = false
}

// 格式化时间
const formatTime = timeString => {
  if (!timeString) return '-'
  return new Date(timeString).toLocaleString('zh-CN')
}

// 获取测试类型名称
const getSpecificTypeName = type => {
  const typeMap = {
    10: 'Web',
    11: 'H5',
    12: '接口'
  }
  return typeMap[type] || type
}

// 获取测试类型标签类型
const getSpecificTypeTagType = type => {
  const typeMap = {
    10: 'primary',
    11: 'success',
    12: 'warning'
  }
  return typeMap[type] || 'info'
}

// 获取用例等级标签类型
const getCaseLevelTagType = level => {
  const levelMap = {
    0: 'danger',
    1: 'warning',
    2: 'primary',
    3: 'info'
  }
  return levelMap[level] || 'info'
}

// 从路径中提取文件名
const getFileNameFromPath = path => {
  if (!path) return '-'
  return path.split('/').pop() || path
}
</script>

<style scoped>
/* 基础容器样式 */
.test-case-list-container {
  padding: 10px 10px 0 10px;
  background-color: #f5f7fa;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  box-sizing: border-box;
  overflow: hidden;
}

/* 页面头部样式 */
.page-header {
  background: white;
  padding: 15px 20px;
  margin-bottom: 15px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #ebeef5;
  flex-shrink: 0;
}

.page-header h1 {
  margin: 0 0 6px 0;
  font-size: 20px;
  color: #2c3e50;
  font-weight: 700;
}

.page-header p {
  margin: 0;
  color: #7f8c8d;
  font-size: 14px;
}

/* 筛选区样式 */
.filter-container {
  background: white;
  padding: 15px 20px;
  margin-bottom: 15px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #ebeef5;
  flex-shrink: 0;
}

.filter-row {
  margin-bottom: 0;
}

.filter-input {
  width: 100%;
}

:deep(.el-input__wrapper) {
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(235, 238, 245, 0.5) !important;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper):hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1) !important;
  border-color: #c0c4cc !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.2) !important;
  border-color: #667eea !important;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}

.filter-actions {
  display: flex;
  gap: 12px;
  height: 100%;
  align-items: center;
  padding-left: 20px;
}

.search-btn {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
  border-radius: 12px;
  font-weight: 600;
  height: 42px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.search-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.reset-btn {
  flex: 1;
  background: #f4f4f5;
  border: 1px solid #dcdfe6;
  color: #606266;
  transition: all 0.3s ease;
  border-radius: 12px;
  font-weight: 600;
  height: 42px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.reset-btn:hover {
  background: #e6e6e6;
  border-color: #c0c4cc;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.icon {
  margin-right: 8px;
}

/* 表格容器样式 */
.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #ebeef5;
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
  font-size: 15px;
  border-collapse: separate;
}

/* 表头样式 */
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
.table-row td {
  color: #34495e;
  transition: all 0.3s ease;
  font-size: 15px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.table-row td::before {
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

.table-row:hover td {
  background-color: transparent !important;
  color: #2c3e50;
  transform: scale(1.02);
}

.table-row:hover td::before {
  opacity: 1;
}

.id-text {
  font-weight: 700;
  color: #667eea;
  font-size: 14px;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 20px;
}

.case-name-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
  color: #2c3e50;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(102, 126, 234, 0.05);
}

.case-name-text:hover {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.15);
  transform: translateX(5px);
}

.time-text,
.creator-text {
  color: #7f8c8d;
  font-size: 14px;
}

/* 标签样式 */
:deep(.case-type-tag),
:deep(.specific-type-tag),
:deep(.level-tag) {
  font-size: 13px;
  border-radius: 24px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-weight: 600;
}

:deep(.case-type-tag:hover),
:deep(.specific-type-tag:hover),
:deep(.level-tag:hover) {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 操作按钮样式 */
.operation-btn {
  color: #667eea !important;
  padding: 6px 6px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.operation-btn:hover {
  color: #5a6fd8 !important;
  background-color: rgba(102, 126, 234, 0.1) !important;
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

/* 分页样式 */
.pagination-container {
  padding: 20px;
  background: white;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.05);
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

:deep(.pagination) {
  font-size: 15px;
}

:deep(.el-pagination__sizes .el-input .el-input__inner),
:deep(.el-pagination__jump .el-input .el-input__inner) {
  font-size: 15px;
  padding: 10px 14px;
  border-radius: 8px;
}

:deep(.el-pagination .el-pagination__jump .el-input .el-input__inner) {
  width: 100px;
}

:deep(.el-pagination button) {
  border-radius: 8px;
  transition: all 0.3s ease;
  background: white;
  border: 1px solid #dcdfe6;
}

:deep(.el-pagination button:hover) {
  background-color: #f0f7ff;
  color: #667eea;
  border-color: #bfdbfe;
}
</style>
