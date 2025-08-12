-- Discord机器人数据库初始化脚本
-- 确保数据库和表正确创建

-- 创建数据库（如果不存在）
-- 注意：在Docker环境中，数据库通常已由docker-compose创建

-- 用户每日请求限制跟踪表
CREATE TABLE IF NOT EXISTS user_request_limits (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    request_date DATE NOT NULL,
    request_count INTEGER DEFAULT 0 NOT NULL,
    last_request_time TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 为查询性能创建索引
CREATE INDEX IF NOT EXISTS idx_user_request_limits_user_id ON user_request_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_request_limits_date ON user_request_limits(request_date);
CREATE INDEX IF NOT EXISTS idx_user_request_limits_user_date ON user_request_limits(user_id, request_date);

-- 豁免用户表
CREATE TABLE IF NOT EXISTS exempt_users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    reason VARCHAR(200),
    added_by VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 为查询性能创建索引
CREATE INDEX IF NOT EXISTS idx_exempt_users_user_id ON exempt_users(user_id);

-- 创建更新触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为两个表创建更新时间触发器
DROP TRIGGER IF EXISTS update_user_request_limits_updated_at ON user_request_limits;
CREATE TRIGGER update_user_request_limits_updated_at
    BEFORE UPDATE ON user_request_limits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_exempt_users_updated_at ON exempt_users;
CREATE TRIGGER update_exempt_users_updated_at
    BEFORE UPDATE ON exempt_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入一些测试数据（可选）
-- INSERT INTO exempt_users (user_id, username, reason, added_by) 
-- VALUES ('admin_user_id', 'AdminUser', '系统管理员', 'system') 
-- ON CONFLICT (user_id) DO NOTHING;

-- 显示表信息
SELECT 'user_request_limits表创建完成' as status;
SELECT 'exempt_users表创建完成' as status;
SELECT 'Discord机器人数据库初始化完成' as final_status;