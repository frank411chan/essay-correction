# 作文批改系统 v2.0

基于 Kimi 多模态大模型的本地作文批改 Web 应用。支持 OCR 多引擎选择、异步批改、文体模板、PDF 导出、学生管理、批量批改、多条件查询。

## 技术栈

- **前端**：Vue 3 + Vite + Element Plus + ECharts
- **后端**：Python 3.12 + FastAPI + SQLAlchemy
- **数据库**：SQLite（零配置）
- **AI**：Moonshot Kimi API（OpenAI 兼容接口）
- **OCR**：Kimi Vision / 百度手写 OCR / 腾讯手写 OCR

## 主要功能

1. **学生管理**：新增、修改、删除、查询学生
2. **单篇批改**：上传图片 → 选择学生/OCR 引擎/文体 → 异步批改 → 查看结果
3. **批量批改**：扫描指定日期目录，按 `人名_作文题目.jpg` 规则自动识别并批改
4. **OCR 引擎**：可选择 Kimi 视觉识别、百度手写 OCR、腾讯手写 OCR
5. **文体模板**：记叙文、议论文、说明文、散文
6. **PDF 导出**：导出完整批改报告
7. **历史查询**：按学生姓名、作文标题、日期、状态查询

## 目录结构

```
essay-correction/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/      # API 路由
│   │   ├── services/     # 业务服务
│   │   │   ├── ocr/      # OCR 引擎抽象层
│   │   │   ├── pdf_service.py
│   │   │   └── prompts.py
│   │   └── ...
│   ├── uploads/          # 上传图片
│   ├── .env              # 配置文件（不提交 Git）
│   └── venv/             # Python 虚拟环境
├── frontend/             # Vue3 前端
├── start-all.sh          # 一键启动脚本
├── start-backend.py      # 启动后端（守护进程）
├── start-frontend.py     # 启动前端（守护进程）
└── README.md
```

## 环境准备

1. 确保已安装 Python 3.12+ 和 Node.js 16+
2. 申请 Moonshot API Key：[https://platform.moonshot.cn/](https://platform.moonshot.cn/)
3. 后端目录创建 `.env` 文件：

```env
# Kimi API 配置（必须）
MOONSHOT_API_KEY=sk-你的APIKey
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=moonshot-v1-32k-vision-preview

# 数据库与上传目录
DATABASE_URL=sqlite:///./essay_correction.db
UPLOAD_DIR=./uploads

# 后端端口（避免与 8000 冲突）
HOST=0.0.0.0
PORT=8001

# 百度 OCR 配置（可选）
BAIDU_OCR_APP_ID=你的AppID
BAIDU_OCR_API_KEY=你的APIKey
BAIDU_OCR_SECRET_KEY=你的SecretKey

# 腾讯 OCR 配置（可选）
TENCENT_OCR_SECRET_ID=你的SecretID
TENCENT_OCR_SECRET_KEY=你的SecretKey

# 批量批改目录
BATCH_SCAN_DIR=/mnt/hgfs/vm_share/workspace/essay-correction
```

> `.env` 文件已加入 `.gitignore`，请勿提交到 Git。

## 快速启动

### 方式一：一键启动

```bash
cd essay-correction
bash start-all.sh
```

### 方式二：手动启动

```bash
# 后端
cd essay-correction
python3 start-backend.py

# 前端（新终端）
cd essay-correction
python3 start-frontend.py
```

## 访问系统

- 前端页面：[http://localhost:5173](http://localhost:5173)
- 后端 API 文档：[http://localhost:8001/docs](http://localhost:8001/docs)

## 批量批改使用说明

批量批改默认扫描目录：

```
/mnt/hgfs/vm_share/workspace/essay-correction/YYYYMMDD/
```

图片命名规则：

```
人名_作文题目.jpg
```

例如：

```
张三_我的家乡.jpg
李四_难忘的一天.jpg
```

系统会：
1. 根据文件名解析出人名和作文题目
2. 自动查找或创建学生
3. 复制图片到 uploads 目录
4. 异步进行 OCR 识别和作文批改

## 百度 OCR 对接说明

### 1. 注册并开通服务

- 访问 [百度智能云](https://cloud.baidu.com/)
- 注册/登录账号
- 进入"文字识别"产品页
- 开通"通用文字识别"或"手写文字识别"服务

### 2. 创建应用获取凭证

进入 [百度智能云控制台](https://console.bce.baidu.com/)：

1. 点击"创建应用"
2. 填写应用名称
3. 勾选"文字识别"相关接口
4. 创建完成后获取：
   - `AppID`
   - `API Key`
   - `Secret Key`

### 3. 配置到系统

将获取的凭证填入 `backend/.env`：

```env
BAIDU_OCR_APP_ID=12345678
BAIDU_OCR_API_KEY=你的APIKey
BAIDU_OCR_SECRET_KEY=你的SecretKey
```

### 4. 选择百度 OCR

上传作文或批量批改时，在"OCR 识别引擎"中选择"百度手写 OCR"即可。

### 5. 接口说明

代码中对接的是百度手写识别接口：

```
POST https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token=xxx
```

请求参数：

```json
{
  "image": "base64编码的图片"
}
```

返回示例：

```json
{
  "words_result": [
    {"words": "第一行文字"},
    {"words": "第二行文字"}
  ],
  "words_result_num": 2
}
```

系统会将所有 `words` 按行拼接成完整文本。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/students` | 新增学生 |
| GET | `/api/students` | 学生列表 |
| PUT | `/api/students/{id}` | 修改学生 |
| DELETE | `/api/students/{id}` | 删除学生 |
| POST | `/api/essays/upload` | 上传作文图片 |
| POST | `/api/essays/{id}/correct` | 触发异步批改 |
| GET | `/api/essays/{id}/status` | 查询批改状态 |
| GET | `/api/essays/{id}` | 获取批改详情 |
| GET | `/api/essays/{id}/pdf` | 导出 PDF 报告 |
| GET | `/api/essays` | 历史记录列表 |
| POST | `/api/batch/scan?date=YYYYMMDD` | 扫描指定日期目录 |
| POST | `/api/batch/today` | 扫描当天目录 |
| GET | `/api/batch/tasks/{task_id}` | 查询批量任务进度 |

## 注意事项

- 后端默认使用 8001 端口，避免与 changying 项目的 8000 端口冲突
- 异步任务状态保存在内存中，重启服务后任务状态会丢失
- PDF 中文字体依赖系统字体（Noto Sans CJK / wqy-zenhei）
- 手写识别准确率与图片清晰度、OCR 引擎能力相关
- 系统默认编码为 UTF-8，支持中文

## 后续优化方向

1. 接入更多 OCR 引擎
2. 支持作文原图批注高亮
3. 定时自动扫描当天目录
4. 多用户登录与权限管理
