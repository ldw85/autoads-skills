"""
Archer Affiliates API Client
=============================
安全处理 OAuth2 认证和 API 请求
用户名/密码仅从环境变量读取，不存储在任何文件中
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# Archer API Base URL
ARCHER_API_BASE = "https://api.archeraffiliates.com"


class ArcherAuthError(Exception):
    """认证失败"""
    pass


class ArcherAPIError(Exception):
    """API 请求失败"""
    pass


class ArcherClient:
    """
    Archer Affiliates API 客户端
    
    安全说明：
    - 用户名/密码仅从环境变量读取：ARCHER_USERNAME, ARCHER_PASSWORD
    - Access Token 仅存内存中，不持久化
    - Refresh 时自动重新认证
    """
    
    # 环境变量名（可配置）
    ENV_USERNAME = "ARCHER_USERNAME"
    ENV_PASSWORD = "ARCHER_PASSWORD"
    
    # Token 过期前缓冲时间（秒）
    TOKEN_REFRESH_BUFFER = 300  # 过期前5分钟刷新
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0  # Unix timestamp
        
        # 验证凭证是否存在
        self._username = os.environ.get(self.ENV_USERNAME)
        self._password = os.environ.get(self.ENV_PASSWORD)
        
        if not self._username or not self._password:
            logger.warning(
                f"Archer 凭证未配置。请设置环境变量："
                f" export {self.ENV_USERNAME}=你的用户名"
                f" export {self.ENV_PASSWORD}=你的密码"
            )
    
    @property
    def is_configured(self) -> bool:
        """检查是否已配置凭证"""
        return bool(self._username and self._password)
    
    @property
    def headers(self) -> Dict[str, str]:
        """认证请求头"""
        if not self._access_token:
            self.authenticate()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
    
    def authenticate(self) -> str:
        """
        使用 OAuth2 Password Flow 获取 Access Token
        
        Returns:
            access_token 字符串
            
        Raises:
            ArcherAuthError: 认证失败
        """
        if not self.is_configured:
            raise ArcherAuthError(
                f"未配置 Archer 凭证。请设置环境变量："
                f" {self.ENV_USERNAME} 和 {self.ENV_PASSWORD}"
            )
        
        logger.info("正在向 Archer API 认证...")
        
        try:
            response = requests.post(
                f"{ARCHER_API_BASE}/token",
                data={
                    "username": self._username,
                    "password": self._password,
                    "grant_type": "password"  # OAuth2 password flow
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                
                # Archer API 通常返回的 token 没有明确的 expires_in
                # 默认假设 1 小时有效，刷新缓冲设为 5 分钟
                self._token_expires_at = time.time() + 3600 - self.TOKEN_REFRESH_BUFFER
                
                if not self._access_token:
                    raise ArcherAuthError("Archer API 返回的 access_token 为空")
                
                logger.info("Archer API 认证成功")
                return self._access_token
                
            elif response.status_code == 401:
                raise ArcherAuthError("Archer 用户名或密码错误")
            elif response.status_code == 422:
                raise ArcherAuthError("Archer 请求参数验证失败")
            else:
                raise ArcherAuthError(f"Archer 认证失败: HTTP {response.status_code}")
                
        except requests.RequestException as e:
            raise ArcherAuthError(f"Archer API 连接失败: {e}")
    
    def _ensure_valid_token(self):
        """确保 token 有效，必要时刷新"""
        if not self._access_token or time.time() >= self._token_expires_at:
            self.authenticate()
    
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发起 GET 请求
        
        Args:
            path: API 路径（如 /get_affiliateID）
            params: 查询参数
            
        Returns:
            API 响应的 JSON 数据（任何状态码的响应体都会返回）
        """
        self._ensure_valid_token()
        
        url = f"{ARCHER_API_BASE}{path}"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            # 所有状态码都尝试解析响应体
            try:
                body = response.json()
            except ValueError:
                body = {"raw_text": response.text}
            
            if response.status_code == 200:
                return body
            elif response.status_code == 401:
                # Token 失效，重新认证后重试
                self.authenticate()
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                body = response.json()
                if response.status_code == 200:
                    return body
                # 重试后仍失败，返回响应体（供调用方判断）
                return body
            else:
                # 非200也返回响应体，由调用方判断
                return body
                
        except requests.RequestException as e:
            raise ArcherAPIError(f"API 请求异常: {e}")
    
    def _post(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发起 POST 请求
        
        Args:
            path: API 路径（如 /single_link_data）
            json_data: 请求体数据
            
        Returns:
            API 响应的 JSON 数据
        """
        self._ensure_valid_token()
        
        url = f"{ARCHER_API_BASE}{path}"
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.authenticate()
                response = requests.post(url, headers=self.headers, json=json_data, timeout=30)
                if response.status_code == 200:
                    return response.json()
                raise ArcherAPIError(f"API 请求失败（重试后）: HTTP {response.status_code}")
            else:
                raise ArcherAPIError(f"API 请求失败: HTTP {response.status_code}, Response: {response.text[:500]}")
                
        except requests.RequestException as e:
            raise ArcherAPIError(f"API 请求异常: {e}")
    
    # ─────────────────────────────────────────────
    # API 方法
    # ─────────────────────────────────────────────
    
    def get_affiliate_id(self) -> str:
        """
        获取联盟 ID
        
        Returns:
            affiliate_id 字符串
        """
        data = self._get("/get_affiliateID")
        return data.get("affiliate_id", "")
    
    def get_all_links(self, page: int = 1, limit: int = 100, link_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取所有 Attribution Links
        
        Args:
            page: 页码（默认1）
            limit: 每页数量（最大500）
            link_name: 可选，按链接名称过滤
            
        Returns:
            包含 links 列表的响应
        """
        params = {"page": page, "limit": limit}
        if link_name:
            params["link_name"] = link_name
        return self._get("/get_all_links", params=params)
    
    def get_single_link(self, asin: str) -> Dict[str, Any]:
        """
        获取单个链接（通过 ASIN）
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            链接数据
        """
        return self._get("/get_single_link", params={"asin": asin})
    
    def get_link_data(
        self,
        start_date: str,
        end_date: str,
        sort_order: bool = False,
        sort: int = 0,
        min_clicks: int = 0,
        min_sales: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取链接粒度的效果数据（用于 ROI 计算的核心方法）
        
        Args:
            start_date: 开始日期，格式 YYYYMMDD
            end_date: 结束日期，格式 YYYYMMDD
            sort_order: True=升序, False=降序
            sort: 排序字段
                0 = totalClickThroughs（点击）
                1 = totalAttributedSales14d（销售额）
                2 = totalUnitsSold14d（销量）
                3 = totalattributedTotalPurchases14d
                4 = created_date_time
            min_clicks: 最少点击数
            min_sales: 最少销售额
            limit: 返回数量（最大100）
            
        Returns:
            链接效果数据列表
        """
        params = {
            "startdate": start_date,
            "enddate": end_date,
            "sort_order": sort_order,
            "sort": sort,
            "minclicks": min_clicks,
            "minsales": min_sales,
            "limit": limit
        }
        return self._get("/link_data", params=params)
    
    def get_product_reports_all(
        self,
        start_date: str,
        end_date: str,
        page: int = 1,
        limit: int = 100,
        asin: Optional[str] = None,
        min_clicks: Optional[int] = None,
        min_sales: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取每个 adgroup 每日级别的效果数据
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            page: 页码
            limit: 每页数量
            asin: 可选，按 ASIN 过滤
            min_clicks: 最少点击
            min_sales: 最少销售
            
        Returns:
            产品效果报告
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "limit": limit
        }
        if asin:
            params["asin"] = asin
        if min_clicks is not None:
            params["min_clicks"] = min_clicks
        if min_sales is not None:
            params["min_sales"] = min_sales
            
        return self._get("/product_reports_all", params=params)
    
    def get_aggregated_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取聚合的总效果数据（所有链接汇总）
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            聚合报告
        """
        params = {"startdate": start_date, "enddate": end_date}
        return self._get("/aggregated_report", params=params)
    
    def get_single_asin_data(
        self,
        asin: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        获取单个 ASIN 的所有链接数据
        
        Args:
            asin: Amazon ASIN
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            该 ASIN 下所有链接的数据列表
        """
        payload = {
            "asin": asin,
            "start_date": start_date,
            "end_date": end_date
        }
        return self._post("/single_asin_data", json_data=payload)
    
    def get_single_link_data(
        self,
        link_name: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        获取指定名称的链接数据
        
        Args:
            link_name: 链接名称
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            该名称下所有链接的数据列表
        """
        payload = {
            "link_name": link_name,
            "start_date": start_date,
            "end_date": end_date
        }
        return self._post("/single_link_data", json_data=payload)
    
    def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        brand_id: Optional[str] = None,
        product_available: str = "yes"
    ) -> Dict[str, Any]:
        """获取产品目录"""
        params = {
            "skip": skip,
            "limit": limit,
            "product_available": product_available
        }
        if search:
            params["search"] = search
        if brand_id:
            params["brand_id"] = brand_id
        return self._get("/getproducts", params=params)
    
    def get_brands(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        brand_name: Optional[str] = None,
        brand_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取品牌列表"""
        params = {"skip": skip, "limit": limit}
        if search:
            params["search"] = search
        if brand_name:
            params["brand_name"] = brand_name
        if brand_id:
            params["brand_id"] = brand_id
        return self._get("/brands", params=params)

    def check_product(self, asin: str) -> Dict[str, Any]:
        """
        检查 ASIN 是否在 Archer 联盟目录中有效

        Args:
            asin: Amazon ASIN

        Returns:
            有效时: {"success": "ASIN passed all checks"}
            无效时: {"detail": "ASIN not available for advertising"}
        """
        return self._get("/check_product", params={"asin": asin})

    def is_product_available(self, asin: str) -> bool:
        """
        检查 ASIN 是否可用（布尔值）

        Returns:
            True = 有效, False = 无效或错误
        """
        try:
            resp = self.check_product(asin)
            return "success" in resp
        except Exception:
            return False
