<template>
  <div class="test-plan-list-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>测试计划列表</h1>
          <p>创建和管理您的测试计划</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate" class="create-btn" size="small">
            <el-icon>
              <Plus/>
            </el-icon>
            新建测试计划
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索和过滤条件 -->
    <div class="filter-container">
      <el-row :gutter="8" class="filter-row">
        <!-- 计划名称 -->
        <el-col :xs="24" :sm="12" :md="6" :lg="4">
          <el-input
            v-model="searchForm.plan_name"
            placeholder="计划名称"
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
        <el-col :xs="24" :sm="12" :md="6" :lg="4">
          <el-input
            v-model="searchForm.creator"
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

    <!-- 测试计划列表 -->
    <div class="table-container">
      <el-table
        :data="testPlanList"
        v-loading="loading"
        element-loading-text="加载中..."
        style="width: 100%"
        class="test-plan-table"
        header-row-class-name="table-header"
        row-class-name="table-row"
        :default-sort="{ prop: 'create_time', order: 'descending' }"
        :cell-style="cellStyle"
        :row-style="{ transition: 'all 0.25s ease' }"
        border
        empty-text="暂无测试计划数据，点击「新建测试计划」开始创建"
      >
        <el-table-column prop="test_plan_id" label="ID" width="60">
          <template #default="scope">
            <span class="id-text">{{ scope.row.test_plan_id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="plan_name" label="计划名称" min-width="180">
          <template #default="scope">
            <el-tooltip :content="scope.row.plan_name" placement="top">
              <span class="plan-name-text">{{ scope.row.plan_name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="scope">
            <el-tooltip :content="scope.row.description" placement="top"
                        v-if="scope.row.description">
              <span class="description-text">{{ truncateDescription(scope.row.description) }}</span>
            </el-tooltip>
            <span v-else>暂无描述</span>
          </template>
        </el-table-column>

        <el-table-column prop="test_environment" label="测试环境" width="100">
          <template #default="scope">
            <el-tag
              :type="getEnvironmentTagType(scope.row.test_environment)"
              class="environment-tag"
            >
              {{ scope.row.test_environment }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="execution_mode" label="执行方式" width="100">
          <template #default="scope">
            <el-tag
              :type="getExecutionModeTagType(scope.row.execution_mode)"
              class="mode-tag"
            >
              {{ scope.row.execution_mode === 'Serial' ? '串行' : '并行' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 新增：定时器状态列 -->
        <el-table-column prop="enable_schedule" label="定时执行" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.enable_schedule ? 'success' : 'danger'"
              class="mode-tag"
            >
              {{ scope.row.enable_schedule ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 新增：通知状态列 -->
        <el-table-column prop="enable_notification" label="执行通知" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.enable_notification ? 'success' : 'danger'"
              class="mode-tag"
            >
              {{ scope.row.enable_notification ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="total_case_count" label="用例数" width="80">
          <template #default="scope">
            <span class="count-text">{{ scope.row.total_case_count || 0 }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="create_user" label="创建者" width="120">
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

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <div class="operation-buttons">
              <el-button size="small" type="warning" @click="handleEdit(scope.row)"
                         class="operation-button" :icon="Edit" circle/>
              <el-button size="small" type="primary" @click="handleTrigger(scope.row)"
                         class="operation-button" :icon="VideoPlay" circle/>
              <el-button size="small" type="success" @click="handleViewCases(scope.row)"
                         class="operation-button" :icon="Operation" circle/>
              <el-button size="small" type="danger" @click="handleDelete(scope.row)"
                         class="operation-button" :icon="Delete" circle/>
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

    <!-- 创建/编辑测试计划对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      top="50px"
      :before-close="handleDialogClose"
      class="test-plan-dialog custom-dialog"
      destroy-on-close
    >
      <div class="dialog-header">
        <h3 class="dialog-title">{{ dialogTitle }}</h3>
      </div>
      <el-form
        ref="planFormRef"
        :model="planForm"
        :rules="planFormRules"
        label-width="120px"
        class="plan-form custom-form"
        size="small"
      >
        <el-form-item label="计划名称" prop="plan_name">
          <el-input
            v-model="planForm.plan_name"
            placeholder="请输入测试计划名称"
            maxlength="50"
            class="custom-input"
          />
        </el-form-item>

        <el-form-item label="测试环境" prop="test_environment">
          <el-select
            v-model="planForm.test_environment"
            placeholder="请选择测试环境" style="width: 100%"
            class="custom-select"
          >
            <el-option label="QA" value="QA"/>
            <el-option label="PL" value="PL"/>
            <el-option label="OL" value="OL"/>
          </el-select>
        </el-form-item>

        <el-form-item label="执行方式" prop="execution_mode">
          <el-select
            v-model="planForm.execution_mode"
            placeholder="请选择执行方式" style="width: 100%"
            class="custom-select"
          >
            <el-option label="串行" value="Serial"/>
            <el-option label="并行" value="Parallel"/>
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="planForm.description"
            type="textarea"
            :rows="1"
            autosize
            placeholder="请输入测试计划描述"
            maxlength="200"
            class="custom-textarea"
          />
        </el-form-item>

        <!-- 新增：定时器状态 -->
        <el-form-item label="定时器状态" prop="enable_schedule">
          <el-switch
            v-model="planForm.enable_schedule"
            active-text="开启"
            inactive-text="关闭"
            active-value="true"
            inactive-value="false"
          />
        </el-form-item>

        <!-- 新增：定时规则（Cron表达式） -->
        <el-form-item
          label="定时规则(Cron)"
          prop="schedule_cron_expression"
          :rules="planForm.enable_schedule === 'true' ? [
      {required: true, message: '开启定时后必须填写Cron表达式', trigger: 'blur'},
      {validator: validateCronExpression, trigger: 'blur'}
    ] : []"
        >
          <!-- Cron表达式输入框 -->
          <el-input
            v-model="planForm.schedule_cron_expression"
            placeholder="Cron表达式（秒 分 时 日 月 周 年），例如：0 0 * * * ? 表示每天凌晨执行"
            maxlength="100"
            class="custom-input"
            :disabled="planForm.enable_schedule !== 'true'"
            @change="parseCronToForm"
          />
          <div class="form-tip">
            <el-icon size="14">
              <InfoFilled/>
            </el-icon>
            <span>支持通配符：*（所有）、?（不指定）、-（范围）、,（列举）、/（间隔）</span>
          </div>

          <!-- Cron可视化配置面板（vcrontab风格） -->
          <div v-if="planForm.enable_schedule === 'true'" class="cron-editor-container">
            <!-- 维度切换标签 -->
            <el-tabs v-model="activeTimeDimension" @tab-change="handleDimensionChange">
              <el-tab-pane label="秒" name="second"/>
              <el-tab-pane label="分钟" name="minute"/>
              <el-tab-pane label="小时" name="hour"/>
              <el-tab-pane label="日" name="day"/>
              <el-tab-pane label="月" name="month"/>
              <el-tab-pane label="周" name="dayOfWeek"/>
            </el-tabs>

            <!-- 配置区域 -->
            <div class="cron-config-area">
              <div class="config-desc">正在配置{{
                  dimensionLabels[activeTimeDimension]
                }}的执行规则：
              </div>

              <!-- 规则类型选择 -->
              <el-radio-group
                v-model="cronForm[activeTimeDimension].type"
                @change="handleRuleTypeChange"
                class="rule-type-group"
              >
                <el-radio label="all" value="all">所有值(*)</el-radio>
                <el-radio label="range" value="range">范围执行(a-b)</el-radio>
                <el-radio
                  label="interval"
                  value="interval"
                  v-if="activeTimeDimension !== 'dayOfWeek'">
                  间隔执行(a/b)
                </el-radio>
                <el-radio label="specific" value="specific">指定值(a,b,c)</el-radio>
              </el-radio-group>


              <!-- 范围执行配置 -->
              <div v-if="cronForm[activeTimeDimension].type === 'range'" class="config-fields">
                <el-form-item
                  :label="activeTimeDimension === 'dayOfWeek' ? '从' : '从'"
                  size="small">
                  <el-select
                    v-if="activeTimeDimension === 'dayOfWeek'"
                    v-model="cronForm[activeTimeDimension].rangeStart"
                    @change="updateCronExpression" style="width: 90px">
                    <el-option
                      v-for="option in getDimensionOptions(activeTimeDimension)"
                      :key="option.value"
                      :label="numberToWeekDay(parseInt(option.value))"
                      :value="parseInt(option.value)"
                    />
                  </el-select>
                  <el-input-number
                    v-else
                    v-model="cronForm[activeTimeDimension].rangeStart"
                    :min="dimensionRanges[activeTimeDimension].min"
                    :max="dimensionRanges[activeTimeDimension].max"
                    @change="updateCronExpression"
                  />
                </el-form-item>
                <span class="separator">-</span>
                <el-form-item
                  :label="activeTimeDimension === 'dayOfWeek' ? '到' : '到'"
                  size="small">
                  <el-select
                    v-if="activeTimeDimension === 'dayOfWeek'"
                    v-model="cronForm[activeTimeDimension].rangeEnd"
                    @change="updateCronExpression" style="width: 90px">
                    <el-option
                      v-for="option in getDimensionOptions(activeTimeDimension)"
                      :key="option.value"
                      :label="numberToWeekDay(parseInt(option.value))"
                      :value="parseInt(option.value)"
                    />
                  </el-select>
                  <el-input-number
                    v-else
                    v-model="cronForm[activeTimeDimension].rangeEnd"
                    :min="dimensionRanges[activeTimeDimension].min"
                    :max="dimensionRanges[activeTimeDimension].max"
                    @change="updateCronExpression"
                  />
                </el-form-item>
                <span class="unit">{{
                    activeTimeDimension === 'dayOfWeek' ?
                      '' : dimensionUnits[activeTimeDimension]
                  }}</span>
              </div>


              <!-- 间隔执行配置 -->
              <div v-if="cronForm[activeTimeDimension].type === 'interval'" class="config-fields">
                <el-form-item label="从" size="small">
                  <el-input-number
                    v-model="cronForm[activeTimeDimension].intervalStart"
                    :min="dimensionRanges[activeTimeDimension].min"
                    :max="dimensionRanges[activeTimeDimension].max"
                    @change="updateCronExpression"
                  />
                </el-form-item>
                <span class="separator">开始，每</span>
                <el-form-item label="间隔" size="small">
                  <el-input-number
                    v-model="cronForm[activeTimeDimension].intervalStep"
                    :min="1"
                    :max="dimensionRanges[activeTimeDimension].max"
                    @change="updateCronExpression"
                  />
                </el-form-item>
                <span class="unit">{{ dimensionUnits[activeTimeDimension] }}执行一次</span>
              </div>

              <!-- 指定值配置 -->
              <div v-if="cronForm[activeTimeDimension].type === 'specific'" class="config-fields">
                <el-select
                  v-if="activeTimeDimension === 'dayOfWeek'"
                  v-model="cronForm[activeTimeDimension].specificValues"
                  multiple
                  placeholder="请选择值"
                  @change="updateCronExpression"
                  style="width: 100%"
                >
                  <el-option
                    v-for="option in getDimensionOptions(activeTimeDimension)"
                    :key="option.value"
                    :label="numberToWeekDay(parseInt(option.value))"
                    :value="parseInt(option.value)"
                  />
                </el-select>
                <el-select
                  v-else
                  v-model="cronForm[activeTimeDimension].specificValues"
                  multiple
                  placeholder="请选择值"
                  @change="updateCronExpression"
                  style="width: 100%"
                >
                  <el-option
                    v-for="option in getDimensionOptions(activeTimeDimension)"
                    :key="option.value"
                    :label="parseInt(option.value)"
                    :value="parseInt(option.value)"
                  />
                </el-select>
              </div>

              <!-- 所有值/不指定 说明 -->
              <div v-if="['all', 'none'].includes(cronForm[activeTimeDimension].type)"
                   class="config-desc">注意：
                {{
                  cronForm[activeTimeDimension].type === 'all' ?
                    (activeTimeDimension === 'second' ? '每秒都会执行' :
                      activeTimeDimension === 'minute' ? '每分钟都会执行' :
                        activeTimeDimension === 'hour' ? '每小时都会执行' :
                          activeTimeDimension === 'day' ? '每天都会执行' :
                            activeTimeDimension === 'month' ? '每月都会执行' :
                              activeTimeDimension === 'dayOfWeek' ? '每周都会执行' : '都会执行') :
                    '不指定具体值（仅用于日和周的互斥场景）'
                }}
              </div>
            </div>

            <!-- 表达式预览 -->
            <div class="cron-preview">
              <div class="preview-label">当前Cron表达式：</div>
              <div class="cron-expression">
                <span
                  v-for="(part, index) in splitCronExpression(planForm.schedule_cron_expression)"
                  :key="index">
                  {{ part || '*' }}
                </span>
              </div>

              <!-- 字段含义对照表 -->
              <div class="cron-fields">
                <div class="field-item" :class="{active: activeTimeDimension === 'second'}">秒</div>
                <div class="field-item" :class="{active: activeTimeDimension === 'minute'}">分</div>
                <div class="field-item" :class="{active: activeTimeDimension === 'hour'}">时</div>
                <div class="field-item" :class="{active: activeTimeDimension === 'day'}">日</div>
                <div class="field-item" :class="{active: activeTimeDimension === 'month'}">月</div>
                <div class="field-item" :class="{active: activeTimeDimension === 'dayOfWeek'}">周
                </div>
              </div>
            </div>

            <!-- 最近执行时间预览 -->
            <div class="execution-preview">
              <div class="preview-label">最近5次执行时间：</div>
              <div v-if="executionTimes.length > 0" class="execution-times">
                <div v-for="(time, index) in executionTimes" :key="index" class="time-item">
                  {{ time }}
                </div>
              </div>
              <div v-else class="no-execution">
                请配置Cron表达式查看执行时间
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- 新增：发送通知开关 -->
        <el-form-item label="发送通知" prop="enable_notification">
          <el-switch
            v-model="planForm.enable_notification"
            active-text="开启"
            inactive-text="关闭"
            active-value="true"
            inactive-value="false"
            @change="handleNotificationSwitchChange"
          />
        </el-form-item>

        <!-- 新增：企微webhook列表 -->
        <el-form-item
          label="企微Webhooks"
          prop="wecom_webhooks">
          <el-input
            v-model="planForm.wecom_webhooks"
            type="textarea"
            :rows="2"
            autosize
            placeholder="请输入企微Webhook地址，多个地址英文逗号分隔"
          />
        </el-form-item>

        <!-- 新增：飞书webhook列表 -->
        <el-form-item label="飞书Webhooks" prop="lark_webhooks">
          <el-input
            v-model="planForm.lark_webhooks"
            type="textarea"
            :rows="2"
            autosize
            placeholder="请输入飞书Webhook地址，多个地址英文逗号分隔"
          />
        </el-form-item>

        <!-- 新增：钉钉webhook列表 -->
        <el-form-item label="钉钉Webhooks" prop="dingtalk_webhooks">
          <el-input
            v-model="planForm.dingtalk_webhooks"
            type="textarea"
            autosize
            placeholder="请输入钉钉Webhook地址，多个地址英文逗号分隔"
          />
        </el-form-item>
      </el-form>
      <div class="dialog-footer">
        <el-button @click="handleDialogClose" class="footer-button cancel-button">取消</el-button>
        <el-button type="primary" @click="submitPlanForm" :loading="submitLoading"
                   class="footer-button confirm-button">
          确定
        </el-button>
      </div>
    </el-dialog>

    <!-- 用例管理抽屉 -->
    <el-drawer
      v-model="caseManagementVisible"
      title="用例管理"
      direction="rtl"
      :size="drawerWidth"
      :with-header="true"
      class="case-management-drawer"
      @open="handleDrawerOpen"
      @close="handleDrawerClose"
      @closed="fetchTestPlanList"
    >
      <div class="drawer-wrapper" @wheel.prevent="handleDrawerWheel">
        <div class="drawer-header">
          <h3>{{ selectedPlan.plan_name || '测试计划' }} - 用例列表</h3>
          <p>管理测试计划中的用例</p>
        </div>

        <!-- 主体内容区域 - 固定高度 -->
        <div class="drawer-main-wrapper">
          <el-tabs v-model="activeTab" class="case-tabs">
            <el-tab-pane label="添加用例" name="add">
              <div class="test-case-selector">
                <div class="selector-header add-header">
                  <div class="selected-count">
                    已选择 {{ selectedCaseUuids.length }} 个用例
                  </div>
                  <div>
                    <el-input
                      v-model="searchKeyword"
                      placeholder="搜索用例名称"
                      clearable
                      size="small"
                      style="width: 200px; margin-right: 10px;"
                      @input="handleSearchCases"
                    />
                    <el-button type="primary" size="small" @click="handleSearchCases"
                               :loading="caseLoading">
                      搜索
                    </el-button>
                    <div class="search-result" v-if="casePagination.total > 0 && searchKeyword">
                      搜索结果: {{ casePagination.total }} 条
                    </div>
                  </div>
                </div>

                <!-- 卡片滚动区域 -->
                <div class="case-scroll-container" @wheel="handleScrollContainerWheel">
                  <div class="case-cards-container">
                    <el-card
                      v-for="item in testCaseList"
                      :key="item.case_uuid"
                      class="case-card"
                      :class="{
                        'case-card-selected': isCaseSelected(item.case_uuid),
                        'case-card-associated': isCaseAssociated(item.case_uuid)
                      }"
                      shadow="hover"
                      @click="handleCardSelect(item)"
                      :disabled="isCaseAssociated(item.case_uuid)"
                    >
                      <div class="case-card-content">
                        <div class="card-header-row">
                          <div class="case-type-tags">
                            <el-tag
                              :type="item.case_type === 'pytest' ? 'primary' : 'success'"
                              size="small"
                            >
                              {{ item.case_type === 'pytest' ? 'Pytest' : 'TestNG' }}
                            </el-tag>
                            <el-tag
                              :type="item.specific_type === 12 ? 'primary' : 'success'"
                              size="small"
                            >
                              {{ getSpecificTypeLabel(item.specific_type) }}
                            </el-tag>
                          </div>
                          <!-- 选中标识 -->
                          <div class="card-select-indicator" v-if="isCaseSelected(item.case_uuid)">
                            <el-icon :size="16" class="selected-icon">
                              <Check/>
                            </el-icon>
                          </div>

                          <!-- 已关联标识 -->
                          <div class="card-associated-indicator"
                               v-if="isCaseAssociated(item.case_uuid)">
                            <el-icon :size="16" class="associated-icon">
                              <Check/>
                            </el-icon>
                            <span class="associated-text">已关联</span>
                          </div>
                        </div>

                        <div class="card-details">
                          <div class="case-name">{{ item.case_name }}</div>
                          <div class="card-footer">
                            <div class="case-author">
                              作者: {{
                                item.case_author?.nickname || item.case_author?.username || '未知'
                              }}
                            </div>
                            <div class="card-actions">
                              <!-- 新增：查看详情按钮 -->
                              <el-button
                                type="primary"
                                size="small"
                                link
                                @click.stop="openCaseDetail(item)"
                              >
                                详情
                              </el-button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </el-card>

                    <div v-if="testCaseList.length === 0 && !caseLoading" class="no-data">
                      <el-empty description="暂无匹配的用例数据"/>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="已关联用例" name="selected">
              <div class="selected-case-selector">
                <!-- 头部操作区 -->
                <div class="selector-header selected-header">
                  <div class="selected-count">
                    已关联 {{ selectedCases.length }} 个用例
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click="handleClearAllCases"
                    :disabled="selectedCases.length === 0 || clearLoading"
                    :loading="clearLoading"
                  >
                    清空已关联用例
                  </el-button>
                </div>

                <!-- 已选用例滚动区域 -->
                <div class="selected-case-scroll" @wheel="handleScrollContainerWheel">
                  <div class="case-cards-container">
                    <el-card
                      v-for="item in selectedCases"
                      :key="item.case_uuid"
                      class="case-card"
                      shadow="hover"
                    >
                      <div class="case-card-content">
                        <div class="card-header-row">
                          <div class="case-type-tags">
                            <el-tag
                              :type="item.case_type === 'pytest' ? 'primary' : 'success'"
                              size="small"
                            >
                              {{ item.case_type === 'pytest' ? 'Pytest' : 'TestNG' }}
                            </el-tag>
                            <el-tag
                              type="info"
                              size="small"
                            >
                              {{ getSpecificTypeLabel(item.specific_type) }}
                            </el-tag>
                          </div>

                          <!-- 已关联标识（与添加用例页保持一致） -->
                          <div class="card-associated-indicator">
                            <el-icon :size="16" class="associated-icon">
                              <Check/>
                            </el-icon>
                            <span class="associated-text">已关联</span>
                          </div>
                        </div>
                        <div class="card-details">
                          <div class="case-name">{{ item.case_name }}</div>
                          <div class="card-footer">
                            <div class="case-author">作者:
                              {{
                                item.case_author?.nickname || item.case_author?.username || '未知'
                              }}
                            </div>
                            <div class="card-actions">
                              <el-button
                                type="danger"
                                size="small"
                                link
                                @click="handleRemoveSelectedCase(item.case_uuid)"
                              >
                                移除
                              </el-button>
                            </div>
                          </div>
                        </div>

                      </div>
                    </el-card>
                    <div v-if="selectedCases.length === 0" class="no-data">
                      <el-empty description="暂无已选用例"/>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="已失效用例" name="invalid">
              <div class="selected-case-selector">
                <!-- 头部操作区 -->
                <div class="selector-header selected-header">
                  <div v-if="invalidCases.length > 0" class="selected-count">{{
                      invalidCases.length
                    }}
                    个用例已失效，可能是用例被删除或者用例脚本被移动/重命名/删除
                  </div>
                  <div v-else class="selected-count">当前测试计划无已失效用例</div>
                  <el-button
                    type="danger"
                    size="small"
                    @click="handleClearInvalidCases"
                    :disabled="invalidCases.length === 0 || clearLoading"
                    :loading="clearLoading"
                  >
                    清空已失效用例
                  </el-button>
                </div>

                <!-- 已选用例滚动区域 -->
                <div class="selected-case-scroll" @wheel="handleScrollContainerWheel">
                  <div class="case-cards-container">
                    <el-card
                      v-for="item in invalidCases"
                      :key="item.case_uuid"
                      class="case-card"
                      shadow="hover"
                    >
                      <div class="case-card-content">
                        <div class="card-header-row">
                          <div class="case-type-tags">
                            <el-tag
                              :type="item.case_type === 'pytest' ? 'primary' : 'success'"
                              size="small"
                            >
                              {{ item.case_type === 'pytest' ? 'Pytest' : 'TestNG' }}
                            </el-tag>
                            <el-tag
                              type="info"
                              size="small"
                            >
                              {{ getSpecificTypeLabel(item.specific_type) }}
                            </el-tag>
                          </div>

                          <!-- 已关联标识（与添加用例页保持一致） -->
                          <div class="card-invalid-indicator">
                            <el-icon :size="16" class="associated-icon">
                              <CloseBold/>
                            </el-icon>
                            <span class="associated-text">已失效</span>
                          </div>
                        </div>
                        <div class="card-details">
                          <div class="case-name">{{ item.case_name }}</div>
                          <div class="card-footer">
                            <div class="case-author">作者:
                              {{
                                item.case_author?.nickname || item.case_author?.username || '未知'
                              }}
                            </div>
                            <div class="card-actions">
                              <el-button
                                type="danger"
                                size="small"
                                link
                                @click="handleRemoveInvalidCase(item.case_uuid)"
                              >
                                移除
                              </el-button>
                            </div>
                          </div>
                        </div>

                      </div>
                    </el-card>
                    <div v-if="selectedCases.length === 0" class="no-data">
                      <el-empty description="暂无已选用例"/>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 底部固定区域 -->
        <div class="drawer-fixed-footer">
          <!-- 仅在"添加用例"标签页显示的内容 -->
          <div v-if="activeTab === 'add'" class="add-tab-footer">
            <div class="footer-content">
              <!-- 分页器居左 -->
              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="casePagination.page_num"
                  v-model:page-size="casePagination.page_size"
                  :page-sizes="[20, 50, 100]"
                  :total="casePagination.total"
                  layout="total, prev, pager, next"
                  @size-change="handleCaseSizeChange"
                  @current-change="handleCaseCurrentChange"
                  size="small"
                  :disabled="casePagination.total === 0"
                />
              </div>

              <!-- 操作按钮居右 -->
              <div class="footer-actions">
                <el-button type="primary" @click="showAddConfirm"
                           :disabled="selectedCaseUuids.length === 0">
                  添加选中用例
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
    <!-- 用例详情抽屉 -->
    <!-- 引入 TestCaseDetailDrawer 组件 -->
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
import {nextTick, onBeforeMount, onMounted, reactive, ref, watch} from 'vue'
import {useRoute} from 'vue-router'
import {CronExpressionParser} from 'cron-parser';
import {ElEmpty, ElMessage, ElMessageBox} from 'element-plus'
import {
  Edit,
  VideoPlay,
  Operation,
  Delete,
  Document,
  User,
  Link,
  PriceTag
} from '@element-plus/icons-vue'
import {Plus, Refresh, Search, Check, InfoFilled, CloseBold} from '@element-plus/icons-vue'
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import java from 'highlight.js/lib/languages/java';
import 'highlight.js/styles/a11y-dark.css';
import TestCaseDetailDrawer from '@/components/TestCaseDetailDrawer.vue'

import {
  createTestPlan,
  deleteTestPlan,
  getTestCaseList,
  getTestPlanDetail,
  getTestPlanList,
  removeTestCaseFromPlan,
  updateTestPlan,
  batchAddTestCaseToPlan,
  clearTestCaseFromPlan,
  triggerTestPlan, clearInvalidTestCaseFromPlan, getTestCaseContentDetail
} from '@/network/api.js'

// 注册语言
hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);

// 路由参数
const route = useRoute()

// 数据状态
const testPlanList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const caseManagementVisible = ref(false)
const activeTab = ref('add')
const selectedPlan = ref({})
const selectedCases = ref([])
const invalidCases = ref([])
const saveLoading = ref(false) // 保存用例加载状态
const clearLoading = ref(false) // 清空用例加载状态
const lastOpenedPlanId = ref(null)
const drawerWidth = ref('80%')

// 用例选择相关
const testCaseList = ref([])
const caseLoading = ref(false)
const searchKeyword = ref('')
const selectedCaseUuids = ref([]) // 存储选中的用例UUID
const casePagination = reactive({
  page_num: 1,
  page_size: 50,
  total: 0
})

const caseDetailVisible = ref(false)
const selectedCase = ref(null)
const selectedCaseContent = ref('')

const submitLoading = ref(false)

// 对话框相关
const planFormRef = ref(null)
const dialogTitle = ref('')

// 搜索表单
const searchForm = reactive({
  plan_name: '',
  creator: ''
})

// 分页参数
const pagination = reactive({
  page_num: 1,
  page_size: 10,
  total: 0
})

// 表单数据
const planForm = reactive({
  test_plan_id: null,
  plan_name: '',
  test_environment: '',
  execution_mode: '',
  description: '',
  // 新增字段
  enable_schedule: 'false', // 定时器状态：true/false
  schedule_cron_expression: '', // Cron表达式
  enable_notification: 'false', // 发送通知开关
  wecom_webhooks: '', // 企微webhook列表（换行分隔）
  lark_webhooks: '', // 飞书webhook列表
  dingtalk_webhooks: '' // 钉钉webhook列表
})

// 表单验证规则
const planFormRules = {
  plan_name: [
    {required: true, message: '请输入计划名称', trigger: 'blur'},
    {max: 50, message: '计划名称最多50个字符', trigger: 'blur'}
  ],
  test_environment: [
    {required: true, message: '请选择测试环境', trigger: 'change'}
  ],
  execution_mode: [
    {required: true, message: '请选择执行方式', trigger: 'change'}
  ],
  enable_schedule: [
    {required: true, message: '请选择定时器状态', trigger: 'change'}
  ],
  enable_notification: [
    {required: true, message: '请选择是否发送通知', trigger: 'change'}
  ]
}


// 维度配置常量
const dimensionLabels = {
  second: '秒',
  minute: '分钟',
  hour: '小时',
  day: '日',
  month: '月',
  dayOfWeek: '周'
};

// 2. 移除dimensionUnits中的年
const dimensionUnits = {
  second: '秒',
  minute: '分钟',
  hour: '小时',
  day: '天',
  month: '月',
  dayOfWeek: '周'
};

// 各维度取值范围
const dimensionRanges = {
  second: {min: 0, max: 59},
  minute: {min: 0, max: 59},
  hour: {min: 0, max: 23},
  day: {min: 1, max: 31},
  month: {min: 1, max: 12},
  dayOfWeek: {min: 0, max: 6} // 0=周一，1=周二，2=周三，3=周四，4=周五，5=周六，6=周日
};

// Cron表单配置（对应vcrontab的配置模式）
const cronForm = reactive({
  second: {
    type: 'all', // all, range, interval, specific, none
    rangeStart: 0,
    rangeEnd: 59,
    intervalStart: 0,
    intervalStep: 1,
    specificValues: []
  },
  minute: {
    type: 'all',
    rangeStart: 0,
    rangeEnd: 59,
    intervalStart: 0,
    intervalStep: 1,
    specificValues: []
  },
  hour: {
    type: 'all',
    rangeStart: 0,
    rangeEnd: 23,
    intervalStart: 0,
    intervalStep: 1,
    specificValues: []
  },
  day: {
    type: 'all',
    rangeStart: 1,
    rangeEnd: 31,
    intervalStart: 1,
    intervalStep: 1,
    specificValues: []
  },
  month: {
    type: 'all',
    rangeStart: 1,
    rangeEnd: 12,
    intervalStart: 1,
    intervalStep: 1,
    specificValues: []
  },
  dayOfWeek: {
    type: 'none', // 周默认不指定（与日互斥）
    rangeStart: 0,
    rangeEnd: 6,
    intervalStart: 0,
    intervalStep: 1,
    specificValues: []
  }
});

// 活跃的时间维度
const activeTimeDimension = ref('minute');

// 执行时间预览
const executionTimes = ref([]);

// 获取维度选项（如月份1-12，周0-6对应周日到周六）
const getDimensionOptions = (dimension) => {
  const options = [];
  const {min, max} = dimensionRanges[dimension];

  if (dimension === 'dayOfWeek') {
    // 按照你提供的映射：0=周一, 1=周二, 2=周三, 3=周四, 4=周五, 5=周六, 6=周日
    const weekLabels = ['周一(0)', '周二(1)', '周三(2)', '周四(3)', '周五(4)', '周六(5)', '周日(6)'];
    for (let i = min; i <= max; i++) {
      options.push({value: i.toString(), label: weekLabels[i]});
    }
  } else if (dimension === 'month') {
    const monthLabels = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    for (let i = min; i <= max; i++) {
      options.push({value: i.toString(), label: `${i}(${monthLabels[i - 1]})`});
    }
  } else {
    for (let i = min; i <= max; i++) {
      options.push({value: i.toString(), label: i.toString()});
    }
  }
  return options;
};


// 数字到中文星期的映射
const numberToWeekDay = (num) => {
  const weekDays = ['周一(0)', '周二(1)', '周三(2)', '周四(3)', '周五(4)', '周六(5)', '周日(6)'];
  return weekDays[num] || '';
};

// 维度切换处理
const handleDimensionChange = (dimension) => {
  // 日和周互斥提示和自动设置
  if (dimension === 'day' && cronForm.dayOfWeek.type !== 'all') {
    // 切换到日时，自动将周设为不指定
    cronForm.dayOfWeek.type = 'all';
    ElMessage.warning({
      message: '日和周不能同时指定，已将周设置为"所有值"',
      duration: 8000 // 8秒
    });
    // 更新Cron表达式
    updateCronExpression();
  }
  if (dimension === 'dayOfWeek' && cronForm.day.type !== 'all') {
    // 切换到周时，自动将日设为不指定
    cronForm.day.type = 'all';
    ElMessage.warning({
      message: '周和日不能同时指定，已将日设置为"所有值"',
      duration: 8000 // 8秒
    });
    // 更新Cron表达式
    updateCronExpression();
  }
};


// 规则类型变更处理
const handleRuleTypeChange = () => {
  updateCronExpression();
};

// 解析Cron表达式到表单
const parseCronToForm = () => {
  if (!planForm.schedule_cron_expression) return;

  const cronParts = planForm.schedule_cron_expression.trim().split(/\s+/);
  // 兼容6位（秒分时空日月周）和5位（分时空日月周）
  const parts = cronParts.length === 6
    ? cronParts
    : ['0', ...cronParts]; // 5位时补全秒为0

  // 对应顺序：秒 分 时 日 月 周
  const dimensionsOrder = ['second', 'minute', 'hour', 'day', 'month', 'dayOfWeek'];

  parts.forEach((part, index) => {
    const dimension = dimensionsOrder[index];
    if (!dimension) return;

    if (part === '*') {
      cronForm[dimension].type = 'all';
    } else if (part === '?') {
      cronForm[dimension].type = 'none';
    } else if (part.includes('-')) {
      const [start, end] = part.split('-');

      // 如果是周字段，需要根据映射进行转换
      if (dimension === 'dayOfWeek') {
        let s = parseInt(start);
        let e = parseInt(end);


        cronForm[dimension].type = 'range';
        cronForm[dimension].rangeStart = s;
        cronForm[dimension].rangeEnd = e;
      } else {
        cronForm[dimension].type = 'range';
        cronForm[dimension].rangeStart = parseInt(start);
        cronForm[dimension].rangeEnd = parseInt(end);
      }
    } else if (part.includes('/')) {
      const [start, step] = part.split('/');

      // 如果是周字段，需要根据映射进行转换
      if (dimension === 'dayOfWeek') {
        let s = start === '*' ? dimensionRanges[dimension].min : parseInt(start);

        // 转换逻辑
        if (s === 0) s = 6; // 周日转为6
        else s = s - 1;      // 其他天减1

        cronForm[dimension].type = 'interval';
        cronForm[dimension].intervalStart = s;
        cronForm[dimension].intervalStep = parseInt(step);
      } else {
        cronForm[dimension].type = 'interval';
        cronForm[dimension].intervalStart = start === '*' ? dimensionRanges[dimension].min : parseInt(start);
        cronForm[dimension].intervalStep = parseInt(step);
      }
    } else if (part.includes(',')) {
      // 处理逗号分隔的多个值
      let values = part.split(',').map(v => parseInt(v));

      cronForm[dimension].type = 'specific';
      cronForm[dimension].specificValues = values;
    } else {
      // 单个值视为指定值
      let value = parseInt(part);

      cronForm[dimension].type = 'specific';
      cronForm[dimension].specificValues = [value];
    }
  });

  // 更新执行时间预览
  updateExecutionTimes();
};


// 根据表单生成Cron表达式
const updateCronExpression = () => {
  // 只处理6个维度：秒 分 时 日 月 周
  const dimensions = ['second', 'minute', 'hour', 'day', 'month', 'dayOfWeek'];
  const parts = dimensions.map(dimension => {
    const config = cronForm[dimension];

    switch (config.type) {
      case 'all':
        return '*';
      case 'none':
        return '?';
      case 'range':
        return `${config.rangeStart}-${config.rangeEnd}`;
      case 'interval':
        return `${config.intervalStart}/${config.intervalStep}`;
      case 'specific':
        return config.specificValues.join(',');
      default:
        return '*';
    }
  });

  planForm.schedule_cron_expression = parts.join(' ');

  // 更新执行时间预览
  updateExecutionTimes();
};

// 生成最近执行时间预览（模拟计算）
const updateExecutionTimes = () => {
  executionTimes.value = [];
  if (!planForm.schedule_cron_expression) return;

  try {
    console.log('Cron表达式:', planForm.schedule_cron_expression);
    // 将Cron表达式中的星期字段转换为标准格式（0=周日, 1=周一, ..., 6=周六）
    const cronParts = planForm.schedule_cron_expression.trim().split(/\s+/);

    // 如果是5位格式，扩展为6位
    let parts = cronParts.length === 6 ? [...cronParts] : ['0', ...cronParts];

    // 处理星期字段（第6位，索引为5）
    if (parts.length >= 6) {
      let dayOfWeekPart = parts[5];

      // 处理不同格式的星期字段
      if (dayOfWeekPart.includes(',')) {
        // 多个值：0,1,2 -> 转换为标准格式
        const values = dayOfWeekPart.split(',').map(v => {
          const num = parseInt(v);
          // 你的映射：0=周一, 1=周二, ..., 6=周日
          // 标准映射：0=周日, 1=周一, ..., 6=周六
          // 转换逻辑：(num + 1) % 7
          return (num + 1) % 7;
        });
        parts[5] = values.join(',');
      } else if (dayOfWeekPart.includes('-')) {
        // 范围：4-6 -> 转换为标准格式
        const [start, end] = dayOfWeekPart.split('-').map(v => parseInt(v));
        // 转换为标准格式
        const stdStart = (start + 1) % 7;
        const stdEnd = (end + 1) % 7;
        // 处理跨越周日的情况：当原始范围跨越周日时（如6-0表示周六到周日）
        if (start > end) {
          // 原始范围跨越周日，需要转换为离散值列表
          const days = [];
          for (let i = start; i <= 6; i++) {
            days.push((i + 1) % 7);
          }
          for (let i = 0; i <= end; i++) {
            days.push((i + 1) % 7);
          }
          parts[5] = days.join(',');
        } else if (stdStart <= stdEnd) {
          parts[5] = `${stdStart}-${stdEnd}`;
        } else {
          // 其他跨越情况也转换为离散值
          const days = [];
          for (let i = start; i <= end; i++) {
            days.push((i + 1) % 7);
          }
          parts[5] = days.join(',');
        }
      } else if (dayOfWeekPart.includes('/')) {
        // 间隔：暂时保持不变，但需要注意转换
        const [base, interval] = dayOfWeekPart.split('/');
        if (base !== '*') {
          const baseNum = base === '?' ? '?' : (parseInt(base) + 1) % 7;
          parts[5] = `${baseNum}/${interval}`;
        }
      } else if (dayOfWeekPart !== '*' && dayOfWeekPart !== '?') {
        // 单个值：4 -> 转换为标准格式
        const num = parseInt(dayOfWeekPart);
        parts[5] = ((num + 1) % 7).toString();
      }
    }

    const standardCronExpression = parts.join(' ');

    // 使用标准格式的Cron表达式进行解析
    const interval = CronExpressionParser.parse(standardCronExpression, {
      currentDate: new Date(),
      tz: 'Asia/Shanghai' // 设置为上海时区
    });

    // 获取最近5次执行时间
    for (let i = 0; i < 5; i++) {
      const next = interval.next();
      const date = next.toDate();

      // 获取星期几（0=周日, 1=周一, ..., 6=周六）
      let jsDayOfWeek = date.getDay(); // JavaScript默认的getDay()返回0-6 (周日到周六)

      // 将JavaScript的星期映射转换为你的应用标准显示
      // JavaScript: 0=周日, 1=周一, 2=周二, 3=周三, 4=周四, 5=周五, 6=周六
      // 你的应用: 0=周一, 1=周二, 2=周三, 3=周四, 4=周五, 5=周六, 6=周日
      let appDayOfWeek;
      if (jsDayOfWeek === 0) {
        appDayOfWeek = 6; // 周日对应你的应用的6
      } else {
        appDayOfWeek = jsDayOfWeek - 1; // 其他天减1
      }

      // 对应中文星期显示
      const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
      const dayName = weekDays[appDayOfWeek];

      executionTimes.value.push(
        date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          timeZone: 'Asia/Shanghai'
        }) + ` (${dayName})`
      );
    }
  } catch (error) {
    console.error('解析Cron表达式失败:', error);
    executionTimes.value = ['Cron表达式格式错误'];
  }
};


// 初始化Cron表单
const initCronForm = () => {
  console.log('初始化Cron表单');
  // 只有在没有 cron 表达式时才初始化默认值
  if (!planForm.schedule_cron_expression) {
    // 设置默认值为每小时一次
    planForm.schedule_cron_expression = '0 0 * * * ?';

    // 解析默认表达式到表单配置
    parseCronToForm();
  }
};

// 监听定时开关，初始化表单
watch(() => planForm.enable_schedule, (val) => {
  if (val === 'true' && !planForm.schedule_cron_expression) {
    initCronForm();
  }
});

// Cron表达式验证（保持原逻辑）
const validateCronExpression = (rule, value, callback) => {
  if (!value) {
    callback();
    return;
  }

  // 通用匹配单个时间字段的正则
  const fieldPattern = (min, max) => {
    const numRange = `(${min}-${max})`;
    const singleNum = `(${min}|[1-9]\\d?|${max})(?![0-9])`;
    const multiNum = `(${singleNum}(,${singleNum})*)`;
    const range = `(${singleNum}-${singleNum})`;
    const interval = `(\\*|${singleNum})\\/(${singleNum})`;
    const none = '\\?';
    return `(\\*|${none}|${multiNum}|${range}|${interval})`;
  };

  // 6位格式：秒 分 时 日 月 周
  const cron6Pattern = new RegExp(`^${fieldPattern(0, 59)}\\s+` + // 秒
    `${fieldPattern(0, 59)}\\s+` + // 分
    `${fieldPattern(0, 23)}\\s+` + // 时
    `${fieldPattern(1, 31)}\\s+` + // 日（支持 ?）
    `${fieldPattern(1, 12)}\\s+` + // 月
    `${fieldPattern(0, 6)}$`); // 周（支持 ?）

  // 5位格式：分 时 日 月 周
  const cron5Pattern = new RegExp(`^${fieldPattern(0, 59)}\\s+` + // 分
    `${fieldPattern(0, 23)}\\s+` + // 时
    `${fieldPattern(1, 31)}\\s+` + // 日（支持 ?）
    `${fieldPattern(1, 12)}\\s+` + // 月
    `${fieldPattern(0, 6)}$`); // 周（支持 ?）

  // 测试表达式
  if (cron6Pattern.test(value.trim()) || cron5Pattern.test(value.trim())) {
    callback();
  } else {
    callback(new Error('Cron表达式格式错误，支持 秒? 分 时 日 月 周 格式'));
  }
};
// 初始化调用
initCronForm();


// 修复滚动问题：保存原始body样式
const originalBodyStyle = ref({})

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

  // 清理监听
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

// 组件挂载时获取数据（确保初始化加载）
onMounted(() => {
  // 确保路由参数存在后再请求
  nextTick(() => {
    fetchTestPlanList()
  })
})

// 抽屉打开时处理：禁止页面滚动 + 设置滚动容器高度
const handleDrawerOpen = () => {
  // 保存原始body样式
  originalBodyStyle.value.overflow = document.body.style.overflow
  originalBodyStyle.value.position = document.body.style.position
  originalBodyStyle.value.height = document.body.style.height

  // 禁止body滚动
  document.body.style.overflow = 'hidden'
  document.body.style.position = 'fixed'
  document.body.style.height = '100vh'
  document.body.style.width = '100%'

  // 延迟设置滚动容器高度，确保DOM已渲染
  setTimeout(() => {
    setScrollContainerHeight()
  }, 100)
}

// 抽屉关闭时处理：恢复页面滚动
const handleDrawerClose = () => {
  // 恢复原始body样式
  document.body.style.overflow = originalBodyStyle.value.overflow || ''
  document.body.style.position = originalBodyStyle.value.position || ''
  document.body.style.height = originalBodyStyle.value.height || ''
  document.body.style.width = ''
}

// 监听窗口大小变化，重新设置滚动容器高度
onMounted(() => {
  window.addEventListener('resize', () => {
    if (caseManagementVisible.value) {
      setScrollContainerHeight()
    }
  })
})

// 监听标签页切换，重新设置滚动容器高度
watch(activeTab, () => {
  if (caseManagementVisible.value) {
    setTimeout(() => {
      setScrollContainerHeight()
    }, 50)
  }
})

// 关键修复：设置滚动容器高度
const setScrollContainerHeight = () => {
  const drawerWrapper = document.querySelector('.drawer-wrapper')
  const drawerHeader = document.querySelector('.drawer-header')
  const drawerFooter = document.querySelector('.drawer-fixed-footer')
  const selectorHeader = document.querySelector(`.${activeTab.value === 'add' ? 'test-case-selector' : 'selected-case-selector'} .${activeTab.value === 'add' ? 'selector-header' : 'selected-header'}`)

  if (!drawerWrapper || !drawerHeader || !drawerFooter || !selectorHeader) return

  // 计算可用高度 = 抽屉总高度 - 头部高度 - 底部高度 - 选择器头部高度 - 内边距
  const drawerHeight = drawerWrapper.offsetHeight
  const headerHeight = drawerHeader.offsetHeight
  const footerHeight = drawerFooter.offsetHeight
  const selectorHeaderHeight = selectorHeader.offsetHeight
  const padding = 40 // 上下内边距总和

  const scrollHeight = drawerHeight - headerHeight - footerHeight - selectorHeaderHeight - padding

  // 设置两个滚动容器的高度
  const addScrollContainer = document.querySelector('.case-scroll-container')
  const selectedScrollContainer = document.querySelector('.selected-case-scroll')

  if (addScrollContainer) {
    addScrollContainer.style.height = `${scrollHeight}px`
  }
  if (selectedScrollContainer) {
    selectedScrollContainer.style.height = `${scrollHeight}px`
  }
}

// 处理抽屉滚动：阻止冒泡到body
const handleDrawerWheel = (e) => {
  e.stopPropagation()
}

// 处理滚动容器滚动：确保只在容器内滚动
const handleScrollContainerWheel = (e) => {
  const container = e.currentTarget
  // 阻止冒泡
  e.stopPropagation()

  // 处理滚动边界，避免滚动不流畅
  const isAtTop = container.scrollTop === 0 && e.deltaY < 0
  const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 1 && e.deltaY > 0

  // 如果已经到达边界，阻止默认行为
  if (isAtTop || isAtBottom) {
    e.preventDefault()
  }
}

// 检查用例是否已关联（核心优化：区分选中和已关联状态）
const isCaseAssociated = (caseUuid) => {
  return selectedCases.value.some(item => item.case_uuid === caseUuid)
}

// 检查用例是否被选中（待添加状态）
const isCaseSelected = (caseUuid) => {
  // 已关联的用例不显示选中状态
  if (isCaseAssociated(caseUuid)) return false
  return selectedCaseUuids.value.some(item => item.case_uuid === caseUuid)
}

// 获取测试计划列表（优化参数处理和错误提示）
const fetchTestPlanList = async () => {
  loading.value = true
  try {
    const params = {
      workspace_id: route.params.id,
      page_num: pagination.page_num,
      page_size: pagination.page_size,
      plan_name: searchForm.plan_name.trim(),
      creator: searchForm.creator.trim()
    }

    // 过滤空参数
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await getTestPlanList(params)

    if (res.code === 0) {
      testPlanList.value = res.data.test_plans || []
      pagination.total = res.data.total || 0
    } else {
      testPlanList.value = []
      pagination.total = 0
      ElMessage.error(res.message || '获取测试计划列表失败')
    }
  } catch (error) {
    console.error('获取测试计划列表异常:', error)
    testPlanList.value = []
    pagination.total = 0
    ElMessage.error('获取测试计划列表失败，请刷新页面重试')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page_num = 1
  fetchTestPlanList()
}

// 重置搜索条件
const handleReset = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = ''
  })
  pagination.page_num = 1
  fetchTestPlanList()
}

// 分页大小改变
const handleSizeChange = (val) => {
  pagination.page_size = val
  pagination.page_num = 1
  fetchTestPlanList()
}

// 当前页改变
const handleCurrentChange = (val) => {
  pagination.page_num = val
  fetchTestPlanList()
}

// 创建测试计划
const handleCreate = () => {
  dialogTitle.value = '新建测试计划'
  resetPlanForm()
  dialogVisible.value = true
}

// 分割Cron表达式为6个部分
const splitCronExpression = (expression) => {
  if (!expression) {
    return ['', '', '', '', '', ''];
  }

  // 分割表达式并确保有6个部分
  const parts = expression.split(/\s+/);
  // 补全或截取到6个部分
  while (parts.length < 6) {
    parts.push('*');
  }
  return parts.slice(0, 6);
};

// 编辑测试计划（确保数据正确赋值）
const handleEdit = (row) => {
  if (!row || !row.test_plan_id) {
    ElMessage.warning('测试计划数据无效')
    return
  }
  dialogTitle.value = `编辑测试计划：${row.plan_name}`
  planForm.test_plan_id = row.test_plan_id
  planForm.plan_name = row.plan_name || ''
  planForm.test_environment = row.test_environment || ''
  planForm.execution_mode = row.execution_mode || ''
  planForm.description = row.description || ''

  // 新增字段赋值
  planForm.enable_schedule = row.enable_schedule ? 'true' : 'false'
  planForm.schedule_cron_expression = row.schedule_cron_expression || ''
  planForm.enable_notification = row.enable_notification ? 'true' : 'false'
  planForm.wecom_webhooks = row.wecom_webhooks ? (Array.isArray(row.wecom_webhooks) ? row.wecom_webhooks.join('\n') : row.wecom_webhooks) : ''
  planForm.lark_webhooks = row.lark_webhooks ? (Array.isArray(row.lark_webhooks) ? row.lark_webhooks.join('\n') : row.lark_webhooks) : ''
  planForm.dingtalk_webhooks = row.dingtalk_webhooks ? (Array.isArray(row.dingtalk_webhooks) ? row.dingtalk_webhooks.join('\n') : row.dingtalk_webhooks) : ''

  // 如果有 cron 表达式，则解析到表单
  if (row.schedule_cron_expression) {
    nextTick(() => {
      parseCronToForm()
    })
  }

  dialogVisible.value = true
}

// // 定时器开关变化处理
// const handleScheduleSwitchChange = (val) => {
//   // 关闭定时时清空Cron表达式
//   if (val === 'false') {
//     planForm.schedule_cron_expression = ''
//     // 重置表单验证
//     if (planFormRef.value) {
//       planFormRef.value.clearValidate('schedule_cron_expression')
//     }
//   } else {
//     console.log('开启定时器')
//     console.log('Cron表达式:', planForm.schedule_cron_expression)
//     // 开启定时器时，如果有表达式则解析，否则初始化
//     if (planForm.schedule_cron_expression) {
//       parseCronToForm()
//     } else {
//       initCronForm()
//     }
//   }
// }


// 通知开关变化处理
const handleNotificationSwitchChange = (val) => {
  // 关闭通知时清空所有webhook
  if (val === 'false') {
    planForm.wecom_webhooks = ''
    planForm.lark_webhooks = ''
    planForm.dingtalk_webhooks = ''
    // 重置表单验证
    if (planFormRef.value) {
      planFormRef.value.clearValidate('wecom_webhooks')
      planFormRef.value.clearValidate('lark_webhooks')
      planFormRef.value.clearValidate('dingtalk_webhooks')
    }
  }
}

// 删除测试计划
const handleDelete = (row) => {
  if (!row || !row.test_plan_id) {
    ElMessage.warning('测试计划数据无效')
    return
  }

  ElMessageBox.confirm(
    `确定要删除测试计划 "${row.plan_name}" 吗？删除后不可恢复`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const res = await deleteTestPlan({test_plan_id: row.test_plan_id})
      if (res.code === 0) {
        ElMessage.success('删除成功')
        fetchTestPlanList()
      } else {
        ElMessage.error(res.message || '删除失败')
      }
    } catch (error) {
      console.error('删除测试计划异常:', error)
      ElMessage.error('删除失败，请重试')
    }
  }).catch(() => {
    // 用户取消删除
  })
}


// 执行测试计划
const handleTrigger = async (row) => {
  // 增加二次确认弹窗
  try {
    await ElMessageBox.confirm(
      `确定要执行测试计划 "${row.plan_name}" 吗？`,
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        center: true
      }
    );
  } catch {
    // 用户取消执行
    return;
  }

  // 用户确认后执行原有逻辑
  try {
    const res = await triggerTestPlan({test_plan_id: row.test_plan_id});
    if (res.code === 0) {
      ElMessage.success('测试任务触发成功');
    } else {
      ElMessage.error(res.message || '测试任务触发失败');
    }
  } catch (error) {
    console.error('测试计划触发异常:', error);
    ElMessage.error('测试任务触发异常，请重试');
  }
};


// 提交表单（优化验证和错误处理）
const submitPlanForm = () => {
  if (!planFormRef.value) return

  planFormRef.value.validate(async (valid) => {
    if (!valid) return

    // 处理webhook数据：将换行分隔的字符串转为数组
    const submitForm = {
      ...planForm,
      workspace_id: route.params.id,
      enable_schedule: planForm.enable_schedule === 'true',
      enable_notification: planForm.enable_notification === 'true',
      wecom_webhooks: planForm.wecom_webhooks ? planForm.wecom_webhooks.split('\n').filter(item => item.trim()) : [],
      lark_webhooks: planForm.lark_webhooks ? planForm.lark_webhooks.split('\n').filter(item => item.trim()) : [],
      dingtalk_webhooks: planForm.dingtalk_webhooks ? planForm.dingtalk_webhooks.split('\n').filter(item => item.trim()) : []
    }

    try {
      submitLoading.value = true
      let res
      if (submitForm.test_plan_id) {
        console.log('更新测试计划:', submitForm)
        // 更新
        res = await updateTestPlan(submitForm)
      } else {
        // 创建
        res = await createTestPlan(submitForm)
      }

      if (res.code === 0) {
        ElMessage.success(submitForm.test_plan_id ? '更新成功' : '创建成功')
        dialogVisible.value = false
        fetchTestPlanList()
      } else {
        ElMessage.error(res.message || (submitForm.test_plan_id ? '更新失败' : '创建失败'))
      }
    } catch (error) {
      console.error(`${planForm.test_plan_id ? '更新' : '创建'}测试计划异常:`, error)
      ElMessage.error(`${planForm.test_plan_id ? '更新' : '创建'}失败，请重试`)
    } finally {
      submitLoading.value = false
    }
  })
}

// 重置表单
const resetPlanForm = () => {
  planForm.test_plan_id = null
  planForm.plan_name = ''
  planForm.test_environment = ''
  planForm.execution_mode = ''
  planForm.description = ''
  // 重置新增字段
  planForm.enable_schedule = 'false'
  planForm.schedule_cron_expression = ''
  planForm.enable_notification = 'false'
  planForm.wecom_webhooks = ''
  planForm.lark_webhooks = ''
  planForm.dingtalk_webhooks = ''

  if (planFormRef.value) {
    planFormRef.value.resetFields()
  }
}

// 关闭对话框
const handleDialogClose = () => {
  dialogVisible.value = false
  resetPlanForm()
}

// 查看用例（优化数据加载顺序）
const handleViewCases = async (row) => {
  if (!row || !row.test_plan_id) {
    ElMessage.warning('测试计划数据无效')
    return
  }

  // 检查是否为同一个测试计划，如果不是则清空已勾选的用例
  if (lastOpenedPlanId.value !== row.test_plan_id) {
    selectedCaseUuids.value = []
    lastOpenedPlanId.value = row.test_plan_id
  }

  selectedPlan.value = {...row} // 深拷贝，避免原数据污染
  caseManagementVisible.value = true

  // 先加载已选数据，再加载可选数据
  try {
    await Promise.all([
      fetchSelectedCases(),
      fetchTestCaseList()
    ])

    // 数据加载完成后设置滚动高度
    setTimeout(() => {
      setScrollContainerHeight()
    }, 100)
  } catch (error) {
    console.error('加载用例数据异常:', error)
    ElMessage.error('加载用例数据失败，请重试')
  }
}

// 获取已选测试用例列表
const fetchSelectedCases = async () => {
  try {
    const res = await getTestPlanDetail(selectedPlan.value.test_plan_id)
    if (res.code === 0) {
      // 确保数据格式正确
      selectedCases.value = Array.isArray(res.data.associated_test_cases) ? res.data.associated_test_cases : [];
      invalidCases.value = Array.isArray(res.data.invalid_test_cases) ? res.data.invalid_test_cases : [];
    } else {
      selectedCases.value = []
      invalidCases.value = []
      ElMessage.error(res.message || '获取已选用例列表失败')
    }
  } catch (error) {
    console.error('获取已选用例列表异常:', error)
    selectedCases.value = []
    invalidCases.value = []
    ElMessage.error('获取已选用例列表失败，请重试')
  }
}

// 获取测试用例列表（优化分页和搜索）
const fetchTestCaseList = async () => {
  caseLoading.value = true
  try {
    // 确保workspace_id存在
    if (!route.params.id) {
      throw new Error('缺少工作空间ID')
    }

    const params = {
      workspace_id: route.params.id,
      case_name: searchKeyword.value.trim(),
      page_num: casePagination.page_num,
      page_size: casePagination.page_size
    }

    const res = await getTestCaseList(params)

    if (res.code === 0) {
      testCaseList.value = res.data.items || []
      casePagination.total = res.data.total || 0
    } else {
      testCaseList.value = []
      casePagination.total = 0
      ElMessage.error(res.message || '获取测试用例列表失败')
    }
  } catch (error) {
    console.error('获取测试用例列表异常:', error)
    testCaseList.value = []
    casePagination.total = 0
    ElMessage.error(error.message || '获取测试用例列表失败，请重试')
  } finally {
    caseLoading.value = false
  }
}

// 搜索用例
const handleSearchCases = () => {
  casePagination.page_num = 1
  fetchTestCaseList()
}

// 获取特定类型标签文本
const getSpecificTypeLabel = (type) => {
  const typeMap = {
    10: 'web',
    11: 'H5',
    12: '接口'
  }
  return typeMap[type] || '未知'
}

// 点击卡片选中/取消选中（优化：已关联用例不可选中）
const handleCardSelect = (item) => {
  const uuid = item.case_uuid

  // 如果是已关联用例，直接返回
  if (isCaseAssociated(uuid)) {
    ElMessage.warning('该用例已关联，无需重复选择')
    return
  }

  // 已选中则移除，未选中则添加
  if (selectedCaseUuids.value.some(c => c.case_uuid === uuid)) {
    selectedCaseUuids.value = selectedCaseUuids.value.filter(c => c.case_uuid !== uuid)
  } else {
    selectedCaseUuids.value.push({
      case_uuid: uuid,
      case_type: item.case_type
    })
  }
}

// 新增：添加选中用例确认弹窗
const showAddConfirm = () => {
  if (selectedCaseUuids.value.length === 0) {
    ElMessage.warning('请选择要添加的用例')
    return
  }

  ElMessageBox.confirm(
    `确定要添加选中的 ${selectedCaseUuids.value.length} 个用例到测试计划吗？`,
    '确认添加',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
      center: true // 按钮居中显示
    }
  ).then(() => {
    saveSelectedCases()
  }).catch(() => {
    // 用户取消添加
  })
}


// 移除已选用例
const handleRemoveSelectedCase = async (caseUuid) => {
  if (!caseUuid) return

  // 找到当前用例信息，用于在确认弹窗中显示
  const currentCase = selectedCases.value.find(c => c.case_uuid === caseUuid)
  if (!currentCase) {
    ElMessage.warning('未找到该用例信息')
    return
  }

  // 二次确认弹窗
  try {
    // 显示确认弹窗
    await ElMessageBox.confirm(
      `确定要移除用例「${currentCase.case_name}」吗？`, // 弹窗内容（显示用例名称，更直观）
      '确认移除', // 弹窗标题
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning', // 警告类型，显示黄色图标
        center: true // 按钮居中显示
      }
    )

    // 用户点击"确定"后，执行移除逻辑
    const res = await removeTestCaseFromPlan({
      test_plan_id: selectedPlan.value.test_plan_id,
      case_uuid: caseUuid,
      case_type: currentCase.case_type || 'pytest' // 直接使用找到的用例类型，更可靠
    })

    if (res.code === 0) {
      const index = selectedCases.value.findIndex(c => c.case_uuid === caseUuid)
      if (index !== -1) {
        selectedCases.value.splice(index, 1)
      }
      ElMessage.success('移除成功')
    } else {
      ElMessage.error(res.message || '移除失败')
    }
  } catch (error) {
    // 捕获错误：如果是用户取消（error.type 为 'cancel'），不提示错误
    if (error !== 'cancel') {
      console.error('移除用例异常:', error)
      ElMessage.error('移除失败，请重试')
    }
  }
}

// 移除指定失效用例
const handleRemoveInvalidCase = async (caseUuid) => {
  if (!caseUuid) return

  // 找到当前用例信息，用于在确认弹窗中显示
  const currentCase = invalidCases.value.find(c => c.case_uuid === caseUuid)
  if (!currentCase) {
    ElMessage.warning('未找到该用例信息')
    return
  }

  // 二次确认弹窗
  try {
    // 显示确认弹窗
    await ElMessageBox.confirm(
      `确定要移除失效用例「${currentCase.case_name}」吗？`, // 弹窗内容（显示用例名称，更直观）
      '确认移除', // 弹窗标题
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning', // 警告类型，显示黄色图标
        center: true // 按钮居中显示
      }
    )

    // 用户点击"确定"后，执行移除逻辑
    const res = await removeTestCaseFromPlan({
      test_plan_id: selectedPlan.value.test_plan_id,
      case_uuid: caseUuid,
      case_type: currentCase.case_type || 'pytest' // 直接使用找到的用例类型，更可靠
    })

    if (res.code === 0) {
      const index = invalidCases.value.findIndex(c => c.case_uuid === caseUuid)
      if (index !== -1) {
        invalidCases.value.splice(index, 1)
      }
      ElMessage.success('移除成功')
    } else {
      ElMessage.error(res.message || '移除失败')
    }
  } catch (error) {
    // 捕获错误：如果是用户取消（error.type 为 'cancel'），不提示错误
    if (error !== 'cancel') {
      console.error('移除用例异常:', error)
      ElMessage.error('移除失败，请重试')
    }
  }
}

// 保存已选用例（替换为批量添加接口）
const saveSelectedCases = async () => {
  saveLoading.value = true
  try {
    const testPlanId = selectedPlan.value.test_plan_id
    if (!testPlanId) {
      throw new Error('测试计划ID无效')
    }

    // 获取已存在的用例UUID
    const existingUuids = (await getTestPlanDetail(testPlanId)).data.associated_test_cases?.map(c => c.case_uuid) || []

    // 筛选需要新增的用例（排除已存在的）
    const casesToAdd = selectedCaseUuids.value
      .filter(caseItem => !existingUuids.includes(caseItem.case_uuid))
      .map(caseItem => ({
        case_uuid: caseItem.case_uuid,
        case_type: caseItem.case_type
      }))

    if (casesToAdd.length > 0) {
      // 使用批量添加接口（单次请求替代循环请求）
      const res = await batchAddTestCaseToPlan({
        test_plan_id: testPlanId,
        cases: casesToAdd // 批量接口参数：用例数组
      })

      if (res.code === 0) {
        ElMessage.success(`成功保存 ${casesToAdd.length} 个用例`)
        // selectedCaseUuids置空
        selectedCaseUuids.value = []
      } else {
        ElMessage.error(res.message || '批量添加用例失败')
      }
    } else {
      ElMessage.success('暂无新增用例需要保存')
    }

  } catch (error) {
    console.error('保存用例异常:', error)
    ElMessage.error(error.message || '保存失败，请重试')
  } finally {
    saveLoading.value = false
    fetchSelectedCases()
  }
}

// 新增：清空已关联的所有用例
const handleClearAllCases = async () => {
  if (selectedCases.length === 0) {
    ElMessage.warning('暂无已关联的用例')
    return
  }

  ElMessageBox.confirm(
    '确定要清空所有已关联的用例吗？此操作不可恢复！',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning', // 警告类型，显示黄色图标
      center: true // 按钮居中显示
    }
  ).then(async () => {
    clearLoading.value = true
    try {
      const res = await clearTestCaseFromPlan({
        test_plan_id: selectedPlan.value.test_plan_id
      })

      if (res.code === 0) {
        selectedCases.value = [] // 清空本地已选列表
        ElMessage.success('所有已关联用例已清空')
      } else {
        ElMessage.error(res.message || '清空用例失败')
      }
    } catch (error) {
      console.error('清空用例异常:', error)
      ElMessage.error('清空失败，请重试')
    } finally {
      clearLoading.value = false
    }
  }).catch(() => {
    // 用户取消清空
  })
}

// 新增：清空已关联的所有用例
const handleClearInvalidCases = async () => {
  if (selectedCases.length === 0) {
    ElMessage.warning('暂无已关联的用例')
    return
  }

  ElMessageBox.confirm(
    '确定要清空所有已失效的用例吗？此操作不可恢复！',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning', // 警告类型，显示黄色图标
      center: true // 按钮居中显示
    }
  ).then(async () => {
    clearLoading.value = true
    try {
      const res = await clearInvalidTestCaseFromPlan({
        test_plan_id: selectedPlan.value.test_plan_id
      })

      if (res.code === 0) {
        invalidCases.value = [] // 清空本地已选列表
        ElMessage.success('所有已失效用例已清空')
      } else {
        ElMessage.error(res.message || '清空失效用例失败')
      }
    } catch (error) {
      console.error('清空失效用例异常:', error)
      ElMessage.error('清空失败，请重试')
    } finally {
      clearLoading.value = false
    }
  }).catch(() => {
    // 用户取消清空
  })
}


// 格式化时间（优化兼容性）
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

// 截断描述显示
const truncateDescription = (description, maxLength = 50) => {
  if (!description) return '暂无描述'
  return description.length > maxLength ? description.substring(0, maxLength) + '...' : description
}

// 用例分页大小改变
const handleCaseSizeChange = (val) => {
  casePagination.page_size = val
  casePagination.page_num = 1
  fetchTestCaseList()
}

// 用例当前页改变
const handleCaseCurrentChange = (val) => {
  casePagination.page_num = val
  fetchTestCaseList()
}

// 打开用例详情的方法
const openCaseDetail = async (row) => {
  selectedCase.value = row
  selectedCaseContent.value = '加载中...'
  caseDetailVisible.value = true

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
.test-plan-list-container {
  padding: 10px 10px 0 10px;
  background-color: #f5f7fa;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  box-sizing: border-box;
  overflow: hidden; /* 防止页面本身滚动 */
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

.action-section {
  flex-shrink: 0;
}

.create-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
  border-radius: 12px;
  font-weight: 600;
  height: 42px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.create-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
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
  gap: 12px;
  height: 90%;
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

.test-plan-table {
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

.plan-name-text {
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

.plan-name-text:hover {
  color: #667eea;
  background-color: rgba(102, 126, 234, 0.15);
  transform: translateX(5px);
}

.description-text {
  color: #64748b;
  font-size: 14px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(102, 126, 234, 0.05);
}

.time-text,
.count-text,
.creator-text {
  color: #7f8c8d;
  font-size: 14px;
}

/* 标签样式 */
:deep(.environment-tag),
:deep(.mode-tag) {
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 24px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-weight: 600;
}

:deep(.environment-tag:hover),
:deep(.mode-tag:hover) {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 操作按钮样式 */
.operation-buttons {
  display: flex;
  gap: 1px;
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

/* 对话框样式 */
.plan-form {
  padding: 20px;
}

.dialog-footer {
  padding: 0 20px 20px;
  text-align: right;
}

/* 新增：表单提示文本样式 */
.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 抽屉整体样式 */
.case-management-drawer {
  --el-drawer-bg-color: #f8fafc;
  overflow: hidden !important;
}

:deep(.case-management-drawer .el-drawer__wrapper) {
  overflow: hidden !important;
}

:deep(.case-management-drawer .el-drawer__body) {
  padding: 0 !important;
  height: 100% !important;
  overflow: hidden !important;
}

/* 抽屉内部布局 */
.drawer-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: 0;
  margin: 0;
  overflow: hidden;
  background-color: #f9fafb
}

.drawer-header {
  padding: 15px 20px;
  border-bottom: 1px solid #e2e8f0;
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

:deep(.case-management-drawer .el-drawer__header) {
  margin-bottom: 5px;
}

.drawer-header h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.drawer-header p {
  margin: 0;
  color: #918c8c;
  font-size: 12px;
}

/* 抽屉主体内容 */
.drawer-main-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 0 20px;
  box-sizing: border-box;
}

/* 标签页样式 */
:deep(.case-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.case-tabs .el-tabs__content) {
  flex: 1;
  overflow: hidden !important;
  padding: 0 !important;
}

:deep(.case-tabs .el-tabs__pane) {
  height: 100%;
  overflow: hidden !important;
  display: flex;
  flex-direction: column;
}

/* 抽屉底部固定区域 */
.drawer-fixed-footer {
  padding: 15px 20px;
  border-top: 1px solid #e2e8f0;
  background-color: #f8fafc;
  flex-shrink: 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.02);
}

/* 添加用例标签页底部内容 */
.add-tab-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}


.footer-actions {
  display: flex;
  gap: 10px;
}

.footer-actions .el-button {
  border-radius: 10px;
  font-size: 14px;
  margin-right: 10px;
  transition: all 0.3s ease;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 强化添加按钮样式 */
.footer-actions .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 8px 20px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.footer-actions .el-button--primary:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.footer-actions .el-button--primary:disabled {
  background: linear-gradient(135deg, #a0cfff 0%, #b3d8ff 100%);
  box-shadow: none;
}

/* 用例选择器样式 - 统一样式 */
.test-case-selector,
.selected-case-selector {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.selector-header .el-input {
  flex: 1;
  max-width: 300px;
}

.selector-header {
  padding: 10px 25px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  justify-content: space-between;
  background: white;
  border-radius: 12px;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #ebeef5;
}

/* 卡片滚动容器 */
.case-scroll-container,
.selected-case-scroll {
  flex: none !important;
  overflow-y: auto !important;
  width: 100%;
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #d9d9d9 #f5f5f5;
  padding: 10px;
  border-radius: 12px;
  background: #fafafa;
}

/* 滚动条样式优化 */
.case-scroll-container::-webkit-scrollbar,
.selected-case-scroll::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.case-scroll-container::-webkit-scrollbar-thumb,
.selected-case-scroll::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.case-scroll-container::-webkit-scrollbar-thumb:hover,
.selected-case-scroll::-webkit-scrollbar-thumb:hover {
  background-color: #909399;
}

.case-scroll-container::-webkit-scrollbar-track,
.selected-case-scroll::-webkit-scrollbar-track {
  background-color: #f5f5f5;
  border-radius: 4px;
}

/* 用例卡片容器 - 统一网格布局 */
.case-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 25px;
  width: 100%;
  box-sizing: border-box;
}

/* 卡片基础样式 - 统一大小和样式 */
.case-card {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  overflow: hidden;
  background-color: white;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  cursor: pointer;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  border: 1px solid #ebeef5;
}

/* hover时的增强效果 */
.case-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
  border-color: #667eea;
}

/* 卡片禁用状态（已关联用例） */
:deep(.case-card.is-disabled) {
  cursor: not-allowed;
  opacity: 0.7;
  background: #fafafa;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  padding: 15px 15px 5px 15px;
}

/* 卡片选中样式 */
.case-card-selected {
  border: 2px solid #667eea !important;
  background: rgba(102, 126, 234, 0.1) !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2) !important;
  transform: translateY(-3px);
}

/* 卡片已关联样式（核心优化） */
.case-card-associated {
  border: 2px solid #67c23a !important;
  background: rgba(103, 194, 58, 0.1) !important;
}

/* 卡片内容样式 - 统一内边距和布局 */
.case-card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

/* 选中标识 */
.card-select-indicator {
  position: static;
  right: 12px;
  z-index: 1;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
  margin-left: 8px;
  flex-shrink: 0;
}

/* 已关联标识（统一样式） */
.card-associated-indicator {
  position: static;
  right: 12px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #67c23a;
  color: white;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 13px;
  box-shadow: 0 4px 8px rgba(103, 194, 58, 0.3);
  margin-left: 8px;
  flex-shrink: 0;
}

.card-invalid-indicator {
  position: static;
  right: 12px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #909399;
  color: white;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 13px;
  box-shadow: 0 4px 8px rgba(144, 147, 153, 0.3);
  margin-left: 8px;
  flex-shrink: 0;
}

.associated-text {
  font-size: 13px;
  font-weight: 500;
}

/* 卡片详情区域 - 统一布局 */
.card-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 5px 15px 15px 15px;
}

/* 作者信息与操作按钮容器 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px dashed #e4e7ed;
  margin-top: auto;
}

/* 用例名称样式调整 */
.case-name {
  font-size: 14px;
  font-weight: 600;
  margin: 8px 0 12px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
  flex-grow: 1;
  min-height: 40px;
  height: 40px;
  padding-bottom: 5px;
}

/* 作者信息样式 */
.case-author {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
}

/* 标签容器 - 统一样式 */
.case-type-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 70%;
}

.case-type-tags .el-tag {
  height: 26px;
  line-height: 24px;
  padding: 0 12px;
  font-size: 13px;
  border-radius: 13px;
  font-weight: 500;
}

/* Pytest标签使用蓝色系 */
.case-type-tags .el-tag--primary {
  background-color: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

/* TestNG标签使用绿色系 */
.case-type-tags .el-tag--success {
  background-color: #f0f9eb;
  border-color: #c2e7b0;
  color: #67c23a;
}

/* specific_type标签使用不同的颜色 */
.case-type-tags .el-tag--info:nth-child(2) {
  background-color: #f4f4f5;
  border-color: #d3d4d6;
  color: #909399;
}

/* 状态标识容器：确保图标/文字不换行 */
.card-status-indicators {
  display: flex;
  align-items: center;
  white-space: nowrap;
}

/* 已选卡片操作区 - 统一样式 */
.card-actions {
  display: flex;
  justify-content: flex-end;
  white-space: nowrap;
}

.card-actions .el-button {
  transition: all 0.2s;
  font-size: 13px;
  border-radius: 6px;
  padding: 6px 12px;
  font-weight: 500;
}

/* 无数据状态 */
.no-data {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 0;
  color: #86909c;
}

:deep(.no-data .el-empty__image) {
  width: 120px;
  height: 120px;
  margin-bottom: 20px;
}

:deep(.no-data .el-empty__description) {
  font-size: 15px;
  color: #86909c;
}

:deep(.case-pagination .el-pagination) {
  font-size: 13px;
  width: 100%;
}

/* 分页按钮样式优化 */
:deep(.case-pagination .el-pagination__sizes .el-input .el-input__inner) {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
}

:deep(.case-pagination .el-pager li) {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  margin: 0 3px;
}

:deep(.case-pagination .el-pagination .btn-prev),
:deep(.case-pagination .el-pagination .btn-next) {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
}

/* Go to输入框优化 */
:deep(.case-pagination .el-pagination__jump .el-input .el-input__inner) {
  border-radius: 6px;
  padding: 0 10px;
  width: 60px;
}

:deep(.case-pagination .el-pagination__editor) {
  margin: 0 5px;
}

/* 修复Element Plus抽屉滚动穿透问题 */
:deep(.el-drawer-open .el-drawer__container) {
  overflow: hidden !important;
}

/* 响应式布局优化 */
@media (min-width: 1600px) {
  .case-cards-container {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (min-width: 1200px) and (max-width: 1599px) {
  .case-cards-container {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .case-cards-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 767px) {
  .case-cards-container {
    grid-template-columns: 1fr;
  }

  .test-plan-list-container {
    padding: 10px;
    height: calc(100vh - 50px);
  }

  .page-header {
    padding: 15px;
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
  }

  .drawer-main-wrapper {
    padding: 0 10px;
  }

  .add-tab-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  :deep(.el-table__fixed-right) {
    width: 180px !important;
  }

  .operation-buttons {
    justify-content: flex-start;
  }

  .operation-button {
    padding: 8px;
    margin-bottom: 6px;
  }
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .test-plan-list-container {
    background-color: #1e293b;
  }

  .page-header,
  .filter-container,
  .table-container,
  .pagination-container,
  .case-card,
  .drawer-fixed-footer {
    background-color: #27364b;
    border-color: #334155;
  }

  .case-card-selected {
    background-color: #1e3a8a !important;
  }

  .case-card-associated {
    background-color: #1e3932 !important;
    border-color: #389e0d !important;
  }

  .page-header h1,
  .title-section h1,
  .drawer-header h3,
  .case-name {
    color: #e2e2e2;
  }

  .page-header p,
  .title-section p,
  .drawer-header p,
  .case-author,
  .associated-text {
    color: #a0a0c0;
  }

  .table-row td,
  .plan-name-text,
  .description-text,
  .time-text,
  .count-text,
  .creator-text {
    color: #e2e8f0;
  }

  :deep(.no-data .el-empty__text),
  :deep(.no-data .el-empty__description) {
    color: #a0a0c0;
  }
}

/* 测试计划对话框美化样式 */
:deep(.test-plan-dialog) {
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.15) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  width: 900px !important;
}

:deep(.test-plan-dialog .el-dialog__header) {
  display: none;
}

:deep(.test-plan-dialog .dialog-header) {
  padding: 20px 25px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  margin: -20px -25px 20px -25px;
  border-radius: 12px 12px 0 0;
}

:deep(.test-plan-dialog .dialog-title) {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.3px;
}

:deep(.test-plan-dialog .plan-form) {
  padding: 0 15px;
  max-height: 70vh;
  overflow-y: auto;
}

:deep(.test-plan-dialog .el-form-item) {
  margin-bottom: 20px;
  transition: all 0.2s ease;
  border-radius: 10px;
}

:deep(.test-plan-dialog .el-form-item:hover) {
  transform: translateX(3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

:deep(.test-plan-dialog .el-form-item__label) {
  font-size: 14px;
  padding: 0 10px 6px 0;
  text-align: right;
  color: #475569;
  font-weight: 500;
}

:deep(.test-plan-dialog .el-form-item__label .el-form-item__label-required) {
  color: #ef4444;
  margin-right: 3px;
}

/* 输入框美化 */
:deep(.test-plan-dialog .custom-input .el-input__wrapper),
:deep(.test-plan-dialog .custom-select .el-select__wrapper),
:deep(.test-plan-dialog .custom-textarea .el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) inset;
  transition: all 0.25s ease;
  height: 42px;
  background: white;
}

:deep(.test-plan-dialog .custom-input .el-input__wrapper:hover),
:deep(.test-plan-dialog .custom-select .el-select__wrapper:hover),
:deep(.test-plan-dialog .custom-textarea .el-textarea__inner:hover) {
  border-color: #94a3b8;
  box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.1);
}

:deep(.test-plan-dialog .custom-input .el-input__wrapper.is-focus),
:deep(.test-plan-dialog .custom-select .el-select__wrapper.is-focused),
:deep(.test-plan-dialog .custom-textarea .el-textarea__inner:focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  outline: none;
}

:deep(.test-plan-dialog .el-textarea__inner) {
  min-height: 40px !important;
  resize: vertical;
  line-height: 1.6;
  font-size: 14px;
  border-radius: 8px;
}

/* Switch开关样式优化 */
:deep(.test-plan-dialog .el-switch) {
  --el-switch-on-color: #667eea;
  --el-switch-off-color: #e6e6e6;
  --el-switch-on-text-color: #ffffff;
  --el-switch-off-text-color: #999999;
}

:deep(.test-plan-dialog .el-switch__label) {
  font-size: 13px;
}

/* 底部按钮区域 */
:deep(.test-plan-dialog .dialog-footer) {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 25px 25px;
  border-top: 1px solid #f0f2f5;
  background-color: #f8fafc;
  margin: 15px -25px -25px -25px;
  border-radius: 0 0 12px 12px;
}

:deep(.test-plan-dialog .footer-button) {
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

:deep(.test-plan-dialog .cancel-button) {
  border: 1px solid #e2e8f0;
  color: #475569;
  background-color: #ffffff;
}

:deep(.test-plan-dialog .cancel-button:hover) {
  background-color: #f1f5f9;
  border-color: #cbd5e1;
  transform: translateY(-2px);
}

:deep(.test-plan-dialog .confirm-button) {
  background-color: #667eea;
  border-color: #667eea;
  color: white;
}

:deep(.test-plan-dialog .confirm-button:hover) {
  background-color: #5a6fd8;
  border-color: #5a6fd8;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

:deep(.test-plan-dialog .confirm-button:active) {
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

/* 响应式调整 */
@media (max-width: 768px) {
  :deep(.test-plan-dialog) {
    width: 95% !important;
  }

  :deep(.test-plan-dialog .el-form-item__label) {
    text-align: left;
    padding-bottom: 5px;
    display: block;
  }
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

/* 分页器容器 */
.pagination-wrapper {
  flex: 1;
  display: flex;
  justify-content: flex-start;
}

/* 操作按钮容器 */
.footer-actions {
  display: flex;
  justify-content: flex-end;
  flex-shrink: 0;
  margin-left: 20px;
}

/* 调整分页器样式 */
:deep(.pagination-wrapper .el-pagination) {
  font-size: 12px;
  width: auto;
}

:deep(.pagination-wrapper .el-pagination__sizes .el-input .el-input__inner) {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

:deep(.pagination-wrapper .el-pager li) {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin: 0 2px;
}

:deep(.pagination-wrapper .el-pagination .btn-prev),
:deep(.pagination-wrapper .el-pagination .btn-next) {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

/* 调整Go to输入框 */
:deep(.pagination-wrapper .el-pagination__jump .el-input .el-input__inner) {
  border-radius: 4px;
  padding: 0 8px;
  width: 50px;
}

:deep(.pagination-wrapper .el-pagination__editor) {
  margin: 0 4px;
}

/* 表单提示文本样式 */
.form-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
  line-height: 1.4;
}

.form-tip el-icon {
  flex-shrink: 0;
}

.cron-editor-container {
  width: 90%;
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.config-desc {
  margin: 10px 0;
  color: #34495e;
  font-size: 13px;
  font-weight: 500;
}

.rule-type-group {
  margin: 15px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.config-fields {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 10px 0;
}

.separator {
  color: #606266;
  white-space: nowrap;
  align-self: center;
  display: flex;
  align-items: center;
  padding-bottom: 20px;
}

.unit {
  color: #606266;
  white-space: nowrap;
  align-self: center;
  display: flex;
  align-items: center;
  padding-bottom: 20px;
}

.cron-preview {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px dashed #e6e6e6;
}

.preview-label {
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
}

.cron-expression {
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e6e6e6;
  margin-bottom: 10px;
  font-family: monospace;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  text-align: center;
  font-size: 14px;
}

.cron-expression span {
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 4px;
  background: rgba(102, 126, 234, 0.1);
}

.cron-fields {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.field-item {
  padding: 4px 8px;
  background: #eef2f7;
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
  border: 1px solid #ebeef5;
}

.field-item.active {
  background: #667eea;
  color: #fff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.execution-preview {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #e6e6e6;
}

.execution-times {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.time-item {
  font-size: 13px;
  color: chocolate;
  padding: 4px 0;
  font-style: italic;
  font-weight: 600;
  background: rgba(210, 105, 30, 0.05);
  border-left: 3px solid chocolate;
  padding-left: 10px;
  border-radius: 0 4px 4px 0;
}

.no-execution {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
  padding: 10px;
  background: rgba(144, 147, 153, 0.05);
  border-radius: 4px;
  border-left: 3px solid #909399;
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

/* 统一设置选择器和输入框的圆角 */
:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(235, 238, 245, 0.5) !important;
  transition: all 0.3s ease;
}

.drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.case-info {
  margin-bottom: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.case-info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #f9fafb;
  transition: all 0.2s ease;
}

.case-info-item:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.case-info-item .icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-size: 14px;
}

.case-info-item .label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  margin-bottom: 4px;
}

.case-info-item .value {
  font-size: 15px;
  color: #1e293b;
  font-weight: 600;
  line-height: 1.4;
  word-break: break-all;
}

.detail-header {
  padding: 24px 24px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
  border-bottom: 1px solid #e5e7eb;
  position: relative;
}

.detail-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(to bottom, #667eea, #764ba2);
  border-radius: 4px 0 0 4px;
}

.detail-title h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-title h2::before {
  content: '';
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  flex-shrink: 0;
}

.detail-title .sub-title {
  margin: 8px 0 0;
  font-size: 14px;
  color: #64748b;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.sub-title > span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  background: #f1f5f9;
  border-radius: 6px;
  font-weight: 500;
  color: #475569;
  font-size: 12px;
}


.code-content :deep(.line-number) {
  display: inline-block;
  width: 30px;
  padding-right: 10px;
  text-align: right;
  color: #858585 !important; /* 行号颜色 */
  user-select: none;
  border-right: 1px solid #444 !important; /* 行号分隔线 */
  margin-right: 10px;
  opacity: 0.8;
  font-size: 12px;
}

.code-content {
  background-color: #000000 !important; /* 深色背景 */
  color: #dadde5 !important; /* 浅色文字 */
  display: block;
  padding: 5px 15px 15px 15px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
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


.no-content {
  text-align: center;
  color: #909399;
  font-size: 14px;
  padding: 20px;
}

:deep(.detail-drawer) {
  border-radius: 16px !important;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15) !important;
}

:deep(.el-card) {
  --el-card-padding: 16px; /* 自定义内边距，例如 16px */
}
</style>




