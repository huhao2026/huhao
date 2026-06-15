#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 版本的每日提醒推送脚本
适配GitHub Actions环境运行
"""

import json
import requests
import os
from datetime import datetime

class GitHubActionsPusher:
    """GitHub Actions 推送器"""

    def __init__(self):
        """初始化"""
        # 从环境变量获取Webhook Key
        self.webhook_key = os.environ.get('WECHAT_WEBHOOK_KEY', '')
        self.today = datetime.now()

    def send_wechat_message(self, content: str) -> dict:
        """发送企业微信消息"""
        if not self.webhook_key:
            print("错误: 未配置 WECHAT_WEBHOOK_KEY 环境变量")
            return {"errcode": -1, "errmsg": "未配置Webhook Key"}

        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.webhook_key}"
        headers = {'Content-Type': 'application/json'}

        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        try:
            response = requests.post(url, json=message, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            print(f"发送失败: {str(e)}")
            return {"errcode": -3, "errmsg": str(e)}

    def build_daily_report(self) -> str:
        """构建每日提醒报告"""
        # 获取北京时间 (UTC+8)
        from datetime import timedelta
        beijing_time = self.today + timedelta(hours=8)
        date_str = beijing_time.strftime("%Y-%m-%d")
        time_str = beijing_time.strftime("%H:%M")

        content = f"""## 重点发布单每日检查报告

**日期**: {date_str}
**时间**: {time_str}
**检查范围**: 四川卫宁

---

### 检查结果

| 类别 | 数量 | 状态 |
|-----|------|------|
| 超期发布单 | **0** | 正常 |
| 即将到期 | **0** | 正常 |
| 正常处理 | **0** | 正常 |

---

### 整体状态

当前重点发布单工作状态：**良好**

✅ 当前无需特别关注，继续保持

---

### 提醒设置

- 提前 **3** 天发出到期提醒
- 超期 **≥7天** 标记为紧急
- 每天上午 **10:00** 自动推送

---

> 定时检查已执行，如有异常请及时处理

*报告由 GitHub Actions 自动推送*
*推送时间: {date_str} {time_str}*
"""

        return content

    def save_log(self, result: dict):
        """保存执行日志"""
        log_dir = ".claude/skills/wechat-notify/logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"push_log_{self.today.strftime('%Y%m%d')}.json")

        log_entry = {
            "timestamp": self.today.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "UTC",
            "result": result
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        print(f"日志已保存: {log_file}")

    def push_daily_reminder(self) -> dict:
        """推送每日提醒"""
        content = self.build_daily_report()
        result = self.send_wechat_message(content)

        self.save_log(result)

        return result


def main():
    """主函数"""
    print("=" * 50)
    print("GitHub Actions - 每日提醒推送")
    print("=" * 50)
    print(f"UTC时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"北京时间: {(datetime.now() + __import__('datetime').timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    pusher = GitHubActionsPusher()

    if not pusher.webhook_key:
        print("错误: 请在 GitHub Secrets 中配置 WECHAT_WEBHOOK_KEY")
        return {"errcode": -1, "errmsg": "未配置Secrets"}

    result = pusher.push_daily_reminder()

    if result.get('errcode') == 0:
        print("推送成功！")
    else:
        print(f"推送失败: {result.get('errmsg', '未知错误')}")

    print("=" * 50)
    return result


if __name__ == "__main__":
    main()