"""
社交媒体多平台发布脚本
支持Reddit、Medium、X(Twitter)的内容发布和格式改写
"""

import os
import json
import re
from typing import Dict, List, Optional

# 平台发布器基类
class PlatformPublisher:
    """平台发布器基类"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
    
    def format_content(self, content: Dict) -> Dict:
        """格式化内容供平台使用"""
        raise NotImplementedError
    
    def publish(self, content: Dict) -> Dict:
        """发布内容"""
        raise NotImplementedError


class RedditPublisher(PlatformPublisher):
    """Reddit发布器"""
    
    def format_content(self, content: Dict) -> Dict:
        """Reddit格式：短标题+正文，添加互动元素"""
        title = content.get('title', '')
        body = content.get('body', '')
        
        # 标题优化
        if len(title) > 300:
            title = title[:297] + '...'
        
        # 添加互动性结尾
        if body and not body.endswith(('?', '!', '.')):
            body += '。有什么想法欢迎评论！'
        
        return {
            'title': title,
            'text': body,
            'subreddit': content.get('subreddit', 'technology'),
            'nsfw': content.get('nsfw', False)
        }
    
    def publish(self, content: Dict) -> Dict:
        """发布到Reddit"""
        formatted = self.format_content(content)
        
        # TODO: 实现实际的Reddit API调用
        # 需要使用praw库或直接调用REST API
        
        return {
            'platform': 'reddit',
            'status': 'success',
            'url': f"https://reddit.com/r/{formatted['subreddit']}/comments/placeholder",
            'formatted': formatted
        }


class MediumPublisher(PlatformPublisher):
    """Medium发布器"""
    
    def format_content(self, content: Dict) -> Dict:
        """Medium格式：保持长文结构，添加标签"""
        title = content.get('title', '')
        body = content.get('body', '')
        
        # 转换为Medium支持的格式
        # Medium支持Markdown
        
        # 添加标签
        tags = content.get('tags', ['tech', 'ai'])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')][:5]
        
        return {
            'title': title,
            'content': body,
            'tags': tags,
            'canonicalUrl': content.get('url', ''),
            'publishStatus': 'public'
        }
    
    def publish(self, content: Dict) -> Dict:
        """发布到Medium"""
        formatted = self.format_content(content)
        
        # TODO: 实现实际的Medium API调用
        
        return {
            'platform': 'medium',
            'status': 'success',
            'url': 'https://medium.com/@user/placeholder',
            'formatted': formatted
        }


class XPublisher(PlatformPublisher):
    """X(Twitter)发布器"""
    
    def format_content(self, content: Dict) -> Dict:
        """X格式：拆分为推文线程，每条<280字符"""
        title = content.get('title', '')
        body = content.get('body', '')
        
        tweets = []
        
        # 第一条：标题/简介
        first_tweet = title[:277]
        if len(title) > 277:
            first_tweet = title[:274] + '...'
        tweets.append(first_tweet)
        
        # 拆分正文
        max_length = 280
        # 保留空间给序号
        remaining_body = body.strip()
        
        while remaining_body:
            # 估算剩余内容
            if len(remaining_body) <= max_length - 10:
                tweets.append(remaining_body)
                break
            
            # 找到合适的断点
            chunk = remaining_body[:max_length - 10]
            last_period = max(chunk.rfind('。'), chunk.rfind('.'), chunk.rfind(' '))
            
            if last_period > max_length // 2:
                tweets.append(chunk[:last_period + 1])
                remaining_body = remaining_body[last_period + 1:]
            else:
                tweets.append(chunk)
                remaining_body = remaining_body[max_length - 10:]
        
        # 添加话题标签
        tags = content.get('tags', [])
        if tags:
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            tag_text = ' '.join([f'#{t}' for t in tags[:3]])
            if tweets:
                tweets[-1] = tweets[-1] + ' ' + tag_text
        
        return {
            'tweets': tweets,
            'thread': True
        }
    
    def publish(self, content: Dict) -> Dict:
        """发布到X"""
        formatted = self.format_content(content)
        
        # TODO: 实现实际的Twitter API调用
        
        return {
            'platform': 'x',
            'status': 'success',
            'tweet_count': len(formatted['tweets']),
            'urls': [f'https://x.com/user/status/{i}' for i in range(len(formatted['tweets']))],
            'formatted': formatted
        }


class SocialMediaPublisher:
    """社交媒体发布管理器"""
    
    def __init__(self):
        self.publishers = {
            'reddit': RedditPublisher(self._get_credentials('reddit')),
            'medium': MediumPublisher(self._get_credentials('medium')),
            'x': XPublisher(self._get_credentials('x'))
        }
    
    def _get_credentials(self, platform: str) -> Dict[str, str]:
        """获取平台凭证"""
        # 从环境变量读取
        creds = {}
        if platform == 'reddit':
            creds = {
                'client_id': os.getenv('REDDIT_CLIENT_ID'),
                'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'user_agent': os.getenv('REDDIT_USER_AGENT', 'SocialMediaPublisher/1.0')
            }
        elif platform == 'medium':
            creds = {
                'token': os.getenv('MEDIUM_INTEGRATION_TOKEN')
            }
        elif platform == 'x':
            creds = {
                'api_key': os.getenv('TWITTER_API_KEY'),
                'api_secret': os.getenv('TWITTER_API_SECRET'),
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
                'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            }
        return creds
    
    def publish(self, content: Dict, platforms: List[str]) -> Dict:
        """发布内容到指定平台
        
        Args:
            content: 包含title, body, tags等的内容
            platforms: 目标平台列表 ['reddit', 'medium', 'x']
        
        Returns:
            各平台的发布结果
        """
        results = {}
        
        for platform in platforms:
            if platform in self.publishers:
                try:
                    result = self.publishers[platform].publish(content)
                    results[platform] = result
                except Exception as e:
                    results[platform] = {
                        'platform': platform,
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                results[platform] = {
                    'platform': platform,
                    'status': 'error',
                    'error': f'Unknown platform: {platform}'
                }
        
        return results
    
    def format_only(self, content: Dict, platform: str) -> Dict:
        """仅格式化内容，不发布"""
        if platform in self.publishers:
            return self.publishers[platform].format_content(content)
        return {}


# CLI入口
if __name__ == '__main__':
    import sys
    
    # 示例用法
    sample_content = {
        'title': 'AI硬件的未来发展',
        'body': '随着AI技术的快速发展，专用AI硬件正在成为新的趋势。从Google的TPU到各种AI芯片，硬件创新正在推动AI能力的边界...',
        'tags': ['AI', '硬件', 'Tech'],
        'subreddit': 'technology'
    }
    
    publisher = SocialMediaPublisher()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--format-only':
        platform = sys.argv[2] if len(sys.argv) > 2 else 'x'
        formatted = publisher.format_only(sample_content, platform)
        print(json.dumps(formatted, ensure_ascii=False, indent=2))
    else:
        results = publisher.publish(sample_content, ['reddit', 'medium', 'x'])
        print(json.dumps(results, ensure_ascii=False, indent=2))
