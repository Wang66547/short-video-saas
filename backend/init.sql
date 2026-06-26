-- 爆款短视频复刻SaaS平台 - 数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS short_video_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE short_video_saas;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    wechat_openid VARCHAR(64) UNIQUE,
    nickname VARCHAR(50) DEFAULT '',
    avatar VARCHAR(500) DEFAULT '',
    password_hash VARCHAR(255),
    membership_level VARCHAR(20) DEFAULT 'free',
    membership_expire_at DATETIME,
    remaining_credits BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    last_login_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_status (status, membership_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 会员套餐表
CREATE TABLE IF NOT EXISTS membership_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    daily_parse_count INT DEFAULT 10,
    daily_generate_count INT DEFAULT 5,
    support_hd_export BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    is_active INT DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) UNIQUE NOT NULL,
    order_type VARCHAR(20) DEFAULT 'membership',
    user_id INT NOT NULL,
    plan_id INT,
    amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    expired_at DATETIME,
    payment_method VARCHAR(20),
    payment_status VARCHAR(20) DEFAULT 'pending',
    paid_at DATETIME,
    callback_data TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id),
    INDEX idx_order_user (user_id, created_at),
    INDEX idx_order_status (payment_status),
    INDEX idx_order_expired (expired_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 解析记录表
CREATE TABLE IF NOT EXISTS parse_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    video_url VARCHAR(1000) NOT NULL,
    result_json TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    duration FLOAT DEFAULT 0,
    error_message VARCHAR(500) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_parse_user (user_id, created_at),
    INDEX idx_parse_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 生成记录表
CREATE TABLE IF NOT EXISTS generate_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    parse_id INT NOT NULL,
    generate_mode VARCHAR(20) DEFAULT 'ai_generate',
    edited_script TEXT DEFAULT '',
    edited_scenes TEXT DEFAULT '[]',
    voice_tone VARCHAR(50) DEFAULT '',
    replace_materials TEXT DEFAULT '[]',
    aspect_ratio VARCHAR(10) DEFAULT '9:16',
    ai_platform VARCHAR(20) DEFAULT 'jimeng',
    generation_params TEXT DEFAULT '{}',
    output_video_url VARCHAR(1000) DEFAULT '',
    output_local_path VARCHAR(500) DEFAULT '',
    output_thumbnail VARCHAR(1000) DEFAULT '',
    output_duration FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    cost_credits INT DEFAULT 5,
    error_message VARCHAR(500) DEFAULT '',
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parse_id) REFERENCES parse_records(id),
    INDEX idx_gen_user (user_id, created_at),
    INDEX idx_gen_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 管理员表
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    real_name VARCHAR(50) DEFAULT '',
    is_active INT DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 卡密表
CREATE TABLE IF NOT EXISTS card_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_code VARCHAR(50) UNIQUE NOT NULL,
    plan_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'unused',
    used_by_user_id INT,
    used_at DATETIME,
    expires_at DATETIME,
    batch_name VARCHAR(100) DEFAULT '',
    remark VARCHAR(200) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id),
    FOREIGN KEY (used_by_user_id) REFERENCES users(id),
    INDEX idx_card_status (status),
    INDEX idx_card_batch (batch_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 卡密批次表
CREATE TABLE IF NOT EXISTS card_key_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_name VARCHAR(100) UNIQUE NOT NULL,
    plan_id INT NOT NULL,
    total_count INT DEFAULT 0,
    used_count INT DEFAULT 0,
    remark VARCHAR(500) DEFAULT '',
    created_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id),
    INDEX idx_batch_plan (plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    operator_id INT,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INT,
    detail TEXT DEFAULT '',
    ip_address VARCHAR(50) DEFAULT '',
    status VARCHAR(20) DEFAULT 'success',
    error_message VARCHAR(500) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_op_user (user_id, created_at),
    INDEX idx_op_action (action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入默认会员套餐
INSERT INTO membership_plans (name, plan_type, price, original_price, daily_parse_count, daily_generate_count, support_hd_export, sort_order, is_active) VALUES
('免费版', 'free', 0, 0, 3, 1, FALSE, 0, 1),
('基础会员', 'basic', 29.9, 49.9, 10, 5, FALSE, 1, 1),
('高级会员', 'premium', 99.9, 199.9, 50, 20, TRUE, 2, 1),
('终身会员', 'lifetime', 999.9, 1999.9, 999, 999, TRUE, 3, 1);

-- 系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    description VARCHAR(255) DEFAULT '',
    is_public INT DEFAULT 0,
    is_sensitive INT DEFAULT 0,
    updated_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES admins(id),
    INDEX idx_sys_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 插入默认管理员账号（密码: Admin@123，首次登录后请修改）
-- ============================================
INSERT INTO admins (username, password_hash, role, real_name, is_active)
VALUES ('admin', '$2b$12$ViBpRxTk/751WjbpI0nBauCdw/k.WGXafnJ/BeAqoECCQdVwpusaa', 'super_admin', '系统管理员', 1);
