# CaseRunRun

## 项目简介

CaseRunRun 是一个企业级自动化测试管理平台，专为测试团队设计，提供测试用例管理、测试计划编排、自动化测试执行和报告生成的完整解决方案。

**核心价值**：
- 统一管理不同类型的测试用例（支持 Pytest 和 TestNG）
- 灵活的测试计划编排与调度
- 自动化测试执行与结果分析
- 与代码仓库（GitLab）集成，实现测试用例自动同步
- 多工作空间隔离，支持团队协作

## 主要功能

### 📋 测试用例管理
- 支持 Pytest 和 TestNG 两种类型的测试用例
- 从 GitLab 代码仓库同步测试用例
- 测试用例元数据管理（作者、级别、路径等）
- 测试用例详情查看与搜索

### 📅 测试计划管理
- 创建、编辑、删除测试计划
- 向测试计划添加/移除测试用例
- 支持定时执行测试计划（基于 cron 表达式）
- 支持测试结果通知（企业微信、飞书、钉钉）

### 🚀 测试执行与报告
- 支持多种测试框架的执行
- 实时监控测试执行状态
- 生成详细的测试报告
- 测试结果可视化展示

### 🏢 工作空间管理
- 支持多工作空间隔离
- 每个工作空间有独立的测试用例和计划
- 工作空间级别的权限管理

### 🌐 虚拟环境管理
- 为测试执行提供隔离的环境
- 支持不同版本的依赖管理
- 确保测试执行的一致性和可重复性

## 技术架构

### 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  前端 Vue.js    │────▶│  后端 FastAPI   │────▶│  数据库/缓存    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │  任务调度系统   │
                      └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │  测试执行引擎   │
                      └─────────────────┘
```

### 技术栈

| 类别 | 技术 | 版本/说明 |
|------|------|----------|
| 后端 | Python | 3.9+ |
| 后端框架 | FastAPI | 0.104.1+ |
| 数据库 ORM | SQLAlchemy | 2.0.23+ |
| 缓存 | Redis | 7.0+ |
| 任务调度 | APScheduler | 3.10.4+ |
| 前端 | Vue.js | 3.3.4+ |
| 前端构建 | Vite | 4.4.5+ |
| 部署 | Docker | 20.10+ |

## 系统要求

- **硬件要求**：
  - CPU: 2核以上
  - 内存: 4GB以上
  - 磁盘: 50GB以上

- **软件要求**：
  - Python 3.9+
  - Redis 7.0+
  - MySQL 8.0+ 或 PostgreSQL 14.0+
  - Node.js 16.0+ (前端构建)

## 安装部署

### 1. 克隆项目

```bash
git clone https://github.com/your-username/caserunrun.git
cd caserunrun
```

### 2. 后端部署

#### 2.1 安装依赖

```bash
pip install -r requirements.txt
```

#### 2.2 配置环境变量

复制 `.env` 文件并修改配置：

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis 等连接信息
```

#### 2.3 启动后端服务

```bash
# 开发环境
python main.py

# 生产环境
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. 前端部署

#### 3.1 安装依赖

```bash
cd caserunrunFrontEnd
npm install
```

#### 3.2 配置环境变量

编辑 `.env.development` 或 `.env.production` 文件：

```bash
# 修改 API 地址
VITE_API_BASE_URL=http://localhost:8000/api
```

#### 3.3 构建和运行

```bash
# 开发环境
npm run dev

# 生产环境构建
npm run build

# 生产环境部署
# 将 dist 目录部署到 Nginx 或其他静态文件服务器
```

### 4. Docker 部署

#### 4.1 构建镜像

```bash
docker build -t caserunrun .
```

#### 4.2 运行容器

```bash
docker run -d \
  --name caserunrun \
  -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://user:password@host:port/dbname" \
  -e REDIS_URL="redis://host:port" \
  caserunrun
```

## 快速开始

### 1. 初始化系统

1. 启动后端服务
2. 访问 API 文档：`http://localhost:8000/docs`
3. 使用默认管理员账号登录

### 2. 配置 GitLab 连接

1. 在系统设置中配置 GitLab 地址和访问令牌
2. 创建工作空间
3. 添加测试用例源（GitLab 项目）

### 3. 管理测试用例

1. 同步测试用例（从 GitLab 拉取）
2. 浏览和搜索测试用例
3. 查看测试用例详情

### 4. 创建测试计划

1. 创建新的测试计划
2. 添加测试用例到计划
3. 配置执行环境和通知方式
4. 设置定时执行规则（可选）

### 5. 执行测试

1. 手动触发测试计划
2. 查看测试执行状态
3. 查看测试报告和结果

## API 文档

- **Swagger UI**：`http://localhost:8000/docs`
- **ReDoc**：`http://localhost:8000/redoc`

## 项目结构

```
caserunrun/
├── app/                      # 后端应用主目录
│   ├── api/                  # API 路由定义
│   │   └── v1/               # API v1 版本
│   ├── case_handler/         # 测试用例处理模块
│   ├── case_source/          # 测试用例源管理
│   ├── core/                 # 核心功能模块
│   ├── runner/               # 测试执行引擎
│   ├── setting/              # 系统设置
│   ├── testplan/             # 测试计划管理
│   ├── user/                 # 用户管理
│   ├── virtual_env/          # 虚拟环境管理
│   └── workspace/            # 工作空间管理
├── caserunrunFrontEnd/       # 前端项目
│   ├── public/               # 静态资源
│   └── src/                  # 前端源码
├── docker_build/             # Docker 构建配置
├── media/                    # 媒体文件（测试报告等）
├── utils/                    # 工具函数
├── main.py                   # 后端入口
└── requirements.txt          # Python 依赖
```

## 核心模块说明

### 测试用例管理模块
- **case_handler**：负责测试用例的解析、同步和管理
- **case_source**：管理测试用例的来源（如 GitLab 项目）

### 测试计划模块
- **testplan**：管理测试计划的创建、编辑和执行
- **runner**：负责测试用例的执行和结果收集

### 核心功能模块
- **core**：包含配置、数据库连接、异常处理等核心功能
- **user**：用户认证和权限管理
- **workspace**：工作空间管理
- **virtual_env**：虚拟环境管理

## 贡献指南

1. **Fork 项目**
2. **创建分支**：`git checkout -b feature/your-feature`
3. **提交更改**：`git commit -m 'Add some feature'`
4. **推送到分支**：`git push origin feature/your-feature`
5. **创建 Pull Request**

## 问题反馈

- **Bug 报告**：在 GitHub Issues 中提交
- **功能请求**：在 GitHub Issues 中提交
- **技术支持**：联系项目维护者

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件

## 联系我们

- **项目维护者**：baojun.wang
- **Email**：baojun.wang@example.com
- **GitHub**：[https://github.com/your-username/caserunrun](https://github.com/your-username/caserunrun)

---

**CaseRunRun** - 让测试更简单，让质量更可靠！ 🚀