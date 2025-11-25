<template>
  <div class="workspace-detail">
    <!-- 第一块：空间图标，名称，管理员 -->
    <el-card class="workspace-info-card mb-2">
      <div class="flex items-center">
        <!-- 空间图标 -->
        <div
          class="w-8 h-8 rounded flex items-center justify-center text-white font-bold text-sm mr-2"
          :style="{ backgroundColor: workspaceColor }"
        >
          {{ workspaceInitial }}
        </div>

        <!-- 空间信息 -->
        <div class="flex-1">
          <h1 class="text-lg font-bold text-gray-800 mb-0.5">{{ workspaceData.name }}</h1>
          <div class="flex items-center">
            <el-icon class="text-gray-600 mr-1" :size="12">
              <User/>
            </el-icon>
            <span class="text-gray-600 text-xs mr-1">管理员：</span>
            <el-tag
              v-for="manager in workspaceData.managers"
              :key="manager.username"
              size="small"
              class="mr-1 text-xs"
            >
              {{ manager.nickname }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 第二块：用例统计信息 -->
    <el-card class="statistics-card">
      <el-row :gutter="5">
        <el-col :span="6">
          <div class="statistic-item">
            <el-icon class="statistic-icon" :size="16">
              <Collection/>
            </el-icon>
            <div class="statistic-value text-base">{{ statistics.totalCases }}</div>
            <div class="statistic-label text-xs">用例总数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="statistic-item">
            <el-icon class="statistic-icon" :size="16">
              <Folder/>
            </el-icon>
            <div class="statistic-value text-base">{{ statistics.repositories }}</div>
            <div class="statistic-label text-xs">用例仓库数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="statistic-item">
            <el-icon class="statistic-icon" :size="16">
              <Document/>
            </el-icon>
            <div class="statistic-value text-base">{{ statistics.pytestCases }}</div>
            <div class="statistic-label text-xs">Pytest用例数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="statistic-item">
            <el-icon class="statistic-icon" :size="16">
              <Files/>
            </el-icon>
            <div class="statistic-value text-base">{{ statistics.testngCases }}</div>
            <div class="statistic-label text-xs">TestNG用例数</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import {User, Collection, Folder, Document, Files} from '@element-plus/icons-vue'
import {getWorkspaceDetail} from "@/network/api.js"

export default {
  name: "WorkspaceDetail",
  components: {
    User,
    Collection,
    Folder,
    Document,
    Files
  },
  data() {
    return {
      // 工作空间数据
      workspaceData: {
        id: '',
        name: '',
        managers: []
      },
      // 统计数据
      statistics: {
        totalCases: 0,
        repositories: 0,
        pytestCases: 0,
        testngCases: 0
      }
    }
  },
  computed: {
    // 生成工作空间名称首字母作为图标
    workspaceInitial() {
      return this.workspaceData.name ? this.workspaceData.name.charAt(0).toUpperCase() : '';
    },
    // 生成随机颜色
    workspaceColor() {
      if (!this.workspaceData.name) return '#4299e1';

      const colors = [
        '#4299e1', '#38b2ac', '#805ad5', '#ed64a6', '#ed8936',
        '#319795', '#6b46c1', '#d53f8c', '#dd6b20', '#4c51bf'
      ];
      // 根据工作空间名称生成固定颜色索引
      const index = Math.abs(this.workspaceData.name.split('').reduce((acc, char) =>
        acc + char.charCodeAt(0), 0)) % colors.length;
      return colors[index];
    }
  },
  async mounted() {
    // 页面加载时获取工作空间详情
    await this.fetchWorkspaceDetail();
  },
  methods: {
    // 获取工作空间详情
    async fetchWorkspaceDetail() {
      try {
        const res = await getWorkspaceDetail({
          workspace_id: this.$route.params.id
        });

        if (res.code === 0) {
          const data = res.data;
          // 更新工作空间数据
          this.workspaceData = {
            id: data.workspace_id,
            name: data.workspace_name,
            managers: data.manager_info_list.map(manager => ({
              username: manager.username,
              nickname: manager.nickname,
              email: manager.email
            }))
          };

          // 这里可以添加获取统计数据的逻辑
          // 暂时使用模拟数据
          this.statistics = {
            totalCases: 128,
            repositories: 5,
            pytestCases: 76,
            testngCases: 52
          };
        } else {
          this.$message.error(res.message || '获取工作空间详情失败');
        }
      } catch (error) {
        console.error('获取工作空间详情失败:', error);
        this.$message.error('获取工作空间详情失败');
      }
    }
  }
}
</script>

<style scoped>
.workspace-detail {
  padding: 5px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 40px);
}

.workspace-info-card {
  border-radius: 4px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 8px;
}

.statistics-card {
  border-radius: 4px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 8px;
}

.statistic-item {
  text-align: center;
  padding: 8px 0;
}

.statistic-icon {
  color: #409eff;
  margin-bottom: 4px;
}

.statistic-value {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 2px;
}

.statistic-label {
  color: #666;
}
</style>
