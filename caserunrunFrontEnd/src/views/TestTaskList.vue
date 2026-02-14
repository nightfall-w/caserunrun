<template>
  <div class="test-task-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>测试任务列表</h1>
          <p>查看和管理测试任务执行情况</p>
        </div>
      </div>
    </div>

    <!-- 搜索和过滤条件 -->
    <div class="filter-container">
      <el-row :gutter="15" class="filter-row">
        <!-- 任务名称 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-input
            v-model="searchForm.task_name"
            placeholder="任务名称"
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

        <!-- 创建者 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-input
            v-model="searchForm.create_user"
            placeholder="创建者"
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

        <!-- 状态筛选 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <el-select
            v-model="searchForm.task_status"
            placeholder="任务状态"
            clearable
            size="default"
            @change="handleSearch"
            class="filter-select"
          >
            <el-option label="全部状态" value=""/>
            <el-option label="待运行" value="Pending"/>
            <el-option label="运行中" value="Running"/>
            <el-option label="已完成" value="Completed"/>
            <el-option label="失败" value="Failed"/>
            <el-option label="已取消" value="Canceled"/>
            <el-option label="超时" value="Timeout"/>
          </el-select>
        </el-col>

        <!-- 按钮区 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="5">
          <div class="filter-actions">
            <el-button
              type="primary"
              @click="handleSearch"
              :loading="loading"
              size="default"
              class="search-btn"
            >
              <el-icon :size="16" class="icon">
                <Search/>
              </el-icon>
              搜索
            </el-button>
            <el-button
              @click="handleReset"
              size="default"
              class="reset-btn"
            >
              <el-icon :size="16" class="icon">
                <Refresh/>
              </el-icon>
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 测试任务列表 -->
    <div class="table-container">
      <el-table
        :data="testTaskList"
        v-loading="loading"
        element-loading-text="加载中..."
        style="width: 100%"
        class="test-task-table"
        header-row-class-name="table-header"
        row-class-name="table-row"
        :default-sort="{ prop: 'create_time', order: 'descending' }"
        :cell-style="cellStyle"
        :row-style="{ transition: 'all 0.3s ease' }"
        border
        empty-text="暂无测试任务数据"
      >
        <el-table-column prop="id" label="ID" width="80">
          <template #default="scope">
            <span class="id-text">#{{ scope.row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="task_name" label="任务名称" min-width="200">
          <template #default="scope">
            <el-tooltip :content="scope.row.task_name" placement="top">
              <span class="task-name-text">{{ scope.row.task_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="test_plan_id" label="测试计划ID" width="120">
          <template #default="scope">
            <span class="plan-id-text">#{{ scope.row.test_plan_id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="test_environment" label="测试环境" width="120">
          <template #default="scope">
            <el-tag
              :type="getEnvironmentTagType(scope.row.test_environment)"
              class="environment-tag"
            >
              {{ scope.row.test_environment }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="task_execution_mode" label="执行方式" width="120">
          <template #default="scope">
            <el-tag
              :type="getExecutionModeTagType(scope.row.task_execution_mode)"
              class="mode-tag"
            >
              {{ scope.row.task_execution_mode === 'Serial' ? '串行' : '并行' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="180">
          <template #default="scope">
            <el-progress
              :percentage="calculateProgress(scope.row)"
              :stroke-width="10"
              :show-text="true"
              :color="getProgressColor(scope.row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="task_status" label="任务状态" width="120">
          <template #default="scope">
            <el-tag
              :type="getStatusTagType(scope.row.task_status)"
              class="status-tag"
            >
              {{ getStatusText(scope.row.task_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="create_user" label="创建者" width="140">
          <template #default="scope">
            <span class="creator-text">{{
                scope.row.creator?.nickname || scope.row.creator?.username || '未知'
              }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="create_time" label="创建时间" width="170">
          <template #default="scope">
            <span class="time-text">{{ formatTime(scope.row.create_time) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="update_time" label="更新时间" width="170">
          <template #default="scope">
            <span class="time-text">{{ formatTime(scope.row.update_time) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <div class="operation-buttons">
              <el-button
                size="small"
                type="primary"
                @click="handleViewDetail(scope.row)"
                class="operation-button"
              >
                查看详情
              </el-button>
            </div>
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
          size="default"
          :disabled="pagination.total === 0"
        />
      </div>
    </div>

    <!-- 任务详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="`任务详情 - ${selectedTask?.task_name || '未命名'}`"
      size="90%"
      direction="rtl"
      :before-close="handleCloseDetailDrawer"
      class="task-detail-drawer"
    >
      <div v-loading="detailLoading" class="detail-content">
        <template v-if="selectedTask">
          <!-- 任务基本信息 -->
          <div class="section">
            <h3 class="section-title">
              <el-icon>
                <Document/>
              </el-icon>
              任务基本信息
            </h3>
            <el-card class="info-card">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="任务ID">
                  #{{ selectedTask.id }}
                </el-descriptions-item>
                <el-descriptions-item label="测试计划ID">
                  #{{ selectedTask.test_plan_id }}
                </el-descriptions-item>
                <el-descriptions-item label="任务名称">
                  {{ selectedTask.task_name }}
                </el-descriptions-item>
                <el-descriptions-item label="测试环境">
                  <el-tag :type="getEnvironmentTagType(selectedTask.test_environment)">
                    {{ selectedTask.test_environment }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="执行方式">
                  <el-tag :type="getExecutionModeTagType(selectedTask.task_execution_mode)">
                    {{ selectedTask.task_execution_mode === 'Serial' ? '串行' : '并行' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="任务状态">
                  <el-tag :type="getStatusTagType(selectedTask.task_status)">
                    {{ getStatusText(selectedTask.task_status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="失败停止">
                  <el-tag :type="selectedTask.fail_stop ? 'danger' : 'success'">
                    {{ selectedTask.fail_stop ? '是' : '否' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建者">
                  {{ selectedTask.creator?.nickname || selectedTask.creator?.username || '未知' }}
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatTime(selectedTask.create_time) }}
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ formatTime(selectedTask.update_time) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </div>

          <!-- 任务统计 -->
          <div class="section">
            <h3 class="section-title">
              <el-icon>
                <DataAnalysis/>
              </el-icon>
              任务统计
            </h3>
            <el-card class="stat-card">
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon>
                      <Document/>
                    </el-icon>
                  </div>
                  <div class="stat-value">{{
                      selectedTask.task_result?.total_case_count || 0
                    }}
                  </div>
                  <div class="stat-label">总用例脚本数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon>
                      <Check/>
                    </el-icon>
                  </div>
                  <div class="stat-value">{{
                      selectedTask.task_result?.finished_case_count || 0
                    }}
                  </div>
                  <div class="stat-label">已完成</div>
                </div>
                <div class="stat-item">
                  <div class="stat-icon">
                    <el-icon>
                      <TrendCharts/>
                    </el-icon>
                  </div>
                  <div class="stat-value">
                    {{
                      selectedTask.task_result?.finished_case_count ?
                        Math.round((selectedTask.task_result.finished_case_count / selectedTask.task_result.total_case_count) * 100) : 0
                    }}%
                  </div>
                  <div class="stat-label">完成率</div>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 任务用例详情 -->
          <div class="section">
            <h3 class="section-title">
              <el-icon>
                <List/>
              </el-icon>
              任务用例详情
            </h3>
            <el-card class="jobs-card">
              <el-table
                :data="selectedTask.jobs"
                style="width: 100%"
                stripe
                border
                :default-sort="{ prop: 'create_time', order: 'ascending' }"
              >
                <el-table-column prop="id" label="Job ID" width="100">
                  <template #default="scope">
                    <span class="job-id">#{{ scope.row.id }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="case_name" label="用例名称" min-width="180">
                  <template #default="scope">
                    <el-tooltip :content="scope.row.case_name" placement="top">
                      <span class="case-name">{{ scope.row.case_name }}</span>
                    </el-tooltip>
                  </template>
                </el-table-column>

                <el-table-column prop="case_type" label="用例类型" width="120">
                  <template #default="scope">
                    <el-tag :type="scope.row.case_type === 'pytest' ? 'primary' : 'success'">
                      {{ scope.row.case_type }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="case_path" label="用例路径" min-width="200">
                  <template #default="scope">
                    <el-tooltip :content="scope.row.case_path" placement="top">
                      <span class="case-path">{{ scope.row.case_path }}</span>
                    </el-tooltip>
                  </template>
                </el-table-column>

                <el-table-column prop="job_status" label="执行状态" width="120">
                  <template #default="scope">
                    <el-tag :type="getStatusTagType(scope.row.job_status)">
                      {{ getStatusText(scope.row.job_status) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column label="function执行结果" width="220">
                  <template #default="scope">
                    <div v-if="isValidJobResult(scope.row.job_result)" class="result-stats">
                      <div class="result-item">
                        <span class="result-label">通过:</span>
                        <span class="result-value passed">{{
                            scope.row.job_result?.passed || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">失败:</span>
                        <span class="result-value failed">{{
                            scope.row.job_result?.failed || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">错误:</span>
                        <span class="result-value error">{{
                            scope.row.job_result?.error || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">忽略:</span>
                        <span class="result-value ignored">{{
                            scope.row.job_result?.ignored || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">跳过:</span>
                        <span class="result-value skipped">{{
                            scope.row.job_result?.skipped || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">总数:</span>
                        <span class="result-value total">{{
                            scope.row.job_result?.total || 0
                          }}</span>
                      </div>
                      <div class="result-item">
                        <span class="result-label">成功率:</span>
                        <span class="result-value success-rate">{{
                            scope.row.job_result?.successful?.toFixed(1) || 0
                          }}%</span>
                      </div>
                    </div>
                    <div v-else class="no-data">
                      无数据
                    </div>
                  </template>
                </el-table-column>


                <el-table-column label="操作" width="140" fixed="right">
                  <template #default="scope">
                    <!-- 第一行：查看用例按钮 -->
                    <div class="button-row">
                      <el-button
                        size="small"
                        type="primary"
                        @click="openCaseDetail(scope.row)"
                        :disabled="!scope.row.case_uuid || !scope.row.case_commit_id"
                        :icon="Document"
                        class="view-case-button"
                      >
                        查看用例
                      </el-button>
                    </div>

                    <!-- 第二行：查看报告按钮 -->
                    <div class="button-row">
                      <el-button
                        size="small"
                        type="success"
                        @click="openReport(scope.row)"
                        :disabled="!scope.row.report_path"
                        :icon="Document"
                        class="view-report-button"
                      >
                        查看报告
                      </el-button>
                    </div>
                  </template>
                </el-table-column>


              </el-table>
            </el-card>
          </div>
        </template>
      </div>
    </el-drawer>

    <!-- 用例详情抽屉 -->
    <TestCaseDetailDrawer
      :visible="caseDetailVisible"
      @update:visible="caseDetailVisible = $event"
      :test-case="selectedCase"
      :test-case-content="selectedCaseContent"
      @close="closeCaseDetail"
    />

  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue'
import {useRoute} from 'vue-router'
import {ElMessage} from 'element-plus'
import {getTestCaseContentDetail} from '@/network/api.js';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import java from 'highlight.js/lib/languages/java';
import 'highlight.js/styles/a11y-dark.css'; // 或者你喜欢的其他主题
import TestCaseDetailDrawer from '@/components/TestCaseDetailDrawer.vue'
import {
  Search,
  Refresh,
  User,
  Document,
  DataAnalysis,
  TrendCharts,
  Check,
  List
} from '@element-plus/icons-vue'
import {getTestTaskList, getTestTaskDetail} from '@/network/api.js'

// 注册语言
hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);
// 路由参数
const route = useRoute()

// 数据状态
const testTaskList = ref([])
const loading = ref(false)

// 搜索表单
const searchForm = reactive({
  task_name: '',
  create_user: '',
  task_status: ''
})

// 分页参数
const pagination = reactive({
  page_num: 1,
  page_size: 10,
  total: 0
})

// 详情抽屉相关状态
const detailDrawerVisible = ref(false)
const detailLoading = ref(false)
const selectedTask = ref(null)
const drawerWidth = ref('50%')
const codeRef = ref(null);

// 用例信息抽屉相关状态
const caseDetailVisible = ref(false)
const selectedCase = ref(null)
const selectedCaseContent = ref('')

// 单元格样式函数
const cellStyle = ({rowIndex}) => {
  return {
    padding: '16px 0',
    borderColor: 'rgba(235, 238, 245, 0.5)',
    backgroundColor: rowIndex % 2 === 0 ? 'rgba(250, 250, 250, 0.5)' : 'rgba(255, 255, 255, 0.7)'
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTestTaskList()
})

// 获取测试任务列表
const fetchTestTaskList = async () => {
  loading.value = true
  try {
    const params = {
      workspace_id: route.params.id,
      page_num: pagination.page_num,
      page_size: pagination.page_size,
      task_name: searchForm.task_name.trim(),
      create_user: searchForm.create_user.trim(),
      task_status: searchForm.task_status
    }

    // 过滤空参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await getTestTaskList(params)

    if (res.code === 0) {
      testTaskList.value = res.data.test_tasks || []
      pagination.total = res.data.total || 0
    } else {
      testTaskList.value = []
      pagination.total = 0
      ElMessage.error(res.message || '获取测试任务列表失败')
    }
  } catch (error) {
    console.error('获取测试任务列表异常:', error)
    testTaskList.value = []
    pagination.total = 0
    ElMessage.error('获取测试任务列表失败，请刷新页面重试')
  } finally {
    loading.value = false
  }
}

// 获取测试任务详情
const fetchTestTaskDetail = async (taskId) => {
  detailLoading.value = true
  try {
    const res = await getTestTaskDetail({task_id: taskId})

    if (res.code === 0) {
      selectedTask.value = res.data
      detailDrawerVisible.value = true
    } else {
      ElMessage.error(res.message || '获取任务详情失败')
    }
  } catch (error) {
    console.error('获取任务详情异常:', error)
    ElMessage.error('获取任务详情失败，请重试')
  } finally {
    detailLoading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page_num = 1
  fetchTestTaskList()
}

// 重置搜索条件
const handleReset = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = ''
  })
  pagination.page_num = 1
  fetchTestTaskList()
}

// 分页大小改变
const handleSizeChange = (val) => {
  pagination.page_size = val
  pagination.page_num = 1
  fetchTestTaskList()
}

// 当前页改变
const handleCurrentChange = (val) => {
  pagination.page_num = val
  fetchTestTaskList()
}

// 查看详情
const handleViewDetail = (row) => {
  fetchTestTaskDetail(row.id)
}

// 关闭详情抽屉
const handleCloseDetailDrawer = () => {
  detailDrawerVisible.value = false
  selectedTask.value = null
}


// 打开报告
const openReport = (job) => {
  if (job.report_path) {
    // 在新窗口打开报告
    window.open(job.report_path, '_blank')
  } else {
    ElMessage.warning('暂无报告可查看')
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '-'
  try {
    const date = new Date(timeString)
    if (isNaN(date.getTime())) return '-'
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-')
  } catch (error) {
    return timeString
  }
}

// 获取环境标签类型
const getEnvironmentTagType = (env) => {
  const typeMap = {
    QA: 'primary',
    PL: 'success',
    OL: 'warning'
  }
  return typeMap[env] || 'info'
}

// 获取执行方式标签类型
const getExecutionModeTagType = (mode) => {
  return mode === 'Serial' ? 'primary' : 'success'
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const typeMap = {
    Running: 'primary',
    Completed: 'success',
    Failed: 'danger',
    Exception: 'danger',
    Success: 'success',
    Timeout: 'warning',
    Canceled: 'info',
    Pending: 'info'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    Pending: '等待中',
    Running: '运行中',
    Completed: '已完成',
    Failed: '失败',
    Canceled: '已取消',
    Timeout: '超时',
    Exception: '异常',
    Success: '成功'
  }
  return textMap[status] || status
}

// 计算进度百分比
const calculateProgress = (row) => {
  if (!row.task_result || row.task_result.total_case_count === 0) {
    return 0;
  }
  const finished = row.task_result.finished_case_count || 0;
  const total = row.task_result.total_case_count;
  return Math.round((finished / total) * 100);
};

// 根据任务状态返回进度条颜色
const getProgressColor = (row) => {
  const status = row.task_status;
  switch (status) {
    case 'Running':
      return '#409EFF'; // 蓝色
    case 'Completed':
      return '#67C23A'; // 绿色
    case 'Success':
      return '#67C23A';
    case 'Failed':
      return '#F56C6C'; // 红色
    case 'Exception':
      return '#a41f4f';
    case 'Timeout':
      return '#E6A23C'; // 橙色
    default:
      return '#909399'; // 灰色
  }
};

const isValidJobResult = (jobResult) => {
  return !(!jobResult || typeof jobResult !== 'object');
};

// 打开用例详情的方法
const openCaseDetail = async (row) => {
  selectedCase.value = row
  selectedCaseContent.value = '加载中...'
  caseDetailVisible.value = true
  console.log('openCaseDetail', row)
  try {
    const res = await getTestCaseContentDetail({
      case_uuid: row.case_uuid,
      case_commit_id: row.case_commit_id
    })
    if (res.code === 0) {
      selectedCaseContent.value = res.data.case_content || '无内容'
    } else {
      selectedCaseContent.value = '获取内容失败: ' + (res.message || '未知错误')
    }
  } catch (error) {
    selectedCaseContent.value = '获取内容失败: ' + error.message
  }
}

// 关闭用例详情的方法
const closeCaseDetail = () => {
  caseDetailVisible.value = false
}

</script>

<style scoped>
/* 全局基础样式 */
.test-task-container {
  padding: 10px 10px 0 10px;
  background: #f5f7fa;
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

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h1 {
  margin: 0 0 6px 0;
  font-size: 20px;
  color: #2c3e50;
  font-weight: 700;
}

.title-section p {
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

.filter-select {
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

.test-task-table {
  border: none;
  flex: 1;
  overflow: auto;
  font-size: 15px;
  border-collapse: separate;
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

.task-name-text {
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

.task-name-text:hover {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.15);
  transform: translateX(5px);
}

.plan-id-text {
  color: #667eea;
  font-weight: 700;
  font-size: 14px;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 20px;
}

.time-text,
.creator-text {
  color: #7f8c8d;
  font-size: 14px;
}

/* 标签样式 */
:deep(.environment-tag),
:deep(.mode-tag),
:deep(.status-tag) {
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 24px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-weight: 600;
}

:deep(.environment-tag:hover),
:deep(.mode-tag:hover),
:deep(.status-tag:hover) {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 操作按钮样式 */
.operation-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.operation-button {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 10px;
  transition: all 0.3s ease;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.operation-button:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.4);
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

/* 详情抽屉样式 */
:deep(.task-detail-drawer) {
  .el-drawer__header {
    margin-bottom: 20px;
    border-bottom: 1px solid #ebeef5;
    padding-bottom: 20px;
    background: #f5f7fa;
  }

  .el-drawer__body {
    overflow-y: auto;
    background: #f8fafc;
  }
}

.detail-content {
  height: 100%;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 25px 0;
  padding-bottom: 15px;
  border-bottom: 2px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border-radius: 12px;
  padding: 15px;
}

.section-title .el-icon {
  color: #667eea;
  font-size: 24px;
}

.info-card {
  margin-bottom: 30px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #ebeef5;
  background: white;
}

.stat-card {
  margin-bottom: 30px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #ebeef5;
  background: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 25px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
}

.stat-item:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
  background: white;
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 15px;
  color: #667eea;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #2c3e50;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 15px;
  color: #7f8c8d;
  font-weight: 600;
}

.jobs-card {
  margin-bottom: 30px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #ebeef5;
  background: white;
}

.job-id {
  font-weight: 700;
  color: #667eea;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 20px;
}

.case-name,
.case-path {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.result-stats {
  display: flex;
  flex-direction: column;
  align-items: center; /* 水平居中 */
  justify-content: center; /* 垂直居中 */
  gap: 8px; /* 项目之间的间距 */
  padding: 10px 0;
}

.result-item {
  align-items: center;
  gap: 6px;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 6px;
  width: 100%; /* 确保宽度一致 */
  text-align: center; /* 文字居中 */
}

.result-label {
  color: #909399;
  font-weight: 600;
}

.result-value {
  font-weight: 700;
}

.result-value.passed {
  color: #67c23a;
}

.result-value.failed {
  color: #f56c6c;
}

.result-value.total {
  color: #409eff;
}

.result-value.error {
  color: #e6a23c; /* 橙色 */
}

.result-value.skipped {
  color: #909399; /* 灰色 */
}

.result-value.ignored {
  color: #909399; /* 灰色 */
}

.result-value.success-rate {
  color: #10b981; /* 绿色 */
}

.success-rate {
  font-weight: 700;
  color: #10b981;
  font-size: 15px;
  padding: 4px 10px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 20px;
}

/* 响应式布局优化 */
@media (max-width: 767px) {
  .test-task-container {
    padding: 10px;
    height: calc(100vh - 50px);
  }

  .page-header {
    padding: 15px;
  }

  .page-header h1 {
    font-size: 18px;
  }

  .filter-container {
    padding: 15px;
  }

  .filter-row {
    display: flex;
    flex-wrap: wrap;
  }

  .filter-actions {
    padding-left: 0;
    width: 100%;
    margin-top: 10px;
  }

  :deep(.el-table__fixed-right) {
    width: 140px !important;
  }

  .operation-buttons {
    justify-content: flex-start;
  }

  .operation-button {
    padding: 8px 12px;
    margin-bottom: 6px;
  }

  /* 抽屉在移动端的调整 */
  :deep(.task-detail-drawer) {
    .el-drawer__body {
      padding: 20px;
    }
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 20px;
    padding: 20px 0;
  }

  .section-title {
    font-size: 18px;
  }

  .stat-value {
    font-size: 26px;
  }
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .test-task-container {
    background: #1e293b;
  }

  .page-header,
  .filter-container,
  .table-container,
  .pagination-container {
    background-color: #27364b;
    border-color: #334155;
  }

  .page-header h1,
  .title-section h1,
  .task-name-text {
    color: #e2e2e2;
  }

  .page-header p,
  .title-section p,
  .creator-text,
  .time-text {
    color: #a0a0c0;
  }

  .table-row td {
    color: #d0d0e7;
  }

  .section-title {
    color: #e2e2e2;
    border-bottom: 1px solid #475569;
  }

  .stat-card {
    background: #334155;
    border: 1px solid #475569;
  }
}

/* 统一设置选择器和输入框的圆角 */
:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(235, 238, 245, 0.5) !important;
  transition: all 0.3s ease;
}

.no-data {
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 10px 0;
}


:deep(.detail-drawer .el-drawer__body) {
  padding: 24px;
  overflow: hidden;
}

.detail-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
}


@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}


</style>
