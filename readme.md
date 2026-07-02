# 每日论文总结应用

每天定时从 arXiv 抓取匹配关键词的高质量论文，生成研究热点与重要事件摘要，并输出 Markdown 日报与静态 HTML 网站。

## 功能

- 按 `config.yaml` 中的关键词与类别抓取 arXiv 论文
- 对论文进行质量打分，筛选 Top-K 高水平论文
- 生成每日 Markdown 日报（`output/reports/YYYY-MM-DD.md`）
- 构建静态 HTML 网站（`site/`，含首页 + 历史归档）
- 支持本地定时运行，或通过 GitHub Actions 自动更新并发布到 GitHub Pages

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 立即执行一次（抓取 + 生成日报 + 构建网站）
python main.py --once

# 启动本地定时任务（默认每天 08:00，Asia/Shanghai）
python main.py
```

产物位置：

- 论文数据：`output/papers/YYYY-MM-DD/`
- Markdown 日报：`output/reports/YYYY-MM-DD.md`
- 静态网站：`site/index.html`、`site/reports/YYYY-MM-DD.html`

本地预览网站：

```bash
cd site && python -m http.server 8000
```

浏览器访问 `http://127.0.0.1:8000`。

## 配置

编辑 `config.yaml`：

- `keywords`：搜索关键词
- `categories`：arXiv 类别
- `days_back` / `max_results` / `top_k`：时间范围与筛选数量
- `output_dir`：数据与 Markdown 输出目录
- `site_dir`：静态网站输出目录
- `schedule.time`：本地定时执行时间

如需启用大模型总结，复制 `.env.example` 为 `.env` 并配置：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

未配置 API Key 时自动使用规则模式（摘要首句 + 关键词词频统计热点）。

## GitHub Pages 部署（详细步骤）

下面是从零到上线的完整流程，按顺序操作即可。

### 前置准备

- 一个 [GitHub 账号](https://github.com/)
- 本机已安装 [Git](https://git-scm.com/)
- 本地已能正常运行：`python main.py --once`，且 `site/` 目录下有 `index.html`

### 第一步：在 GitHub 创建仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 填写仓库信息：
   - **Repository name**：例如 `paper-reading`（项目站点）或 `你的用户名.github.io`（用户站点）
   - **Public**：选 Public（免费 GitHub Pages 需要公开仓库，或你有 Pro 账号可用私有仓库）
   - **不要**勾选 "Add a README file"（避免和本地代码冲突）
3. 点击 **Create repository**
4. 记下仓库地址，例如：
   - `https://github.com/你的用户名/paper-reading.git`

> **两种站点地址区别**
>
> | 仓库名 | 访问地址 |
> |--------|----------|
> | `paper-reading`（普通项目仓库） | `https://你的用户名.github.io/paper-reading/` |
> | `你的用户名.github.io`（专用用户站点仓库） | `https://你的用户名.github.io/` |

### 第二步：本地初始化 Git 并推送代码

在项目根目录执行（把下面的用户名和仓库名换成你的）：

```bash
cd /path/to/paper_reading_cursor

# 初始化仓库
git init

# 添加所有文件（.gitignore 会排除 .venv、.env、site/ 等）
git add .
git commit -m "feat: initial paper reading app with GitHub Pages support"

# 关联远程仓库
git branch -M main
git remote add origin https://github.com/你的用户名/paper-reading.git

# 推送到 GitHub
git push -u origin main
```

推送时若提示登录，按 GitHub 页面指引使用 Personal Access Token 或 SSH。

**说明**：`site/` 目录不提交到仓库，它由 GitHub Actions 每次运行时重新生成并直接发布到 Pages。历史日报的 Markdown 会保存在 `output/reports/` 并提交回仓库。

### 第三步：开启 GitHub Pages

1. 打开你的 GitHub 仓库页面
2. 进入 **Settings**（设置）→ 左侧 **Pages**
3. 在 **Build and deployment** 区域：
   - **Source** 选择 **GitHub Actions**（不要选 Deploy from a branch）
4. 保存后无需其他配置，页面会提示等待第一次 Actions 部署

### 第四步：首次手动触发部署

定时任务每天北京时间 08:00 才会自动跑，首次建议手动触发：

1. 进入仓库的 **Actions** 标签页
2. 左侧选择 **Daily Paper Report** 工作流
3. 点击右侧 **Run workflow** → 选择 `main` 分支 → **Run workflow**
4. 等待约 1～3 分钟，点击正在运行的任务查看日志

**成功标志**（各步骤应显示绿色 ✓）：

| 步骤 | 说明 |
|------|------|
| Checkout repository | 拉取代码 |
| Set up Python | 安装 Python 3.11 |
| Install dependencies | 安装依赖 |
| Run daily pipeline | 抓取 arXiv、生成日报和网站 |
| Commit report history | 将 `output/` 提交回仓库 |
| Upload Pages artifact | 上传 `site/` 静态文件 |
| Deploy to GitHub Pages | 发布到 Pages |

若 **Deploy to GitHub Pages** 第一次失败并提示需要配置 environment：

1. 回到 **Settings → Pages**，确认 Source 为 **GitHub Actions**
2. 再次手动 Run workflow，通常第二次即可成功

### 第五步：访问你的网站

部署成功后：

1. 在 **Settings → Pages** 顶部会显示：**Your site is live at ...**
2. 或在 Actions 运行日志最后的 **Deploy to GitHub Pages** 步骤里查看 `page_url`

访问地址示例：

- 项目仓库 `paper-reading`：`https://你的用户名.github.io/paper-reading/`
- 用户站点仓库 `你的用户名.github.io`：`https://你的用户名.github.io/`

首页展示最新日报，下方 **历史归档** 可点击进入往日详情。

### 第六步：确认自动更新

工作流 `.github/workflows/daily.yml` 已配置：

- **定时**：每天 UTC 00:00，即北京时间 **08:00**
- **手动**：随时可在 Actions 页面 **Run workflow**

每次自动运行会：

1. 抓取 arXiv 论文并生成当日日报
2. 把 `output/reports/YYYY-MM-DD.md` 提交回仓库（历史不丢失）
3. 重新构建 `site/` 并发布到 GitHub Pages

可在仓库 **Commits** 页面看到机器人提交：`chore: update daily paper reports`。

### 常见问题排查

**1. Actions 没有运行**

- 确认仓库是 Public，或账号支持私有仓库的 Actions
- 进入 **Settings → Actions → General**，确保 **Allow all actions** 已开启

**2. Run daily pipeline 失败**

- 点开失败步骤查看日志，常见原因是 arXiv 网络超时，重试即可
- 本地先执行 `python main.py --once` 确认能通过

**3. 网站 404**

- 等待 1～5 分钟再刷新（DNS 和 CDN 有缓存）
- 确认 Pages Source 是 **GitHub Actions** 而非 branch
- 确认最后一次 workflow 的 Deploy 步骤成功

**4. 样式或链接错乱**

- 项目站点请用完整路径访问，例如 `https://用户名.github.io/paper-reading/`，不要漏掉仓库名
- 本地预览用 `cd site && python -m http.server 8000`，访问 `http://127.0.0.1:8000`

**5. 想改用大模型总结**

在仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret 名称 | 值 |
|-------------|-----|
| `OPENAI_API_KEY` | 你的 API Key |
| `OPENAI_BASE_URL` | 可选，如 `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 可选，如 `gpt-4.1-mini` |

然后在 `.github/workflows/daily.yml` 的 `Run daily pipeline` 步骤增加 `env` 传入这些 Secret（需要的话可再改 workflow）。

### 部署后目录说明

```
仓库中（提交到 Git）          Actions 运行时生成（不提交 site/）
├── main.py                  ├── site/index.html      → 发布到 Pages
├── config.yaml              ├── site/reports/*.html
├── paper_reading/           └── output/reports/*.md  → 提交回仓库
└── output/reports/*.md
```

## 阶段二：迁移到服务器

当需要从 GitHub Actions 迁移到自有服务器时，可采用以下方案：

### 方案 A：系统 crontab（推荐）

```bash
# 每天 08:00 执行
0 8 * * * cd /path/to/paper_reading_cursor && /path/to/.venv/bin/python main.py --once
```

### 方案 B：常驻进程 + APScheduler

```bash
python main.py
```

程序会按 `config.yaml` 中的 `schedule.time` 每天自动执行。

### 网站托管

将 `site/` 目录通过 Web 服务器对外提供：

```bash
# 简单预览
cd site && python -m http.server 8080

# 或使用 nginx 指向 site/ 目录
```

若使用 nginx，将 `root` 指向项目的 `site/` 目录即可。

### 可选：启用大模型

在服务器上配置 `.env` 文件，填入 API Key 后即可启用 LLM 模式生成中文热点与大事件总结。
