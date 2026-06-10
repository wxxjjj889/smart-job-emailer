"""AI 提取模块 —— 使用 DeepSeek / OpenAI 兼容 API 从招聘 JD 中提取结构化信息。"""
import json
import urllib.request
import urllib.error

DEFAULT_API_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
TIMEOUT_SECONDS = 15

# ---------------------------------------------------------------------------
# 内部工具函数
# ---------------------------------------------------------------------------

def _build_extract_prompt(text):
    return f"""你是一个招聘信息提取助手。请从以下招聘公告文本中提取关键信息，严格按 JSON 格式返回。

文本：
---
{text}
---

请提取以下字段（如果某个字段在文本中找不到，请返回空字符串 ""）：
1. email: 简历投递邮箱地址
2. naming_format: 简历文件命名格式要求（保留原文中的占位符如"姓名""学校""岗位"等，不要替换）
3. company: 公司名称（去除"招聘""急招""校招"等前缀）
4. position: 招聘岗位名称

返回格式要求：
- 必须只返回一个合法的 JSON 对象，不要包含任何其他文字
- JSON 的键名必须是 email, naming_format, company, position
- 示例返回：{{"email": "hr@example.com", "naming_format": "姓名-学校-岗位", "company": "字节跳动", "position": "算法实习生"}}"""


def _build_fill_prompt(fmt, user_info):
    return f"""你是一个简历命名格式填充助手。请根据命名模板和用户信息，将模板中的占位符替换为真实值。

命名模板：{fmt}

用户真实信息：
- 姓名：{user_info.get('name', '')}
- 手机号：{user_info.get('phone', '')}
- 学校：{user_info.get('school', '')}
- 研究生院校：{user_info.get('grad_school', '')}
- 本科院校：{user_info.get('undergrad_school', '')}
- 专业：{user_info.get('major', '')}
- 本科专业：{user_info.get('undergrad_major', '')}
- 每周出勤：{user_info.get('weekly', '')}
- 实习时长：{user_info.get('duration', '')}
- 到岗时间：{user_info.get('arrival', '')}
- 毕业时间：{user_info.get('grad_time', '')}
- 年级：{user_info.get('grade', '')}
- 邮箱：{user_info.get('email', '')}
- 岗位：{user_info.get('position', '')}
- 公司：{user_info.get('company', '')}

请将模板中的占位符（如"姓名""学校""岗位"等）替换为对应的真实值。
返回格式要求：
- 必须只返回填充后的字符串，不要包含任何其他文字
- 如果某个信息为空，对应的占位符保持原样不动"""


def _call_api(messages, config, response_format=None):
    """调用 OpenAI 兼容 Chat Completions API，返回响应文本。"""
    api_base = (config.get("api_base") or DEFAULT_API_BASE).rstrip("/")
    api_key = config.get("api_key", "")
    model = config.get("model") or DEFAULT_MODEL

    url = f"{api_base}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1024,
    }
    if response_format:
        body["response_format"] = response_format

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API 请求失败 (HTTP {e.code}): {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络连接失败: {e.reason}")
    except json.JSONDecodeError:
        raise RuntimeError("API 返回内容无法解析")

    if not result.get("choices"):
        raise RuntimeError("API 返回无有效结果")

    return result["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def extract_info_ai(text, config):
    """使用 AI 从招聘文本中提取信息。返回 dict 同 extract_info() 格式。"""
    if not text.strip():
        return {"email": "", "naming_format": "", "company": "", "position": ""}

    if not config.get("api_key"):
        raise RuntimeError("API Key 未配置，请在 AI 设置中填写")

    prompt = _build_extract_prompt(text)
    raw = _call_api(
        [{"role": "user", "content": prompt}],
        config,
        response_format={"type": "json_object"},
    )

    # 清理可能的 markdown 代码块包裹
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"AI 返回格式异常，无法解析为 JSON: {raw[:200]}")

    return {
        "email": str(result.get("email", "")).strip(),
        "naming_format": str(result.get("naming_format", "")).strip(),
        "company": str(result.get("company", "")).strip(),
        "position": str(result.get("position", "")).strip(),
    }


def fill_template_ai(fmt, user_info, config):
    """使用 AI 将命名模板中的占位符替换为真实用户信息。返回填充后的字符串。"""
    if not fmt.strip():
        return fmt

    if not config.get("api_key"):
        raise RuntimeError("API Key 未配置，请在 AI 设置中填写")

    prompt = _build_fill_prompt(fmt, user_info)
    raw = _call_api(
        [{"role": "user", "content": prompt}],
        config,
    )
    return raw.strip().strip('"').strip("'")
