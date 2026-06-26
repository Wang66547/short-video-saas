# AI 视频生成服务配置指南

## 概述

平台集成了多种 AI 服务，包括：
- 🎬 **AI 视频生成**：即梦（Jimeng）、可灵（Kling）
- ✍️ **AI 文案改写**：兼容 OpenAI 格式的大模型 API
- 🗣️ **AI 语音合成（TTS）**：阿里云、腾讯云
- 🔊 **AI 语音识别（Whisper）**：本地部署 Whisper 模型

---

## 一、AI 视频生成

### 1.1 即梦（Jimeng）- 推荐

即梦是字节跳动旗下的 AI 视频生成平台，效果较好。

**申请地址**：https://jimeng.jianying.com/

**配置方法**：

```bash
# 即梦 API Key
JIMENG_API_KEY=你的即梦APIKey
# 即梦 API 地址（默认即可）
JIMENG_BASE_URL=https://api.jimeng.jianying.com/visual/api
# 默认使用即梦
DEFAULT_AI_PLATFORM=jimeng
```

**功能特点**：
- 支持文生视频、图生视频
- 支持分镜脚本生成
- 支持多种画面比例（9:16、16:9、1:1）
- 视频时长：5-30秒

---

### 1.2 可灵（Kling）

可灵是快手旗下的 AI 视频生成平台。

**申请地址**：https://klingai.com/

**配置方法**：

```bash
# 可灵 API Key
KLING_API_KEY=你的可灵APIKey
# 可灵 API 地址（默认即可）
KLING_BASE_URL=https://klingai.com/api
```

**功能特点**：
- 支持文生视频、图生视频
- 运动控制能力强
- 支持多种画面比例

---

### 1.3 视频生成流程

```
用户提交解析记录
        ↓
编辑分镜脚本和文案
        ↓
选择 AI 平台（即梦/可灵）
        ↓
提交生成任务（异步）
        ↓
AI 平台生成视频
        ↓
下载生成的视频
        ↓
裁剪水印/AI标识
        ↓
合成配音和背景音乐
        ↓
生成完成，返回结果
```

---

## 二、AI 文案改写

### 2.1 配置

平台使用兼容 OpenAI 格式的大模型 API 进行文案改写。

```bash
# API 地址（兼容 OpenAI 格式即可）
OPENAI_API_BASE=https://apihub.agnes-ai.com/v1
# API Key
OPENAI_API_KEY=你的APIKey
# 使用的模型
OPENAI_MODEL=agnes-2.0-flash
```

### 2.2 改写模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `synonym` | 同义改写 | 轻微调整，降低重复度 |
| `rewrite` | 深度改写 | 大幅调整句式结构 |
| `style_change` | 风格转换 | 转换为幽默/专业/情感风格 |
| `optimize` | 爆款优化 | 优化开头钩子、节奏感 |

---

## 三、AI 语音合成（TTS）

### 3.1 阿里云语音合成（推荐）

**申请地址**：https://www.aliyun.com/product/dashscope

**配置方法**：

```bash
# 阿里云 DashScope API Key
ALIYUN_TTS_API_KEY=你的APIKey
# 默认使用阿里云
DEFAULT_TTS_PROVIDER=ali
```

**可用音色**：

| 音色标识 | 名称 | 性别 | 适用场景 |
|----------|------|------|----------|
| `female_warm` | 温暖女声 | 女 | 情感类内容 |
| `female_clear` | 清新女声 | 女 | 知识科普 |
| `male_deep` | 磁性男声 | 男 | 影视解说 |
| `male_youth` | 阳光男声 | 男 | 运动健身 |
| `female_narrator` | 解说女声 | 女 | 专业解说 |
| `male_narrator` | 解说男声 | 男 | 沉稳解说 |

---

### 3.2 腾讯云语音合成

**申请地址**：https://cloud.tencent.com/product/tts

**配置方法**：

```bash
# 腾讯云 SecretId
TENCENT_TTS_SECRET_ID=你的SecretId
# 腾讯云 SecretKey
TENCENT_TTS_SECRET_KEY=你的SecretKey
```

---

### 3.3 语音合成参数

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| `speed` | 0.5 - 2.0 | 1.0 | 语速 |
| `pitch` | -500 - 500 | 0 | 音调 |
| `volume` | 0 - 100 | 50 | 音量 |

---

## 四、AI 语音识别（Whisper）

### 4.1 配置

Whisper 用于视频语音转文字，解析视频文案。

```bash
# 模型大小: tiny/base/small/medium/large
WHISPER_MODEL=base
# 设备: cpu/cuda
WHISPER_DEVICE=cpu
# 语言: zh/en/auto
WHISPER_LANGUAGE=zh
```

### 4.2 模型选择

| 模型 | 体积 | 速度 | 准确率 | 内存占用 |
|------|------|------|--------|----------|
| `tiny` | ~39MB | 极快 | 较低 | ~1GB |
| `base` | ~74MB | 快 | 一般 | ~1GB |
| `small` | ~244MB | 中 | 较好 | ~2GB |
| `medium` | ~769MB | 慢 | 好 | ~5GB |
| `large` | ~1.5GB | 很慢 | 最好 | ~10GB |

> 💡 **建议**：生产环境建议使用 `base` 或 `small` 模型，平衡速度和准确率。GPU 环境可使用更大的模型。

---

## 五、完整配置示例

### 5.1 基础版（只配置即梦）

```bash
# AI 视频生成
JIMENG_API_KEY=sk-xxxxxxxxxxxxxxxx
DEFAULT_AI_PLATFORM=jimeng

# 文案改写
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo

# 语音合成
ALIYUN_TTS_API_KEY=sk-xxxxxxxxxxxxxxxx
DEFAULT_TTS_PROVIDER=ali

# 语音识别
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
```

### 5.2 完整版（双平台 + 全功能）

```bash
# AI 视频生成
JIMENG_API_KEY=sk-xxxxxxxxxxxxxxxx
KLING_API_KEY=sk-xxxxxxxxxxxxxxxx
DEFAULT_AI_PLATFORM=jimeng

# 文案改写
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# 语音合成
ALIYUN_TTS_API_KEY=sk-xxxxxxxxxxxxxxxx
TENCENT_TTS_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_TTS_SECRET_KEY=xxxxxxxxxxxxxxxx
DEFAULT_TTS_PROVIDER=ali

# 语音识别
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_LANGUAGE=zh
```

---

## 六、Railway 部署配置

在 Railway 项目的 **Variables** 页面添加以下环境变量：

### 必选配置（视频生成）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `JIMENG_API_KEY` | 即梦 API Key | `sk-abc123...` |
| `OPENAI_API_KEY` | 大模型 API Key | `sk-xyz789...` |
| `ALIYUN_TTS_API_KEY` | 阿里云 TTS Key | `sk-tts456...` |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `KLING_API_KEY` | 可灵 API Key | - |
| `DEFAULT_AI_PLATFORM` | 默认 AI 平台 | `jimeng` |
| `WHISPER_MODEL` | Whisper 模型大小 | `base` |
| `WHISPER_DEVICE` | Whisper 运行设备 | `cpu` |
| `OPENAI_MODEL` | 文案改写模型 | `agnes-2.0-flash` |
| `DEFAULT_TTS_PROVIDER` | 默认 TTS 服务商 | `ali` |

---

## 七、费用说明

### 7.1 即梦定价

| 套餐 | 价格 | 视频数 |
|------|------|--------|
| 免费版 | 0元 | 约10次/天 |
| 基础版 | ~99元/月 | 约500次 |
| 专业版 | ~299元/月 | 约2000次 |

> 具体价格以官方为准：https://jimeng.jianying.com/

### 7.2 大模型文案改写

按 token 计费，通常 1000 token ≈ 700 中文字符。
- GPT-3.5 级别：约 0.002 美元 / 1K token
- GPT-4 级别：约 0.03 美元 / 1K token

### 7.3 语音合成

- 阿里云：约 0.02 元 / 次（100字以内）
- 腾讯云：约 0.02 元 / 次

---

## 八、常见问题

### Q: 没有配置 AI 服务还能使用吗？

A: 可以。基础功能（视频解析、会员管理等）不受影响。
- 文案改写：会返回模拟结果，并标记 `is_mock: true`
- 视频生成：会失败并提示未配置 AI 服务
- 语音合成：会失败并提示错误

### Q: 即梦和可灵哪个效果更好？

A: 各有优势：
- **即梦**：人物效果好，画面稳定，适合剧情类
- **可灵**：运动效果好，适合动作、风景类

建议都申请，让用户选择。

### Q: Whisper 首次启动很慢？

A: 是的，首次使用会自动下载模型文件。建议在配置好后先触发一次解析，预热模型。

### Q: 视频生成失败怎么办？

A: 检查：
1. API Key 是否正确
2. 账户余额是否充足
3. 网络是否能访问 API 地址
4. 查看后端日志获取详细错误信息

### Q: 如何降低 AI 成本？

A: 优化建议：
1. 文案改写：使用较小的模型，控制输入长度
2. 视频生成：合理设置每日免费额度
3. 语音合成：缓存常用音频，避免重复生成
4. 会员套餐：按量计费的可以考虑包月套餐

---

## 九、API 接口说明

### 文案改写

```
POST /api/generate/rewrite-script
Content-Type: application/json

{
  "script": "要改写的文案内容",
  "mode": "synonym",
  "temperature": 0.7
}
```

### 语音合成

```
POST /api/generate/synthesize-voice
Content-Type: application/json

{
  "text": "要合成的文本",
  "voice": "female_warm",
  "speed": 1.0
}
```

### 创建生成任务

```
POST /api/generate/create
Content-Type: application/json

{
  "parse_id": 1,
  "generate_mode": "ai_generate",
  "ai_platform": "jimeng",
  "aspect_ratio": "9:16",
  "edited_script": "编辑后的文案",
  "edited_scenes": [...]
}
```
