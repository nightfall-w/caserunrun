<!-- src/components/BaseLayout.vue -->
<template>
  <div class="bg-gray-50 min-h-screen flex flex-col">
    <!-- 添加 Header 组件 -->
    <Header/>

    <el-container class="flex-grow flex flex-col">
      <el-container class="flex-grow flex flex-row">
        <!-- 侧边栏菜单 -->
        <el-aside class="bg-white shadow-md" :width="isCollapse ? '54px' : '160px'">
          <div class="collapse-toggle" :class="{ 'collapsed': isCollapse }" @click="toggleCollapse">
            <el-icon v-if="isCollapse" :size="14" class="text-gray-600">
              <Expand/>
            </el-icon>
            <div v-else class="el-menu-item" style="padding: 0; height: 40px; line-height: 40px;">
              <el-icon :size="14" class="text-gray-600 mr-2">
                <Fold/>
              </el-icon>
              <span class="text-gray-600" style="font-size: 12px;">折叠</span>
            </div>
          </div>


          <el-menu
            default-active="dashboard"
            class="el-menu-vertical-demo"
            :collapse="isCollapse"
            router
            background-color="#ffffff"
            text-color="#333333"
            active-text-color="#165DFF"
            :collapse-transition="false"
          >
            <!-- 工作空间 -->
            <el-menu-item :index="'/workspace/' + workspaceId" v-if="workspaceId">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">概览</span>
            </el-menu-item>

            <el-menu-item :index="'/workspace/' + workspaceId+ '/case-source-manage'"
                          v-if="workspaceId">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">代码仓库</span>
            </el-menu-item>

            <el-menu-item :index="'/workspace/' + workspaceId +'/test-case-list'"
                          v-if="workspaceId">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">用例列表</span>
            </el-menu-item>

            <el-menu-item :index="'/workspace/' + workspaceId +'/test-plan-list'"
                          v-if="workspaceId">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">测试计划</span>
            </el-menu-item>

            <el-menu-item :index="'/workspace/' + workspaceId +'/test-task-list'"
                          v-if="workspaceId">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">测试任务</span>
            </el-menu-item>

            <el-menu-item :index="'/workspace/' + workspaceId +'/workspace-config'"
                          v-if="workspaceId && isWorkspaceAdmin">
              <el-icon class="text-lg">
                <Film/>
              </el-icon>
              <span v-if="!isCollapse">设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>


        <!-- 主内容区域 -->
        <el-main class="main-content">
          <router-view/>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {
  Film,
  Document,
  Grid,
  DataAnalysis,
  List,
  Reading,
  Expand,
  Fold
} from '@element-plus/icons-vue'
import Header from '@/components/Header.vue'
import {getWorkspaceDetail} from '@/network/api.js'

// 控制侧边栏折叠状态
const isCollapse = ref(false)

// 获取当前路由信息
const route = useRoute()

// 从路由参数中获取workspaceId
const workspaceId = computed(() => {
  return route.params.id
})

// 当前用户是否为工作区管理员
const isWorkspaceAdmin = ref(false)

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 获取工作区详情以判断用户权限
const fetchWorkspaceDetail = async () => {
  if (!workspaceId.value) return

  try {
    const res = await getWorkspaceDetail({
      workspace_id: workspaceId.value
    })

    if (res.code === 0) {
      // 获取当前用户信息
      const currentUserJson = localStorage.getItem('currentUser')
      if (currentUserJson) {
        const currentUser = JSON.parse(currentUserJson)
        // 检查当前用户是否为管理员
        isWorkspaceAdmin.value = res.data.manager_info_list.some(
          manager => manager.username === currentUser.username
        )
      }
    }
  } catch (error) {
    console.error('获取工作区详情失败:', error)
  }
}

// 组件挂载时获取工作区详情
onMounted(() => {
  fetchWorkspaceDetail()
})
</script>


<style scoped>
/* 侧边栏样式 */
.el-menu-vertical-demo {
  width: 100%;
  height: calc(100vh - 80px); /* 减去 Header 高度 */
  border: none;
}

/* 调整菜单项字体大小 */
.el-menu-vertical-demo .el-menu-item,
.el-menu-vertical-demo .el-sub-menu__title {
  font-size: 12px;
  height: 40px;
  line-height: 40px;
}

/* 调整图标大小 */
.el-menu-vertical-demo .el-menu-item .el-icon,
.el-menu-vertical-demo .el-sub-menu__title .el-icon {
  font-size: 14px;
}


/* 主内容区域样式 */
.main-content {
  padding: 5px;
  background-color: #f5f5f5;
  height: calc(100vh - 40px);
  overflow: hidden; /* 阻止整个页面滚动 */
}

/* 折叠按钮样式 */
.collapse-toggle {
  display: flex;
  align-items: center;
  height: 40px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  padding: 0 20px;
}

.collapse-toggle:hover {
  background-color: #f5f5f5;
}

/* 展开时左对齐 */
.collapse-toggle:not(.collapsed) {
  justify-content: flex-start;
}

/* 折叠时图标居中 */
.collapse-toggle.collapsed {
  justify-content: center;
}

/* 折叠时的菜单项样式 */
.el-menu--collapse .el-sub-menu__title span,
.el-menu--collapse .el-menu-item span {
  display: none;
}

.el-menu--collapse .el-sub-menu__title,
.el-menu--collapse .el-menu-item {
  text-align: center;
}

.el-menu--collapse .el-sub-menu__title .el-icon,
.el-menu--collapse .el-menu-item .el-icon {
  margin: 0 auto;
  width: 100%;
}
</style>
