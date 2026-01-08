import os
import requests
from typing import Optional, Tuple, List
from pydantic import BaseModel, Field
from cozeloop.decorator import observe
from coze_coding_utils.runtime_ctx.context import Context, default_headers


class WebItem(BaseModel):
    """Web搜索结果项模型（对应WebItem-搜索结果项）"""

    Id: str = Field(..., description="结果Id")

    SortId: int = Field(..., description="排序Id")

    Title: str = Field(..., description="标题")

    SiteName: Optional[str] = Field(None, description="站点名")

    Url: Optional[str] = Field(None, description="落地页")

    Snippet: str = Field(..., description="普通摘要（100字左右的相关切片）")

    Summary: Optional[str] = Field(None, description="精准摘要（300~500字左右经过模型处理的相关片段）")

    Content: Optional[str] = Field(None, description="正文（引用站点正文）")

    PublishTime: Optional[str] = Field(None, description="发布时间, ISO时间格式\n示例: 2025-05-30T19:35:24+08:00")

    LogoUrl: Optional[str] = Field(None, description="落地页IconUrl链接")

    RankScore: Optional[float] = Field(None, description="得分")

    AuthInfoDes: str = Field(..., description="权威度描述, 包括: 非常权威、正常权威、一般权威、一般不权威")

    AuthInfoLevel: int = Field(...,
                               description="权威度评级, 对应权威度描述, 包括: 1 非常权威、2 正常权威、3 一般权威、4 一般不权威")


class ImageInfo(BaseModel):
    """ImageInfo-图片结果项（图片详情子模型）"""

    Url: str = Field(..., description="图片链接")

    Width: Optional[int] = Field(None, description="宽")

    Height: Optional[int] = Field(None, description="高")

    Shape: str = Field(
        ...,
        description="""横长方形，判断: (宽>高*1.2)；竖长方形，判断: (宽<高*1.2)；方形，判断: (其余情况)"""
    )


class ImageItem(BaseModel):
    """ImageItem-搜索结果项（SearchType=image的结果项）"""

    Id: str = Field(..., description="结果Id")

    SortId: int = Field(..., description="排序Id")

    Title: Optional[str] = Field(None, description="标题")

    SiteName: Optional[str] = Field(None, description="站点名")

    Url: Optional[str] = Field(None, description="落地页")

    PublishTime: Optional[str] = Field(
        None,
        description="发布时间, ISO时间格式。示例: 2025-05-30T19:35:24+08:00"
    )

    Image: ImageInfo = Field(..., description="图片详情")


@observe
def web_search(
        ctx: Context,
        query: str,
        search_type: str = "web",
        count: Optional[int] = 10,
        need_content: Optional[bool] = False,
        need_url: Optional[bool] = False,
        sites: Optional[str] = None,
        block_hosts: Optional[str] = None,
        need_summary: Optional[bool] = True,
        time_range: Optional[str] = None,
) -> Tuple[List[WebItem], str, Optional[List[ImageItem]], dict]:
    """
    融合信息搜索API，返回搜索结果项列表、搜索结果内容总结和原始响应数据。

    Args:
        ctx: 上下文对象，用于串联一次运行态的相关信息
        query (str): 用户搜索query，1~100个字符(过长会截断)，不支持多词搜索。
        search_type (str, 可选): 搜索类型枚举值，目前支持 web：web搜索，返回搜索到的站点信息；web_summary：web搜索总结版，返回搜索到的站点信息及LLM总结结果；image：图片搜索，返回搜索到的图片信息。
        count (int, 可选): 返回条数，最多50条，默认10条。
        need_content (bool, 可选): 是否仅返回有正文的结果，默认false（不限制必须有正文）。
        need_url (bool, 可选): 是否仅返回原文链接的结果，默认false（不限制必须有Url）。
        sites (str, 可选): 指定搜索的Site范围，多个域名使用'|'分隔，最多支持5个。需填入完整域名，示例：aliyun.com|mp.qq.com。
        block_hosts (str, 可选): 指定屏蔽的搜索Site，多个域名使用'|'分隔，最多支持5个。需填入完整域名，示例：aliyun.com|mp.qq.com。
        need_summary (bool, 可选): 是否需要精准摘要，默认true。调用 web_summary web搜索总结版 时，本字段必须为true。
        time_range (str, 可选): 指定搜索的发文时间。以下枚举值，不填即为不限制：OneDay：1天内；OneWeek：1周内；OneMonth：1月内；OneYear：1年内；YYYY-MM-DD..YYYY-MM-DD：从日期A（包含）至日期B（包含）区间段内发文的内容，示例"2024-12-30..2025-12-30"。

    Returns:
        tuple[list[WebItem], str, Optional[list[ImageItem]], dict]: 包含WebItem列表、搜索结果摘要、ImageItem列表(如有)和原始响应数据的元组。
    """
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_BASE_URL")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    headers.update(default_headers(ctx))
    request = {
        "Query": query,
        "SearchType": search_type,
        "Count": count,
        "Filter": {
            "NeedContent": need_content,
            "NeedUrl": need_url,
            "Sites": sites,
            "BlockHosts": block_hosts,
        },
        "NeedSummary": need_summary,
        "TimeRange": time_range,
    }
    try:
        response = requests.post(f'{base_url}/api/search_api/web_search', json=request, headers=headers)
        response.raise_for_status()  # 检查HTTP请求状态
        data = response.json()

        response_metadata = data.get("ResponseMetadata", {})
        result = data.get("Result", {})
        if response_metadata.get("Error"):
            raise Exception(f"web_search 失败: {response_metadata.get('Error')}")

        web_items = []
        image_items = []
        if result.get("WebResults"):
            web_items = [WebItem(**item) for item in result.get("WebResults", [])]
        if result.get("ImageResults"):
            image_items = [ImageItem(**item) for item in result.get("ImageResults", [])]
        content = None
        if result.get("Choices"):
            content = result.get("Choices", [{}])[0].get("Message", {}).get("Content", "")
        return web_items, content, image_items, result
    except requests.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"web_search 失败: {str(e)}")
    finally:
        response.close()
