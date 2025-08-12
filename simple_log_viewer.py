from flask import Flask
import json
import os
import subprocess
import psutil
from datetime import datetime, timedelta

app = Flask(__name__)

def get_bot_status():
    """获取机器人服务状态"""
    status = {
        'discord_bot': False,
        'log_viewer': True,  # 当前服务运行中
        'database': False,
        'system_info': {}
    }
    
    try:
        # 检查Discord机器人进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'simple_bot.py' in cmdline or 'bot.py' in cmdline:
                    status['discord_bot'] = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 检查数据库连接
        try:
            import psycopg2
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                conn = psycopg2.connect(db_url)
                conn.close()
                status['database'] = True
        except:
            pass
            
        # 系统信息
        status['system_info'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
    except Exception as e:
        print(f"获取状态失败: {e}")
    
    return status

def load_log_data(date=None):
    """加载指定日期的日志数据"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
        
    file_path = f"daily_logs/requests_{date}.json"
    
    if not os.path.exists(file_path):
        return []
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
                
            # 尝试解析JSON数组格式
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果不是数组，尝试按行解析
                logs = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return logs
    except Exception as e:
        print(f"读取日志文件失败: {e}")
        return []

def get_available_dates(days=7):
    """获取最近几天的日志文件"""
    dates = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        file_path = f"daily_logs/requests_{date}.json"
        if os.path.exists(file_path):
            dates.append(date)
    return dates

@app.route('/api/status')
def get_status():
    """获取服务状态API"""
    from flask import jsonify
    try:
        status = get_bot_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'discord_bot': False,
            'log_viewer': True,
            'database': False,
            'system_info': {'cpu_percent': 0, 'memory_percent': 0, 'disk_percent': 0},
            'error': str(e)
        })

@app.route('/')
def index():
    """主页"""
    return show_date()

@app.route('/date/<date>')
def show_date(date=None):
    """显示指定日期的日志"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    logs = load_log_data(date)
    available_dates = get_available_dates(7)
    bot_status = get_bot_status()
    
    # 生成HTML
    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Discord Bot 详细日志</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: #007bff;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .status-bar {{
                margin-top: 15px; 
                padding: 10px; 
                background: rgba(255,255,255,0.1); 
                border-radius: 5px;
                display: flex; 
                gap: 20px; 
                justify-content: center; 
                flex-wrap: wrap;
            }}
            .status-bar span {{
                font-size: 14px;
            }}
            .date-nav {{
                padding: 15px;
                background: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }}
            .date-btn {{
                display: inline-block;
                padding: 8px 16px;
                margin: 5px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            .date-btn.active {{
                background: #28a745;
            }}
            .stats {{
                padding: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #007bff;
            }}
            .log-section {{
                padding: 20px;
            }}
            .user-block {{
                margin-bottom: 30px;
                background: #f8f9fa;
                border-radius: 6px;
                overflow: hidden;
            }}
            .user-header {{
                background: #e9ecef;
                padding: 15px;
                font-weight: bold;
            }}
            .request-item {{
                padding: 10px 15px;
                border-bottom: 1px solid #ddd;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .request-item:last-child {{
                border-bottom: none;
            }}
            .type-badge {{
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-width: 60px;
                text-align: center;
            }}
            .type-chart {{ background: #e3f2fd; color: #1565c0; }}
            .type-prediction {{ background: #f3e5f5; color: #7b1fa2; }}
            .type-analysis {{ background: #fff3e0; color: #ef6c00; }}
            .status {{
                font-size: 16px;
            }}
            .success {{ color: #28a745; }}
            .failed {{ color: #dc3545; }}
            .time {{
                font-size: 12px;
                color: #666;
            }}
            .content {{
                flex: 1;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Discord Bot 详细日志</h1>
                <p>用户请求详细记录与统计分析</p>
                <div class="status-bar">
                    <span id="discord-status">🤖 Discord Bot: <span style="color: #ffc107;">检查中...</span></span>
                    <span id="db-status">🗄️ 数据库: <span style="color: #ffc107;">检查中...</span></span>
                    <span id="log-status">📊 日志查看器: <span style="color: #28a745;">运行中</span></span>
                    <span id="system-info">💻 系统: <span style="color: #ffc107;">检查中...</span></span>
                </div>
            </div>
            
            <div class="date-nav">
                <strong>选择日期：</strong>
    '''
    
    for available_date in available_dates:
        active_class = 'active' if available_date == date else ''
        html += f'<a href="/date/{available_date}" class="date-btn {active_class}">{available_date}</a>'
    
    if not logs:
        html += '''
            </div>
            <div style="padding: 40px; text-align: center; color: #666;">
                <h3>暂无数据</h3>
                <p>选择的日期没有找到日志记录</p>
            </div>
        </div>
    </body>
    </html>
        '''
        return html
    
    # 统计信息
    total_requests = len(logs)
    successful = len([l for l in logs if l.get('success', True)])
    failed = total_requests - successful
    success_rate = (successful / total_requests * 100) if total_requests > 0 else 0
    
    # 按用户分组
    users = {}
    for log in logs:
        username = log.get('username', 'Unknown')
        if username not in users:
            users[username] = []
        users[username].append(log)
    
    html += f'''
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>📈 总请求数</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #007bff;">{total_requests}</div>
                </div>
                <div class="stat-card">
                    <h3>✅ 成功请求</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #28a745;">{successful}</div>
                </div>
                <div class="stat-card">
                    <h3>❌ 失败请求</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #dc3545;">{failed}</div>
                </div>
                <div class="stat-card">
                    <h3>👥 活跃用户</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #6f42c1;">{len(users)}</div>
                    <div style="margin-top: 10px;">成功率: {success_rate:.1f}%</div>
                </div>
            </div>
            
            <div class="log-section">
                <h2>👥 用户详细请求记录 ({date})</h2>
    '''
    
    # 显示每个用户的请求
    for username, user_logs in users.items():
        html += f'''
                <div class="user-block">
                    <div class="user-header">
                        {username} (总计 {len(user_logs)} 次请求)
                    </div>
        '''
        
        for log in user_logs:
            request_type = log.get('request_type', 'unknown')
            content = log.get('content', '')
            timestamp = log.get('timestamp', '')
            success = log.get('success', True)
            
            # 格式化时间
            time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
            
            # 类型标签
            type_class = f'type-{request_type}'
            type_emoji = {'chart': '📊', 'prediction': '📈', 'analysis': '🖼️'}.get(request_type, '📋')
            
            # 状态图标
            status_icon = '✅' if success else '❌'
            status_class = 'success' if success else 'failed'
            
            html += f'''
                    <div class="request-item">
                        <span class="type-badge {type_class}">{type_emoji} {request_type}</span>
                        <span class="status {status_class}">{status_icon}</span>
                        <span class="content" title="{content}">{content[:50]}{'...' if len(content) > 50 else ''}</span>
                        <span class="time">{time_str}</span>
                    </div>
            '''
        
        html += '</div>'
    
    html += '''
            </div>
        </div>
        
        <script>
            // 实时更新状态
            function updateStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(status => {
                        const discordStatus = document.getElementById('discord-status');
                        const dbStatus = document.getElementById('db-status');
                        const systemInfo = document.getElementById('system-info');
                        
                        if (discordStatus) {
                            const discordSpan = discordStatus.querySelector('span');
                            if (status.discord_bot) {
                                discordSpan.textContent = '运行中';
                                discordSpan.style.color = '#28a745';
                            } else {
                                discordSpan.textContent = '离线';
                                discordSpan.style.color = '#dc3545';
                            }
                        }
                        
                        if (dbStatus) {
                            const dbSpan = dbStatus.querySelector('span');
                            if (status.database) {
                                dbSpan.textContent = '连接正常';
                                dbSpan.style.color = '#28a745';
                            } else {
                                dbSpan.textContent = '连接失败';
                                dbSpan.style.color = '#dc3545';
                            }
                        }
                        
                        if (systemInfo && status.system_info) {
                            const systemSpan = systemInfo.querySelector('span');
                            const cpu = status.system_info.cpu_percent || 0;
                            const mem = status.system_info.memory_percent || 0;
                            systemSpan.textContent = `CPU ${cpu.toFixed(1)}% | 内存 ${mem.toFixed(1)}%`;
                            systemSpan.style.color = cpu > 80 || mem > 80 ? '#ffc107' : '#28a745';
                        }
                    })
                    .catch(error => console.log('Status update failed:', error));
            }
            
            // 每5秒更新状态
            updateStatus();
            setInterval(updateStatus, 5000);
            
            // 每30秒刷新页面数据
            setTimeout(function() {
                location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs("daily_logs", exist_ok=True)
    
    # 尝试不同的端口，避免冲突
    ports = [5001, 5002, 5003, 8000, 8080]
    port_to_use = 5001
    
    for port in ports:
        try:
            print(f"尝试启动日志查看器在端口 {port}...")
            app.run(host='0.0.0.0', port=port, debug=False)
            port_to_use = port
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"端口 {port} 被占用，尝试下一个...")
                continue
            else:
                raise
    else:
        print("❌ 所有端口都被占用，无法启动日志查看器")