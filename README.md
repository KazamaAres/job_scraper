# Job Scraper

自动抓取 seek.co.nz 和 nz.skykiwi.com 的职位信息，筛选匹配岗位后通过 Gmail 发送每日推送邮件。

## 项目结构

```
job_scraper/
├── scrapers/
│   ├── __init__.py
│   ├── seek.py        # 抓取 seek.co.nz
│   └── skykiwi.py    # 抓取 nz.skykiwi.com
├── config.py          # 配置（邮箱、关键词等）
├── matcher.py         # 关键词匹配筛选
├── notifier.py        # Gmail 发送 HTML 邮件
├── main.py            # 主程序入口
├── requirements.txt
└── jobs_seen.json     # 自动生成，记录已推送的职位 URL
```

## 配置步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Gmail App Password

Gmail 需要使用「应用专用密码」而非登录密码：

1. 登录 Google 账户 → 安全 → 两步验证（需先开启）
2. 搜索「应用专用密码」→ 生成一个名为 `job_scraper` 的密码
3. 复制生成的 16 位密码

### 3. 编辑 config.py

```python
GMAIL_USER = "your_email@gmail.com"       # 你的 Gmail 地址
GMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"    # 16 位应用专用密码
RECIPIENT_EMAIL = "recipient@example.com"  # 收件人邮箱
SEEK_LOCATION = "Auckland"                 # 搜索地区
```

可按需修改 `SEEK_KEYWORDS` 和 `MATCH_KEYWORDS` 调整搜索和筛选关键词。

## 运行

```bash
python main.py
```

运行日志会同时输出到终端和 `scraper.log` 文件。

## 定时自动运行（Windows 任务计划程序）

1. 打开「任务计划程序」→ 创建基本任务
2. 触发器：每天（例如早上 8:00）
3. 操作：启动程序
   - 程序：`python`
   - 参数：`main.py`
   - 起始位置：`D:\Projects\job_scraper`

或使用 cron（Linux/Mac）：

```bash
0 8 * * * cd /mnt/d/Projects/job_scraper && python main.py
```

## 注意事项

- seek.co.nz 为动态渲染网站，若抓取结果为空可能需要改用 `selenium` 或 Seek 官方 API
- SkyKiwi 的 HTML 结构如有变动需手动更新 `scrapers/skykiwi.py` 中的选择器
- `jobs_seen.json` 记录所有已推送 URL，删除该文件会导致所有职位重新推送
