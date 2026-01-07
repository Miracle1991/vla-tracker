from __future__ import annotations

import os
import re
import time
from typing import Any, Optional, Tuple
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


def _clean_arxiv_text(text: str) -> str:
    text = text.strip()
    # arXiv API 里的 title/summary 经常带换行与多空格
    return re.sub(r"\s+", " ", text)


def get_arxiv_metadata(arxiv_id: str) -> Tuple[Optional[str], Optional[str], Optional[list[str]]]:
    """
    使用 arXiv API 获取论文标题、摘要和作者。
    
    Args:
        arxiv_id: arXiv 论文 ID，格式如 "2406.09246"
    
    Returns:
        (title, abstract, authors)；如果获取失败返回 (None, None, None)
        authors 是作者名称列表
    """
    try:
        # arXiv API: https://arxiv.org/help/api/user-manual
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        resp = requests.get(api_url, timeout=10)
        
        if resp.status_code != 200:
            return (None, None, None)
        
        # 解析 XML 响应
        root = ElementTree.fromstring(resp.content)
        # arXiv API 使用 Atom 格式
        namespace = {"atom": "http://www.w3.org/2005/Atom"}

        entry = root.find(".//atom:entry", namespace)
        if entry is None:
            return (None, None, None)

        title_elem = entry.find("atom:title", namespace)
        summary_elem = entry.find("atom:summary", namespace)

        title = _clean_arxiv_text(title_elem.text) if (title_elem is not None and title_elem.text) else None
        abstract = _clean_arxiv_text(summary_elem.text) if (summary_elem is not None and summary_elem.text) else None
        
        # 提取作者信息
        authors = []
        for author_elem in entry.findall("atom:author", namespace):
            name_elem = author_elem.find("atom:name", namespace)
            if name_elem is not None and name_elem.text:
                author_name = _clean_arxiv_text(name_elem.text)
                if author_name:
                    authors.append(author_name)
        
        return (title, abstract, authors if authors else None)
    except Exception as e:
        print(f"[WARN] 获取 arXiv {arxiv_id} 元数据失败: {e}")
        return (None, None, None)


def get_arxiv_abstract(arxiv_id: str) -> Optional[str]:
    _, abstract, _ = get_arxiv_metadata(arxiv_id)
    return abstract


def translate_with_baidu_api(text: str, app_id: str, secret_key: str) -> Optional[str]:
    """
    使用百度翻译 API 翻译文本。
    百度翻译 API 免费额度：每月 200 万字符，更稳定可靠。
    
    Args:
        text: 要翻译的文本
        app_id: 百度翻译 API App ID
        secret_key: 百度翻译 API Secret Key
    
    Returns:
        翻译后的中文文本，失败返回 None
    """
    import hashlib
    import random
    
    try:
        # 百度翻译 API 文档: https://fanyi-api.baidu.com/doc/21
        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        
        # 如果文本太长，截断（百度翻译单次最多 6000 字符）
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        salt = str(random.randint(32768, 65536))
        sign_str = app_id + text + salt + secret_key
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
        
        params = {
            "q": text,
            "from": "en",
            "to": "zh",
            "appid": app_id,
            "salt": salt,
            "sign": sign,
        }
        
        resp = requests.post(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "trans_result" in data:
                translated_text = "\n".join([item.get("dst", "") for item in data["trans_result"]])
                return translated_text
            elif "error_code" in data:
                print(f"[WARN] 百度翻译 API 错误: {data.get('error_code')} - {data.get('error_msg')}")
        else:
            print(f"[WARN] 百度翻译 API 请求失败: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"[WARN] 百度翻译 API 调用失败: {e}")
        return None


def translate_with_youdao_api(text: str, app_key: str, app_secret: str) -> Optional[str]:
    """
    使用有道翻译 API 翻译文本。
    有道翻译 API 免费额度：每月 100 万字符。
    
    Args:
        text: 要翻译的文本
        app_key: 有道翻译 API App Key
        app_secret: 有道翻译 API App Secret
    
    Returns:
        翻译后的中文文本，失败返回 None
    """
    import hashlib
    import uuid
    import time
    
    try:
        # 有道翻译 API 文档: https://ai.youdao.com/DOCSIRMA/html/自然语言翻译/API文档/文本翻译服务/文本翻译服务-API文档.html
        url = "https://openapi.youdao.com/api"
        
        # 如果文本太长，截断（有道翻译单次最多 5000 字符）
        max_length = 4500
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        salt = str(uuid.uuid1())
        curtime = str(int(time.time()))
        sign_str = app_key + text + salt + curtime + app_secret
        sign = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()
        
        data = {
            "q": text,
            "from": "en",
            "to": "zh-CHS",
            "appKey": app_key,
            "salt": salt,
            "sign": sign,
            "signType": "v3",
            "curtime": curtime,
        }
        
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("errorCode") == "0":
                translated_text = result.get("translation", [""])[0]
                return translated_text
            else:
                print(f"[WARN] 有道翻译 API 错误: {result.get('errorCode')} - {result.get('errorMsg')}")
        else:
            print(f"[WARN] 有道翻译 API 请求失败: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"[WARN] 有道翻译 API 调用失败: {e}")
        return None


def translate_with_googletrans(text: str) -> Optional[str]:
    """
    使用 googletrans 库翻译文本（免费，无需 API Key）。
    如果翻译失败，直接返回 None（不重试）。
    
    Args:
        text: 要翻译的文本
    
    Returns:
        翻译后的中文文本，失败返回 None
    """
    try:
        from googletrans import Translator
        
        # 如果文本太长，截断（避免超时）
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        translator = Translator(service_urls=['translate.google.com'])
        
        # 直接尝试翻译，失败则返回 None（不重试）
        try:
            result = translator.translate(text, src="en", dest="zh-cn")
            if result and result.text:
                return result.text
        except Exception as e:
            error_msg = str(e)
            is_timeout = (
                "timeout" in error_msg.lower() or 
                "timed out" in error_msg.lower() or
                "read operation timed out" in error_msg.lower()
            )
            
            if is_timeout:
                print(f"[WARN] googletrans 超时，保留英文摘要")
            else:
                print(f"[WARN] googletrans 翻译失败: {error_msg}，保留英文摘要")
        
        return None
    except ImportError:
        print("[WARN] googletrans 未安装，跳过翻译。可以运行: pip install googletrans==4.0.0rc1")
        return None
    except Exception as e:
        print(f"[WARN] googletrans 调用失败: {e}，保留英文摘要")
        return None


def translate_to_chinese(text: str) -> Optional[str]:
    """
    将英文文本翻译成中文。
    使用 googletrans 库（免费，无需 API Key）。
    
    如果翻译失败，将跳过翻译（保留英文摘要）。
    
    Args:
        text: 要翻译的英文文本
    """
    try:
        result = translate_with_googletrans(text)
        if result and result.strip():
            return result
        else:
            print("[WARN] googletrans 翻译失败，将保留英文摘要")
            return None
        
    except Exception as e:
        print(f"[WARN] 翻译失败: {e}，将保留英文摘要")
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
        
        resp = requests.post(url, params=params, timeout=30)
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

        # 过滤掉非论文页面（例如 arXiv 分类页 / 帮助页等）
        if extract_arxiv_id(url) is None:
            # 没有 arXiv ID 的链接很可能不是论文
            continue
        
        # 提取 arXiv ID
        arxiv_id = extract_arxiv_id(url)
        if not arxiv_id:
            enriched_items.append(item)
            continue

        item["arxiv_id"] = arxiv_id

        # 用 arXiv API 的 title 覆盖搜索结果 title，避免出现 "1 Introduction" 这类网页章节标题
        title, abstract, authors = get_arxiv_metadata(arxiv_id)
        if title:
            item["title"] = title
        
        # 添加作者信息
        if authors:
            item["authors"] = authors
        
        # 获取摘要
        if abstract:
            item["abstract"] = abstract
            # 翻译成中文（添加延迟避免请求过快）
            if idx > 0:
                time.sleep(3)  # 翻译请求之间添加延迟，避免触发限流和超时
            
            try:
                abstract_zh = translate_to_chinese(abstract)
                if abstract_zh and abstract_zh.strip():
                    # 翻译成功，使用中文摘要
                    item["abstract_zh"] = abstract_zh
                else:
                    # 翻译失败或返回空，保留英文摘要
                    print(f"[INFO] 翻译 arXiv {arxiv_id} 摘要失败，保留英文摘要")
                    item["abstract_zh"] = abstract
            except Exception as e:
                # 翻译异常，保留英文摘要
                print(f"[WARN] 翻译 arXiv {arxiv_id} 摘要时发生异常: {e}，保留英文摘要")
                item["abstract_zh"] = abstract
        else:
            # 如果没有获取到摘要，至少设置一个空值
            item["abstract"] = ""
            item["abstract_zh"] = ""
        
        enriched_items.append(item)
        
        # 添加延迟，避免请求过快（arXiv API 建议每秒不超过1次请求）
        if idx < len(items) - 1:
            time.sleep(1)
    
    return enriched_items
