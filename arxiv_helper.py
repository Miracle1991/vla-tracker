from __future__ import annotations

import re
import time
from typing import Any, Optional
from xml.etree import ElementTree

import requests


def extract_arxiv_id(url: str) -> Optional[str]:
    """
    从 arXiv URL 中提取论文 ID。
    支持的格式：
    - https://arxiv.org/abs/2406.09246
    - https://arxiv.org/html/2601.02295v1
    - https://arxiv.org/pdf/2406.09246.pdf
    """
    # 匹配 arxiv.org/abs/、arxiv.org/html/、arxiv.org/pdf/ 后面的 ID
    patterns = [
        r"arxiv\.org/abs/(\d{4}\.\d{4,5})",
        r"arxiv\.org/html/(\d{4}\.\d{4,5})",
        r"arxiv\.org/pdf/(\d{4}\.\d{4,5})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_arxiv_abstract(arxiv_id: str) -> Optional[str]:
    """
    使用 arXiv API 获取论文摘要。
    
    Args:
        arxiv_id: arXiv 论文 ID，格式如 "2406.09246"
    
    Returns:
        论文摘要，如果获取失败返回 None
    """
    try:
        # arXiv API: https://arxiv.org/help/api/user-manual
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        resp = requests.get(api_url, timeout=10)
        
        if resp.status_code != 200:
            return None
        
        # 解析 XML 响应
        root = ElementTree.fromstring(resp.content)
        # arXiv API 使用 Atom 格式
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        
        # 查找摘要
        summary_elem = root.find(".//atom:summary", namespace)
        if summary_elem is not None and summary_elem.text:
            # 清理摘要文本（移除换行和多余空格）
            abstract = summary_elem.text.strip()
            abstract = re.sub(r"\s+", " ", abstract)  # 将多个空白字符替换为单个空格
            return abstract
        
        return None
    except Exception as e:
        print(f"[WARN] 获取 arXiv {arxiv_id} 摘要失败: {e}")
        return None


def translate_to_chinese(text: str) -> Optional[str]:
    """
    将英文文本翻译成中文。
    使用 Google Translate API（需要配置 GOOGLE_TRANSLATE_API_KEY）或免费服务。
    
    如果配置了 GOOGLE_TRANSLATE_API_KEY，使用 Google Translate API。
    否则，尝试使用 googletrans 库（免费但不稳定）。
    """
    try:
        try:
            import config
        except ImportError:
            try:
                import config.example as config  # type: ignore
            except ImportError:
                # 如果 config 不存在，创建一个虚拟对象
                class Config:
                    GOOGLE_TRANSLATE_API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", None)
                config = Config()  # type: ignore
        
        # 优先使用 Google Translate API（如果配置了）
        api_key = getattr(config, "GOOGLE_TRANSLATE_API_KEY", None)
        if api_key:
            return translate_with_google_api(text, api_key)
    except Exception:
        pass  # config 不存在或出错，继续使用 googletrans
    
    # 否则尝试使用 googletrans（免费但不稳定）
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src="en", dest="zh-cn")
        if result and result.text:
            return result.text
    except ImportError:
        print("[WARN] googletrans 未安装，跳过翻译。可以运行: pip install googletrans==4.0.0rc1")
    except Exception as e:
        print(f"[WARN] 翻译失败: {e}")
    
    return None


def translate_with_google_api(text: str, api_key: str) -> Optional[str]:
    """
    使用 Google Cloud Translation API 翻译文本。
    """
    try:
        # Google Cloud Translation API v2
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            "key": api_key,
            "q": text,
            "source": "en",
            "target": "zh-CN",
        }
        
        resp = requests.post(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            translated_text = data.get("data", {}).get("translations", [{}])[0].get("translatedText")
            return translated_text
        
        return None
    except Exception as e:
        print(f"[WARN] Google Translate API 调用失败: {e}")
        return None


def enrich_arxiv_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    为 arXiv 论文条目添加摘要（中文翻译）。
    
    Args:
        items: 论文条目列表，每个条目应包含 "url" 字段
    
    Returns:
        添加了 "abstract" 和 "abstract_zh" 字段的条目列表
    """
    enriched_items = []
    
    for idx, item in enumerate(items):
        url = item.get("url", "")
        if not url or "arxiv.org" not in url:
            enriched_items.append(item)
            continue
        
        # 提取 arXiv ID
        arxiv_id = extract_arxiv_id(url)
        if not arxiv_id:
            enriched_items.append(item)
            continue
        
        # 获取摘要
        abstract = get_arxiv_abstract(arxiv_id)
        if abstract:
            item["abstract"] = abstract
            # 翻译成中文
            abstract_zh = translate_to_chinese(abstract)
            if abstract_zh:
                item["abstract_zh"] = abstract_zh
            else:
                # 如果翻译失败，至少保留英文摘要
                item["abstract_zh"] = abstract
        
        enriched_items.append(item)
        
        # 添加延迟，避免请求过快
        if idx < len(items) - 1:
            time.sleep(1)  # arXiv API 建议每秒不超过1次请求
    
    return enriched_items
