from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime, timedelta
import glob

app = Flask(__name__)

class LogWebViewer:
    def __init__(self):
        self.logs_dir = "daily_logs"
        
    def get_log_files(self, days=7):
        """获取最近几天的日志文件"""
        files = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            file_path = f"{self.logs_dir}/requests_{date}.json"
            if os.path.exists(file_path):
                files.append({
                    'date': date,
                    'path': file_path
                })
        return files
        
    def load_log_data(self, date=None):
        """加载指定日期的日志数据"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        file_path = f"{self.logs_dir}/requests_{date}.json"
        
        if not os.path.exists(file_path):
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [json.loads(line.strip()) for line in f if line.strip()]
        except Exception as e:
            print(f"读取日志文件失败: {e}")
            return []
            
    def get_detailed_stats(self, date=None):
        """获取详细统计信息"""
        logs = self.load_log_data(date)
        if not logs:
            return None
            
        stats = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_requests': len(logs),
            'successful': len([l for l in logs if l.get('success', True)]),
            'failed': len([l for l in logs if not l.get('success', True)]),
            'users': {},
            'requests_by_type': {'chart': [], 'prediction': [], 'analysis': []},
            'all_requests': logs
        }
        
        # 统计用户请求
        for log in logs:
            username = log.get('username', 'Unknown')
            if username not in stats['users']:
                stats['users'][username] = {
                    'total': 0,
                    'chart': [],
                    'prediction': [],
                    'analysis': []
                }
            
            stats['users'][username]['total'] += 1
            request_type = log.get('request_type', 'unknown')
            content = log.get('content', '')
            
            if request_type in stats['users'][username]:
                stats['users'][username][request_type].append({
                    'content': content,
                    'timestamp': log.get('timestamp'),
                    'success': log.get('success', True)
                })
                
            # 按类型分类请求
            if request_type in stats['requests_by_type']:
                stats['requests_by_type'][request_type].append({
                    'username': username,
                    'content': content,
                    'timestamp': log.get('timestamp'),
                    'success': log.get('success', True),
                    'channel': log.get('channel_name', ''),
                    'guild': log.get('guild_name', '')
                })
                
        return stats

# 创建全局实例
log_viewer = LogWebViewer()

@app.route('/')
def index():
    """主页 - 显示最近7天的日志"""
    available_dates = log_viewer.get_log_files(7)
    today_stats = log_viewer.get_detailed_stats()
    
    return render_template('log_viewer.html', 
                         dates=available_dates, 
                         today_stats=today_stats)

@app.route('/api/logs/<date>')
def get_logs_api(date):
    """API接口 - 获取指定日期的详细日志"""
    stats = log_viewer.get_detailed_stats(date)
    return jsonify(stats)

@app.route('/date/<date>')
def view_date(date):
    """查看指定日期的日志"""
    stats = log_viewer.get_detailed_stats(date)
    available_dates = log_viewer.get_log_files(7)
    
    return render_template('log_viewer.html', 
                         dates=available_dates, 
                         today_stats=stats,
                         selected_date=date)

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs("daily_logs", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)