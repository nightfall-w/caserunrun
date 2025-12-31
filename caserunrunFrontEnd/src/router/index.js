// src/router/index.js
import {createRouter, createWebHistory} from 'vue-router'
import Home from '@/views/Home.vue';
import Login from '@/views/Login.vue';
import WorkspaceDetail from '@/views/WorkspaceDetail.vue';
import BaseLayout from '@/components/BaseLayout.vue';
import SystemConfig from '@/views/SystemConfig.vue'
import WorkspaceConfig from '@/views/WorkspaceConfig.vue'
import CaseSourceManage from '@/views/CaseSourceManage.vue'
import TestCaseList from '@/views/TestCaseList.vue'
import TestPlanList from '@/views/TestPlanList.vue'
import TestTaskList from '@/views/TestTaskList.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Home,
    meta: {requiresAuth: true}
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {requiresAuth: true}
  },
  {
    path: '/system-config',
    name: 'SystemConfig',
    component: SystemConfig,
    meta: {requiresAuth: true}
  },
  {
    path: '/workspace/:id',
    component: BaseLayout,
    children: [
      {
        path: '',
        name: 'WorkspaceDetail',
        component: WorkspaceDetail,
        meta: {requiresAuth: true},
        props: true
      },
      {
        path: 'workspace-config',
        name: 'WorkspaceConfig',
        component: WorkspaceConfig,
        meta: {requiresAuth: true},
        props: true
      },
      {
        path: 'case-source-manage',
        name: 'CaseSourceManage',
        component: CaseSourceManage,
        meta: {requiresAuth: true},
        props: true
      },
      {
        path: 'test-case-list',
        name: 'TestCaseList',
        component: TestCaseList,
        meta: {requiresAuth: true},
        props: true
      },
      {
        path: 'test-plan-list',
        name: 'TestPlanList',
        component: TestPlanList,
        meta: {requiresAuth: true},
        props: true
      },
      {
        path: 'test-task-list',
        name: 'TestTaskList',
        component: TestTaskList,
        meta: {requiresAuth: true},
        props: true
      }
    ]
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 添加路由守卫
router.beforeEach((to, from, next) => {
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    // 检查用户是否已登录
    const currentUserJson = localStorage.getItem('currentUser')
    if (currentUserJson) {
      try {
        const currentUser = JSON.parse(currentUserJson)
        // 检查是否是环境变量中的超级管理员 (id=0)
        if (currentUser.id === 0) {
          // 如果是环境变量中的超级管理员，只能访问 /system-config 页面
          if (to.path !== '/system-config') {
            // 强制重定向到系统配置页面
            next('/system-config')
            return
          }
        }
        // 额外添加的管理员可以正常访问所有页面，不需要特殊处理

        // 允许访问
        next()
      } catch (e) {
        // JSON解析失败，认为未登录
        next('/login')
      }
    } else {
      // 未登录，保存当前访问路径并重定向到登录页
      if (to.path !== '/login') {
        // 保存用户尝试访问的路径
        localStorage.setItem('redirectPath', to.fullPath);
      }
      next('/login')
    }
  } else {
    // 不需要认证的页面（如登录页）直接访问
    next()
  }
})

export default router
