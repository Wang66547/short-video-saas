# 项目上下文：爆款短视频复刻SaaS平台

## 项目概述
基于 FastAPI + Vue 3 的短视频复刻工具SaaS平台，提供视频解析、生成、会员付费等功能。

## 技术栈
- 后端：Python 3.10 + FastAPI + SQLAlchemy 2.0 + MySQL 8.0 + Redis 7.0 + Celery
- 前端：Vue 3 + Vite + Element Plus + Pinia
- 视频：FFmpeg + faster-whisper + PaddleOCR
- 支付：微信支付V3 + 支付宝
- 安全：JWT认证 + bcrypt密码哈希 + CORS + 限流

## 核心模块
1. 用户认证（JWT + 微信登录）
2. 会员体系（套餐/卡密/积分/每日限额）
3. 视频解析（Celery异步任务）
4. 视频生成（Celery异步任务）
5. 支付系统（微信/支付宝）
6. 管理后台（数据统计/用户/订单/卡密管理）

## 数据库设计
- users: 用户表（手机号/微信openid/会员等级/积分）
- membership_plans: 会员套餐（月卡/季卡/年卡/终身卡/次卡）
- orders: 订单表
- parse_records: 解析记录表
- generate_records: 生成记录表
- admins: 管理员表
- card_keys: 卡密表
- operation_logs: 操作日志表

## 目录结构
backend/app/
├── core/          # 配置/限流/安全/中间件/异常
├── db/            # 数据库会话管理
├── models/        # SQLAlchemy 数据模型
├── schemas/       # Pydantic 请求/响应模型
├── api/           # API 路由
├── services/      # 业务逻辑层
├── tasks/         # Celery 异步任务
└── utils/         # 工具函数

## 权限控制
- 免费用户：每日3次解析，1次生成
- 基础会员：每日10次解析，5次生成
- 高级会员：每日50次解析，20次生成

## 短信服务
- 阿里云短信接口预留
- 开发环境返回测试验证码
- 生产环境配置环境变量接入

## 支付体系
- 微信支付V3：Native支付（二维码）、JSAPI支付（公众号/小程序）
- 支付宝：手机网站支付（WAP）
- 卡密兑换：管理员批量生成，用户输入兑换
- 订单管理：创建、查询、列表、回调处理

## 视频拆解功能
- FFmpeg视频基础信息提取（时长/分辨率/帧率/码率）
- faster-whisper语音转写
- PaddleOCR字幕识别
- 帧差法分镜检测
- 人声/BGM分离
- 水印位置检测
- 解析结果结构化返回

## AI视频生成
- 即梦(Jimeng)API集成
- 可灵(Kling)API集成
- 本地FFmpeg合成模式
- 去水印/去字幕/去AI标识
