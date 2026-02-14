<template>
  <el-drawer
    :model-value="visible"
    title="用例详情"
    direction="rtl"
    :size="'80%'"
    :with-header="true"
    :resizable="true"
    class="detail-drawer"
    @update:model-value="emit('update:visible', $event)"
  >
    <!-- 抽屉内容区 -->
    <div class="drawer-content">
      <!-- 顶部信息栏 -->
      <div class="detail-header">
        <div class="detail-title">
          <h2>{{ testCase?.case_name || '未选择用例' }}</h2>
          <p class="sub-title">ID: {{ testCase?.id || '-' }} | 上次同步:
            {{ formatTime(testCase?.update_time) }}</p>
        </div>
        <div class="detail-tags">
          <el-tag
            :type="testCase?.case_type === 'pytest' ? 'primary' : 'success'"
            class="tag-type"
          >
            {{ testCase?.case_type === 'pytest' ? 'Python (Pytest)' : 'Java (TestNG)' }}
          </el-tag>
          <el-tag
            :type="getSpecificTypeTagType(testCase?.specific_type)"
            class="tag-type"
          >
            {{ getSpecificTypeName(testCase?.specific_type) }}
          </el-tag>
          <el-tag
            :type="getCaseLevelTagType(testCase?.case_level)"
            class="tag-priority"
          >
            S{{ testCase?.case_level !== undefined ? testCase?.case_level : '-' }}
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
                <div class="info-value">{{ testCase?.git_project_name || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <el-icon>
                    <Collection/>
                  </el-icon>
                  <span>用例名称</span>
                </div>
                <div class="info-value">{{ testCase?.case_name || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <el-icon>
                    <Folder/>
                  </el-icon>
                  <span>用例路径</span>
                </div>
                <div class="info-value mono-text">{{ testCase?.case_path || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <el-icon>
                    <User/>
                  </el-icon>
                  <span>作者</span>
                </div>
                <div class="info-value" v-if="testCase?.case_author.nickname">
                  <el-tooltip
                    :content="`${testCase?.case_author.nickname}(${testCase?.case_author.username})`"
                    placement="top"
                  >
                    <span class="author-text">{{ testCase?.case_author.nickname }}</span>
                  </el-tooltip>
                </div>
                <div class="info-value" v-else>{{ testCase?.case_author.username || '-' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">
                  <el-icon>
                    <Coin/>
                  </el-icon>
                  <span>commit_id</span>
                </div>
                <div class="info-value">{{ testCase?.case_commit_id || '-' }}</div>
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
                  {{ testCase?.case_type === 'pytest' ? 'Python' : 'Java' }}
                </span>
                <el-button
                  size="small"
                  type="primary"
                  @click="openFullscreen"
                  :disabled="!testCaseContent || testCaseContent.includes('加载中')"
                  class="fullscreen-btn"
                >
                  <el-icon :size="16">
                    <FullScreen/>
                  </el-icon>
                  全屏
                </el-button>
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
              <!-- 加载中状态 -->
              <div v-if="!testCaseContent || testCaseContent.includes('加载中')"
                   class="code-loading">
                <el-icon class="loading-spinner is-loading">
                  <Loading/>
                </el-icon>
                <p>加载代码中...</p>
              </div>
              <!-- 代码内容 -->
              <div v-else class="code-container" ref="normalCodeContainer">
                <div class="line-numbers" ref="normalLineNumbers">
                  <div
                    v-for="(line, index) in testCaseContent.split('\n')"
                    :key="`normal-${index}`"
                    class="line-number"
                  >
                    {{ index + 1 }}
                  </div>
                </div>
                <pre class="code-pre" ref="normalCodePre">
                  <code
                    class="code-content"
                    :class="testCase?.case_type === 'pytest' ? 'language-python' : 'language-java'"
                    v-html="highlightedCode"
                  ></code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 全屏对话框 -->
    <el-dialog
      v-if="fullscreenVisible"
      v-model="fullscreenVisible"
      :title="testCase?.case_name || '代码预览'"
      fullscreen
      transition="scale"
      class="fullscreen-dialog"
      @opened="doHighlightFull"
    >
      <div class="fullscreen-code-container">
        <!-- 加载中状态 -->
        <div v-if="!testCaseContent || testCaseContent.includes('加载中')" class="code-loading">
          <el-icon class="loading-spinner is-loading">
            <Loading/>
          </el-icon>
          <p>加载代码中...</p>
        </div>
        <!-- 全屏代码内容 -->
        <div v-else class="code-container fullscreen-code-container-inner">
          <div class="line-numbers">
            <div
              v-for="(line, index) in testCaseContent.split('\n')"
              :key="`fullscreen-${index}`"
              class="line-number"
            >
              {{ index + 1 }}
            </div>
          </div>
          <pre class="code-pre fullscreen-code-pre">
            <code
              ref="fullCodeRef"
              class="fullscreen-code-content"
              :class="testCase?.case_type === 'pytest' ? 'language-python' : 'language-java'"
            ></code>
          </pre>
        </div>
      </div>
      <template #footer>
        <div class="fullscreen-dialog-footer">
          <el-button @click="closeFullscreen">关闭</el-button>
          <el-button type="primary" @click="copyCode">复制代码</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 抽屉底部按钮 -->
    <template #footer>
      <div class="drawer-actions">
        <el-button
          type="default"
          @click="closeDrawer"
          class="btn-secondary"
        >
          关闭
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import {ref, computed, onMounted, watch} from 'vue'
import {ElNotification} from 'element-plus'

import {
  Coin,
  CopyDocument,
  Document,
  Document as Collection,
  Folder,
  FullScreen,
  InfoFilled,
  Loading,
  Memo,
  User
} from '@element-plus/icons-vue'

// 完整导入highlight.js并全局注册
import hljs from 'highlight.js';
import 'highlight.js/styles/a11y-dark.css';
// 预加载语言包，解决首次识别失败问题
import python from 'highlight.js/lib/languages/python';
import java from 'highlight.js/lib/languages/java';

hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);

// Props 定义
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  testCase: {
    type: Object,
    default: () => ({})
  },
  testCaseContent: {
    type: String,
    default: ''
  }
});

// Emit 定义
const emit = defineEmits(['update:visible', 'close']);

// 内部状态
const fullscreenVisible = ref(false);
const fullCodeRef = ref(null);
// 非全屏代码容器 refs
const normalCodeContainer = ref(null);
const normalCodePre = ref(null);
const normalLineNumbers = ref(null);

// 计算语言类型
const lang = computed(() => props.testCase?.case_type === 'pytest' ? 'python' : 'java');

// 实时高亮普通区域代码
const highlightedCode = computed(() => {
  if (!props.testCaseContent) return '';
  try {
    return hljs.highlight(props.testCaseContent, {language: lang.value}).value;
  } catch (e) {
    return props.testCaseContent;
  }
});

// 打开全屏对话框
const openFullscreen = () => {
  fullscreenVisible.value = true;
};

// 关闭全屏对话框
const closeFullscreen = () => {
  fullscreenVisible.value = false;
};

// 全屏代码高亮（每次打开都执行）
const doHighlightFull = () => {
  if (!fullCodeRef.value || !props.testCaseContent) return;
  // 重置内容并高亮
  fullCodeRef.value.textContent = props.testCaseContent;
  fullCodeRef.value.className = `fullscreen-code-content language-${lang.value}`;
  hljs.highlightElement(fullCodeRef.value);
};

// 同步滚动：核心修复 - 精准绑定当前容器的滚动事件
const syncScroll = () => {
  // 非全屏代码区域同步
  if (normalCodePre.value && normalLineNumbers.value) {
    // 移除旧的滚动事件，避免重复绑定
    normalCodePre.value.onscroll = null;
    // 绑定新的滚动事件：行号跟随代码滚动
    normalCodePre.value.onscroll = () => {
      normalLineNumbers.value.scrollTop = normalCodePre.value.scrollTop;
      normalLineNumbers.value.scrollLeft = normalCodePre.value.scrollLeft;
    };
  }
};

// 组件挂载时初始化滚动同步
onMounted(() => {
  syncScroll();
});

// 监听代码内容变化，重新绑定滚动（解决代码更新后滚动失效）
watch(() => props.testCaseContent, () => {
  // 延迟一点，确保DOM更新完成
  setTimeout(() => syncScroll(), 100);
});

// 监听抽屉显示状态，确保DOM渲染完成后绑定滚动
watch(() => props.visible, (newVal) => {
  if (newVal) {
    setTimeout(() => syncScroll(), 200);
  }
});

// 复制代码
const copyCode = async () => {
  if (!props.testCaseContent || props.testCaseContent.includes('加载中')) {
    ElNotification({
      title: '提示',
      message: '暂无可复制的代码内容',
      type: 'warning',
      duration: 2000
    });
    return;
  }

  try {
    await navigator.clipboard.writeText(props.testCaseContent);
    ElNotification({
      title: '成功',
      message: '代码已复制到剪贴板',
      type: 'success',
      duration: 2000
    });
  } catch (e) {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = props.testCaseContent;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    ElNotification({
      title: '成功',
      message: '代码已复制到剪贴板（降级模式）',
      type: 'success',
      duration: 2000
    });
  }
};

// 关闭抽屉
const closeDrawer = () => {
  emit('update:visible', false);
  emit('close');
};

// 辅助方法
const formatTime = (timeString) => {
  if (!timeString) return '-';
  return new Date(timeString).toLocaleString('zh-CN');
};

const getSpecificTypeName = (type) => {
  const typeMap = {
    10: 'Web',
    11: 'H5',
    12: '接口'
  };
  return typeMap[type] || type || '-';
};

const getSpecificTypeTagType = (type) => {
  const typeMap = {
    10: 'primary',
    11: 'success',
    12: 'warning'
  };
  return typeMap[type] || 'info';
};

const getCaseLevelTagType = (level) => {
  const levelMap = {
    0: 'danger',
    1: 'warning',
    2: 'primary',
    3: 'info'
  };
  return levelMap[level] || 'info';
};
</script>

<style scoped>
/* 抽屉样式 */
.detail-drawer .el-drawer__header {
  display: none; /* 隐藏默认标题栏 */
}

.detail-drawer .el-drawer__body {
  padding: 24px;
  overflow: hidden;
}

.drawer-content {
  height: calc(100vh - 155px);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.detail-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0;
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

.tag-type {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 6px;
  background-color: rgba(64, 158, 255, 0.1);
  color: #3b82f6;
  border: none;
  transition: all 0.2s ease;
}

.tag-type:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.tag-priority {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
  border: none;
  transition: all 0.2s ease;
}

.detail-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  flex: 1;
  overflow: hidden;
  margin-top: 10px;
}

.panel-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0;
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
  flex-shrink: 0;
}

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

.code-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  margin-top: 0;
}

.code-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  background-color: #1e1e1e;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.code-card .panel-title {
  background: linear-gradient(to right, #1e293b, #0f172a);
  color: #e2e8f0;
  border-bottom: 1px solid #334155;
  padding: 12px 10px;
}

.code-card .panel-icon {
  color: #94a3b8;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
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
  margin-right: 15px;
}

.copy-btn {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
  transition: all 0.2s;
  padding: 6px 12px;
  border-radius: 6px;
  margin-right: 20px;
}

.copy-btn:hover {
  background-color: #2563eb;
  border-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 代码容器样式 */
.code-container {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 行号栏样式 - 核心修复：统一行距 + 可滚动 */
.line-numbers {
  width: 60px;
  min-width: 60px;
  padding: 18px 0;
  background-color: #181818;
  border-right: 1px solid #333;
  overflow: hidden;
  flex-shrink: 0;
  /* 禁止行号容器滚动 */
  overflow-y: inherit;
  /* 隐藏滚动条 */
  scrollbar-width: none;
}

.line-numbers::-webkit-scrollbar {
  display: none;
}

/* 核心修复：行号与代码行距完全统一 */
.line-number {
  height: 22px;
  line-height: 22px;
  text-align: right;
  padding: 0 12px;
  font-size: 13px;
  color: #858585;
  user-select: none;
  white-space: nowrap;
  font-family: 'Fira Code', monospace;
}

/* 代码内容栏样式 - 核心修复：统一行距 */
.code-pre {
  flex: 1;
  margin: 0;
  padding: 0;
  overflow: auto;
  height: 100%;
  background-color: #1e1e1e;
  /* 统一字体 */
  font-family: 'Fira Code', monospace;
}

/* 核心修复：代码内容行距与行号完全一致 */
.code-content {
  display: block;
  padding: 0 20px;
  font-size: 13px;
  line-height: 22px; /* 和行号的line-height一致 */
  color: #dadde5;
  background-color: transparent;
  white-space: pre;
  min-width: fit-content;
  font-family: 'Fira Code', monospace;
}

/* 代码加载样式 */
.code-content-wrapper {
  flex: 1;
  overflow: hidden;
  padding: 0;
  position: relative;
  height: calc(100% - 48px);
}

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

.detail-drawer .el-drawer__footer {
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

.fullscreen-btn {
  background-color: #67c23a;
  border-color: #67c23a;
  color: white;
  transition: all 0.2s;
  padding: 6px 12px;
  border-radius: 6px;
  margin-right: 1px;
}

.fullscreen-btn:hover {
  background-color: #5daf34;
  border-color: #5daf34;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.fullscreen-btn:disabled {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
  color: #c0c4cc;
}

.fullscreen-dialog .el-dialog__header {
  background: linear-gradient(to right, #1e293b, #0f172a);
  padding: 20px 20px;
}

.fullscreen-dialog .el-dialog__title {
  color: #e2e8f0;
  font-weight: 600;
}

.fullscreen-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #94a3b8;
}

.fullscreen-dialog .el-dialog__headerbtn .el-dialog__close:hover {
  color: #ffffff;
}

.fullscreen-dialog .el-dialog__body {
  padding: 0;
  background-color: #181818;
  height: calc(100vh - 125px);
}

.fullscreen-code-container {
  height: 100%;
  overflow: hidden;
}

.fullscreen-code-container-inner {
  height: 100%;
}

.fullscreen-code-pre {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: auto;
  background-color: #1e1e1e;
  font-family: 'Fira Code', monospace;
}

.fullscreen-code-content {
  display: block;
  padding: 2px 25px;
  font-size: 13px;
  line-height: 22px; /* 统一全屏行距 */
  color: #dadde5;
  background-color: transparent;
  white-space: pre;
  min-width: fit-content;
  font-family: 'Fira Code', monospace;
}

.fullscreen-dialog .el-dialog__footer {
  background-color: #ffffff;
  padding: 12px 20px;
  border-top: 1px solid #e2e8f0;
}

.fullscreen-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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
  .detail-drawer .el-drawer__body {
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

  .line-numbers {
    width: 50px;
    min-width: 50px;
  }

  .line-number {
    padding: 0 8px;
  }
}

/* 强制清除代码块中的 text-shadow */
.code-content,
.fullscreen-code-content,
.code-content code,
.code-content pre {
  text-shadow: none !important;
}
</style>
