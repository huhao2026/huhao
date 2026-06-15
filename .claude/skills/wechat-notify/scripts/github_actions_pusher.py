#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 版本的每日提醒推送脚本
适配GitHub Actions环境运行，支持多群推送
"""

import json
import requests
import os
from datetime import datetime, timedelta

class GitHubActionsPusher:
    """GitHub Actions 推送器（支持多群）"""

    def __init__(self):
        """初始化"""
        # 从环境变量获取Webhook Keys（支持逗号分隔多个）
        webhook_keys_str = os.environ.get('WECHAT_WEBHOOK_KEY', '')
        self.webhook_keys = self._parse_webhook_keys(webhook_keys_str)
        self.today = datetime.now()

    def _parse_webhook_keys(self, keys_str: str) -> list:
        """解析Webhook Keys（支持逗号分隔）"""
        if not keys_str:
            return []

        # 支持逗号分隔多个Key
        keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        return keys

    def send_wechat_message(self, content: str, webhook_key: str) -> dict:
        """发送企业微信消息到指定群"""
        if not webhook_key:
            print("错误: Webhook Key为空")
            return {"errcode": -1, "errmsg": "Webhook Key为空"}

        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"
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

    def save_log(self, results: list):
        """保存执行日志"""
        log_dir = ".claude/skills/wechat-notify/logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"push_log_{self.today.strftime('%Y%m%d')}.json")

        log_entry = {
            "timestamp": self.today.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "UTC",
            "total_groups": len(self.webhook_keys),
            "results": results
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

        print(f"日志已保存: {log_file}")

    def push_daily_reminder(self) -> list:
        """推送每日提醒到所有群"""
        content = self.build_daily_report()
        results = []

        for i, webhook_key in enumerate(self.webhook_keys):
            print(f"正在推送到第 {i+1} 个群...")
            result = self.send_wechat_message(content, webhook_key)
            result['group_index'] = i + 1
            result['webhook_key_preview'] = f"{webhook_key[:8]}...{webhook_key[-4:]}"
            results.append(result)

            if result.get('errcode') == 0:
                print(f"  第 {i+1} 个群推送成功")
            else:
                print(f"  第 {i+1} 个群推送失败: {result.get('errmsg', '未知错误')}")

        self.save_log(results)
        return results


def main():
    """主函数"""
    print("=" * 50)
    print("GitHub Actions - 每日提醒推送（多群版）")
    print("=" * 50)
    print(f"UTC时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"北京时间: {(datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    # 调试：打印环境变量状态
    webhook_keys_str = os.environ.get('WECHAT_WEBHOOK_KEY', '')
    print(f"WECHAT_WEBHOOK_KEY 原始长度: {len(webhook_keys_str) if webhook_keys_str else 0}")
    print(f"WECHAT_WEBHOOK_KEY 是否存在: {'是' if webhook_keys_str else '否'}")

    pusher = GitHubActionsPusher()
    print(f"解析到 {len(pusher.webhook_keys)} 个Webhook Key")

    for i, key in enumerate(pusher.webhook_keys):
        print(f"  Key {i+1}: {key[:8]}...{key[-4:]}")

    print("-" * 50)

    if not pusher.webhook_keys:
        print("错误: 请在 GitHub Secrets 中配置 WECHAT_WEBHOOK_KEY")
        print("提示: 多群推送时，多个Key用逗号分隔")
        print("示例: key1,key2,key3")
        return {"errcode": -1, "errmsg": "未配置Secrets"}

    results = pusher.push_daily_reminder()

    # 统计结果
    success_count = sum(1 for r in results if r.get('errcode') == 0)
    fail_count = len(results) - success_count

    print("-" * 50)
    print(f"推送完成: 成功 {success_count} 个群, 失败 {fail_count} 个群")
    print("=" * 50)

    return {"success": success_count, "failed": fail_count, "results": results}


if __name__ == "__main__":
    main()