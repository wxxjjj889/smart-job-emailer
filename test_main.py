import unittest
import json
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import (
    get_smtp_config,
    extract_info,
    extract_company,
    load_json,
    save_json,
)

# ---------------------------------------------------------------------------
# extract_company (enhanced)
# ---------------------------------------------------------------------------
class TestExtractCompany(unittest.TestCase):
    def test_bracket_chinese(self):
        self.assertEqual(extract_company("【字节跳动】招聘实习生"), "字节跳动")

    def test_bracket_square(self):
        self.assertEqual(extract_company("[腾讯] 招产品实习生"), "腾讯")

    def test_bracket_book(self):
        self.assertEqual(extract_company("《小红书》招聘"), "小红书")

    def test_known_company_in_body(self):
        """公司名出现在正文中间，没有括号"""
        self.assertEqual(
            extract_company("招聘运营实习生\n百度 AI团队招聘，base北京"),
            "百度"
        )

    def test_known_company_long_name_first(self):
        """长公司名应优先于短名（如 字节跳动 优先于 跳动）"""
        self.assertEqual(
            extract_company("字节跳动商业化团队招聘"),
            "字节跳动"
        )

    def test_tiktok_in_body(self):
        self.assertEqual(
            extract_company("TikTok电商部门招聘实习生"),
            "TikTok"
        )

    def test_securities_pattern(self):
        """XX证券 - 优先匹配已知公司名（申万宏源），或后缀模式"""
        self.assertEqual(
            extract_company("招聘：申万宏源证券研究所实习生"),
            "申万宏源"
        )

    def test_bank_pattern(self):
        """XX银行 后缀模式匹配（招商银行在已知库中会先匹配）"""
        result = extract_company("某商业银行招聘风控实习生 — 某银行")
        # 会优先匹配到某个已知银行，或者后缀模式
        self.assertTrue(result != "")

    def test_fund_pattern(self):
        """XX基金 后缀模式匹配"""
        self.assertEqual(
            extract_company("某基金公司招聘 — 天弘基金研究部"),
            "天弘基金"
        )

    def test_foreign_company(self):
        self.assertEqual(
            extract_company("Google上海招聘软件工程师实习生"),
            "Google"
        )

    def test_company_in_middle_of_text(self):
        """公司名在长文本中间"""
        text = "岗位职责：\n1. 协助团队进行行业研究\n2. 支持腾讯广告业务数据分析"
        self.assertEqual(extract_company(text), "腾讯")

    def test_first_line_fallback(self):
        """没有括号、不在已知库、没有后缀模式 → 第一行兜底"""
        text = "某不知名小公司 - 运营实习生招聘"
        result = extract_company(text)
        self.assertTrue(len(result) >= 2)

    def test_multiple_companies_returns_first_known(self):
        """文本中出现多个公司，返回已知库中最先匹配的那个"""
        text = "百度对比腾讯的产品策略研究"
        result = extract_company(text)
        self.assertIn(result, ["百度", "腾讯"])

    def test_kuaishou(self):
        self.assertEqual(
            extract_company("快手商业化招聘数据分析实习生"),
            "快手"
        )

    def test_xiaohongshu(self):
        self.assertEqual(
            extract_company("小红书社区部招聘运营实习生"),
            "小红书"
        )

    def test_meituan(self):
        self.assertEqual(
            extract_company("美团到店事业群招聘后端实习生"),
            "美团"
        )

    def test_deepseek(self):
        self.assertEqual(
            extract_company("DeepSeek招聘AI研究实习生"),
            "DeepSeek"
        )

    def test_byd(self):
        self.assertEqual(
            extract_company("比亚迪招聘智能驾驶实习生"),
            "比亚迪"
        )

    def test_consulting_firm(self):
        self.assertEqual(
            extract_company("麦肯锡大中华区招聘咨询实习生"),
            "麦肯锡"
        )

    def test_deloitte(self):
        self.assertEqual(
            extract_company("德勤审计部招聘寒假实习生"),
            "德勤"
        )

    def test_bracket_location_filtered(self):
        """【上海】是地点，不应被当作公司名，应继续匹配已知公司"""
        text = "上海*1【上海】字节跳动-高阶岗位招聘实习生"
        self.assertEqual(extract_company(text), "字节跳动")

    def test_bracket_location_filtered_no_known_company(self):
        """括号里是地点，且没有已知公司名时，跳过后走下一个括号或其他策略"""
        text = "【北京】某科技有限公司招聘开发实习生"
        self.assertNotEqual(extract_company(text), "北京")


# ---------------------------------------------------------------------------
# get_smtp_config
# ---------------------------------------------------------------------------
class TestGetSmtpConfig(unittest.TestCase):
    def test_known_163(self):
        server, port = get_smtp_config("test@163.com")
        self.assertEqual(server, "smtp.163.com")
        self.assertEqual(port, 465)

    def test_known_126(self):
        server, port = get_smtp_config("user@126.com")
        self.assertEqual(server, "smtp.126.com")
        self.assertEqual(port, 465)

    def test_known_yeah(self):
        server, port = get_smtp_config("abc@yeah.net")
        self.assertEqual(server, "smtp.yeah.net")
        self.assertEqual(port, 465)

    def test_known_qq(self):
        server, port = get_smtp_config("test@qq.com")
        self.assertEqual(server, "smtp.qq.com")
        self.assertEqual(port, 465)

    def test_known_foxmail(self):
        server, port = get_smtp_config("abc@foxmail.com")
        self.assertEqual(server, "smtp.qq.com")
        self.assertEqual(port, 465)

    def test_known_gmail(self):
        server, port = get_smtp_config("user@gmail.com")
        self.assertEqual(server, "smtp.gmail.com")
        self.assertEqual(port, 465)

    def test_known_outlook(self):
        server, port = get_smtp_config("me@outlook.com")
        self.assertEqual(server, "smtp-mail.outlook.com")
        self.assertEqual(port, 587)

    def test_known_hotmail(self):
        server, port = get_smtp_config("me@hotmail.com")
        self.assertEqual(server, "smtp-mail.outlook.com")
        self.assertEqual(port, 587)

    def test_known_sina(self):
        server, port = get_smtp_config("a@sina.com")
        self.assertEqual(server, "smtp.sina.com")
        self.assertEqual(port, 465)

    def test_known_sohu(self):
        server, port = get_smtp_config("b@sohu.com")
        self.assertEqual(server, "smtp.sohu.com")
        self.assertEqual(port, 465)

    def test_unknown_domain_fallback(self):
        server, port = get_smtp_config("user@custom.com")
        self.assertEqual(server, "smtp.custom.com")
        self.assertEqual(port, 465)

    def test_case_insensitive_domain(self):
        server, port = get_smtp_config("User@QQ.COM")
        self.assertEqual(server, "smtp.qq.com")
        self.assertEqual(port, 465)


# ---------------------------------------------------------------------------
# extract_info
# ---------------------------------------------------------------------------
class TestExtractInfo( unittest.TestCase):
    # --- email extraction ---
    def test_email_simple(self):
        info = extract_info("联系邮箱: hr@company.com")
        self.assertEqual(info["email"], "hr@company.com")

    def test_email_multiple_takes_first(self):
        info = extract_info("邮箱 hr@abc.com 或 backup@abc.com")
        self.assertEqual(info["email"], "hr@abc.com")

    def test_email_no_email(self):
        info = extract_info("没有邮箱的招聘信息")
        self.assertEqual(info["email"], "")

    def test_email_with_underscore_and_digits(self):
        info = extract_info("campus_2024@my-company.cn")
        self.assertEqual(info["email"], "campus_2024@my-company.cn")

    # --- naming format extraction ---
    def test_naming_format_standard(self):
        text = "简历命名格式：姓名-学校-岗位-联系方式"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-岗位-联系方式")

    def test_naming_format_with_colon(self):
        text = "简历和邮件主题命名：姓名_学校_实习岗位_手机号"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名_学校_实习岗位_手机号")

    def test_naming_format_pdf_included(self):
        text = "简历命名：姓名+学校+岗位.pdf"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名+学校+岗位.pdf")

    def test_naming_format_cut_at_semicolon(self):
        text = "简历命名：学校-姓名-专业；实习时间不少于3个月"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "学校-姓名-专业")

    def test_naming_format_no_format(self):
        info = extract_info("招聘一名实习生，要求有编程经验")
        self.assertEqual(info["naming_format"], "")

    def test_naming_format_too_short_rejected(self):
        info = extract_info("命名格式：AB")
        self.assertEqual(info["naming_format"], "")

    def test_naming_format_too_long_rejected(self):
        text = "命名格式：" + "非常" * 35
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "")

    # --- company extraction ---
    def test_company_bracket_chinese(self):
        info = extract_info("【字节跳动】招聘实习生")
        self.assertEqual(info["company"], "字节跳动")

    def test_company_bracket_square(self):
        info = extract_info("[腾讯] 招产品实习生")
        self.assertEqual(info["company"], "腾讯")

    def test_company_from_first_line_fallback(self):
        info = extract_info("阿里巴巴 - 测试开发实习生招聘")
        self.assertEqual(info["company"], "阿里巴巴")

    def test_company_from_first_line_strips_prefix(self):
        info = extract_info("急招实习生，地点北京")
        self.assertEqual(info["company"], "实习生")

    # --- position extraction ---
    def test_position_with_suffix_engineer(self):
        info = extract_info("招聘岗位：算法工程师")
        self.assertEqual(info["position"], "算法工程师")

    def test_position_with_suffix_intern(self):
        info = extract_info("岗位名称：前端开发实习生")
        self.assertEqual(info["position"], "前端开发实习生")

    def test_position_with_suffix_manager(self):
        info = extract_info("【腾讯】产品经理 北京")
        self.assertEqual(info["position"], "产品经理")

    # --- combined extraction ---
    def test_full_job_posting(self):
        text = """【美团】数据开发实习生
        岗位：数据开发实习生
        简历命名格式：姓名-学校-岗位
        简历请发送至 hr@meituan.com
        """
        info = extract_info(text)
        self.assertEqual(info["email"], "hr@meituan.com")
        self.assertEqual(info["company"], "美团")
        self.assertEqual(info["position"], "数据开发实习生")
        self.assertEqual(info["naming_format"], "姓名-学校-岗位")

    def test_full_job_posting_variant(self):
        text = """小红书 - 运营实习生招聘
        邮箱: campus@xiaohongshu.com
        简历和邮件主题命名: 投递岗位_姓名_学校_联系方式
        每周到岗4天，实习3个月以上
        """
        info = extract_info(text)
        self.assertEqual(info["email"], "campus@xiaohongshu.com")
        self.assertEqual(info["company"], "小红书")
        self.assertEqual(info["position"], "运营实习生")
        self.assertEqual(info["naming_format"], "投递岗位_姓名_学校_联系方式")

    def test_gaode_job_posting(self):
        text = """[高德] 大数据开发工程师
        职位描述：负责数据平台建设
        邮箱：gaode-hr@alibaba-inc.com
        简历命名：姓名-学校-岗位
        """
        info = extract_info(text)
        self.assertEqual(info["email"], "gaode-hr@alibaba-inc.com")
        self.assertEqual(info["company"], "高德")
        self.assertEqual(info["position"], "大数据开发工程师")

    # ---- 新增：邮件标题 / 主题格式提取 ----
    def test_naming_format_email_subject_chinese(self):
        """邮件标题请注明：XXX-姓名-院校-年级-每周可实习天数以及实习周期"""
        text = "简历请发：campus@chinaamc.com，邮件标题请注明：华夏股权投资者关系-姓名-院校-年级-每周可实习天数以及实习周期。"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "华夏股权投资者关系-姓名-院校-年级-每周可实习天数以及实习周期")

    def test_naming_format_email_subject_with_underscore(self):
        """邮件主题：姓名_学校_岗位_手机号"""
        text = "邮箱: hr@test.com\n邮件主题：姓名_学校_岗位_手机号"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名_学校_岗位_手机号")

    def test_naming_format_email_subject_with_plus(self):
        """邮件标题：姓名+学校+岗位+联系方式"""
        text = "邮箱: hr@test.com\n邮件标题：姓名+学校+岗位+联系方式"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名+学校+岗位+联系方式")

    def test_naming_format_resume_and_email_separate(self):
        """简历命名和邮件标题分别指定"""
        text = "简历命名：姓名-学校-岗位\n邮件标题：应聘岗位-姓名-学校"
        info = extract_info(text)
        # 应提取第一个匹配的（简历命名），两个都符合命名格式模式
        self.assertIn("姓名", info["naming_format"])
        self.assertIn("学校", info["naming_format"])

    def test_naming_format_with_chinese_dash(self):
        """使用中文横杆——作为分隔符"""
        text = "简历请命名为：姓名——学校——岗位"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名——学校——岗位")

    def test_naming_format_write_clearly(self):
        """请写明邮件标题格式"""
        text = "请写明邮件标题：应聘岗位-姓名-院校-联系方式"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "应聘岗位-姓名-院校-联系方式")

    def test_naming_format_mark(self):
        """请标注命名格式"""
        text = "请标注：姓名_学校_实习岗位"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名_学校_实习岗位")

    def test_naming_format_quoted(self):
        """引号内的命名格式"""
        text = '简历请以"姓名-学校-岗位"的格式命名'
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-岗位")

    def test_naming_format_no_keyword_but_pattern(self):
        """没有明确关键词但行内容明显是命名格式"""
        text = "邮箱: hr@test.com\n姓名-学校-岗位-联系方式\n要求：实习3个月"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-岗位-联系方式")

    def test_naming_format_in_long_jd(self):
        """完整的招聘JD中包含邮件标题格式"""
        text = """【招聘职位】华夏股权（华夏基金全资子公司）-投资者关系部（IR）实习生
实习地点：北京金融街
部门简介：团队负责基金募资、存量投资者维护、品牌推介及机构渠道拓展；
职责描述：
1、协助开展市场及机构投资者调研，整理行业、机构动态信息，撰写募资材料。
2、配合对接各类LP、金融机构及合作渠道。
岗位要求
1、国内外知名院校研究生及以上在读。
2、拥有头部机构IR、募资相关实习经历者优先。
【联系方式】
简历请发：campus@chinaamc.com，邮件标题请注明：华夏股权投资者关系-姓名-院校-年级-每周可实习天数以及实习周期。"""
        info = extract_info(text)
        self.assertEqual(info["email"], "campus@chinaamc.com")
        self.assertEqual(info["naming_format"], "华夏股权投资者关系-姓名-院校-年级-每周可实习天数以及实习周期")
        self.assertEqual(info["company"], "华夏基金")
        self.assertIn("实习生", info["position"])

    def test_naming_format_strips_parenthetical_example(self):
        """括号中的示例说明应被去除，如 学校-年级-专业（如"交大-研一-金融"）"""
        text = """【投递要求】
        1、邮箱：hr@tencent.com
        2、命名：学校-年级-专业-最早到岗日期-每周实习天数-实习时长（如"上海交通大学-研一-金融-6/1-5天-6个月"）"""
        info = extract_info(text)
        self.assertEqual(info["email"], "hr@tencent.com")
        self.assertEqual(info["naming_format"], "学校-年级-专业-最早到岗日期-每周实习天数-实习时长")

    def test_naming_format_strips_e_g_example(self):
        """英文括号示例 e.g."..." 也应被去除"""
        text = """邮件标题：姓名-学校-岗位 (e.g."张三-北大-产品经理")"""
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-岗位")

    def test_naming_format_strips_instruction_parenthetical(self):
        """括号中的指令说明应被去除，如 （请严格按上述格式命名）"""
        text = """简历及邮件命名格式：姓名-学校-专业-毕业时间-每周可实习天数-计划实习月数（请严格按上述格式命名）。"""
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-专业-毕业时间-每周可实习天数-计划实习月数")

    def test_naming_format_strips_parenthetical_note(self):
        """括号中的注意事项应被去除，如 （不按要求命名不予考虑）"""
        text = "简历命名：姓名-学校-岗位（不按要求命名者不予考虑）"
        info = extract_info(text)
        self.assertEqual(info["naming_format"], "姓名-学校-岗位")


# ---------------------------------------------------------------------------
# load_json / save_json
# ---------------------------------------------------------------------------
class TestJsonIO(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_load_nonexistent_file_returns_default(self):
        path = os.path.join(self.tmpdir, "nofile.json")
        result = load_json(path, {"a": 1})
        self.assertEqual(result, {"a": 1})

    def test_load_valid_json(self):
        path = os.path.join(self.tmpdir, "test.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"key": "value"}, f)
        result = load_json(path)
        self.assertEqual(result, {"key": "value"})

    def test_load_invalid_json_returns_default(self):
        path = os.path.join(self.tmpdir, "bad.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("not valid json {{{")
        result = load_json(path, {"fallback": True})
        self.assertEqual(result, {"fallback": True})

    def test_save_and_load_roundtrip(self):
        path = os.path.join(self.tmpdir, "roundtrip.json")
        data = {"姓名": "张三", "年龄": 25, "skills": ["Python", "Java"]}
        save_json(path, data)
        loaded = load_json(path)
        self.assertEqual(loaded, data)

    def test_save_creates_file(self):
        path = os.path.join(self.tmpdir, "new.json")
        save_json(path, [1, 2, 3])
        self.assertTrue(os.path.exists(path))

    def test_load_default_when_no_default_passed(self):
        path = os.path.join(self.tmpdir, "nofile.json")
        result = load_json(path)
        self.assertEqual(result, {})

    def test_load_empty_file_returns_default(self):
        path = os.path.join(self.tmpdir, "empty.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        result = load_json(path, {"default": "yes"})
        self.assertEqual(result, {"default": "yes"})

    def test_save_unicode_handling(self):
        path = os.path.join(self.tmpdir, "unicode.json")
        data = {"emoji": "😀", "中文": "你好"}
        save_json(path, data)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        self.assertIn("😀", raw)
        self.assertIn("你好", raw)


# ---------------------------------------------------------------------------
# _fill_template (imported function logic, tested via a helper)
# ---------------------------------------------------------------------------
class TestFillTemplate(unittest.TestCase):
    """Test the _fill_template replacement logic.

    We replicate the logic here for isolated, GUI-free testing.
    """
    def _do_fill(self, fmt, info, name="张三", phone="13800001111",
                 school="北京大学", email="me@163.com", weekly="每周5天"):
        replacements = [
            ("姓名", name),
            ("名字", name),
            ("应聘岗位", info.get("position", "")),
            ("岗位", info.get("position", "")),
            ("职位", info.get("position", "")),
            ("每周出勤", weekly),
            ("每周实习几天", weekly),
            ("每周几天", weekly),
            ("实习几天", weekly),
            ("计划实习月数", weekly),
            ("实习月数", weekly),
            ("出勤时间", weekly),
            ("出勤天数", weekly),
            ("联系方式", phone),
            ("电话", phone),
            ("手机号", phone),
            ("手机", phone),
            ("学校", school),
            ("邮箱", email),
            ("公司", info.get("company", "")),
        ]
        result = fmt
        for placeholder, value in replacements:
            if value:
                result = result.replace(placeholder, value)
        return result

    def test_simple_name_replacement(self):
        result = self._do_fill(
            "姓名-学校-岗位", {"position": "开发", "company": "字节"},
            name="王潇霄", school="对外经贸"
        )
        self.assertEqual(result, "王潇霄-对外经贸-开发")

    def test_position_replacement(self):
        result = self._do_fill(
            "应聘岗位-姓名", {"position": "产品经理"},
            name="张三"
        )
        self.assertEqual(result, "产品经理-张三")

    def test_phone_replacement(self):
        result = self._do_fill(
            "姓名_手机号", {},
            name="李四", phone="13912345678"
        )
        self.assertEqual(result, "李四_13912345678")

    def test_all_fields_replacement(self):
        fmt = "姓名_学校_岗位_联系方式"
        result = self._do_fill(
            fmt,
            {"position": "前端实习生", "company": "美团"},
            name="赵六", school="清华", phone="13600000000"
        )
        self.assertEqual(result, "赵六_清华_前端实习生_13600000000")

    def test_no_replacement_when_no_data(self):
        fmt = "简历模板"
        result = self._do_fill(fmt, {})
        self.assertEqual(result, "简历模板")

    def test_partial_replacement_only_filled_fields(self):
        """Placeholders without values should remain untouched."""
        fmt = "姓名-学校-岗位"
        result = self._do_fill(fmt, {}, name="", school="", phone="")
        self.assertEqual(result, "姓名-学校-岗位")

    def test_email_in_template(self):
        result = self._do_fill(
            "姓名_邮箱", {},
            name="张三", email="zhangsan@163.com"
        )
        self.assertEqual(result, "张三_zhangsan@163.com")

    def test_weekly_attendance_in_template(self):
        result = self._do_fill(
            "姓名-出勤时间", {},
            name="张三", weekly="每周5天"
        )
        self.assertEqual(result, "张三-每周5天")

    def test_weekly_attendance_chuqin_in_template(self):
        result = self._do_fill(
            "姓名-每周出勤-学校", {},
            name="李四", weekly="出勤5天", school="清华"
        )
        self.assertEqual(result, "李四-出勤5天-清华")

    def test_weekly_internship_days_replacement(self):
        """每周实习几天 应整体替换，不应残留 实习几天"""
        result = self._do_fill(
            "姓名-每周实习几天", {},
            name="张三", weekly="每周5天"
        )
        self.assertEqual(result, "张三-每周5天")

    def test_internship_days_standalone_replacement(self):
        """单独的 实习几天 也应替换"""
        result = self._do_fill(
            "姓名-实习几天", {},
            name="张三", weekly="每周5天"
        )
        self.assertEqual(result, "张三-每周5天")

    def test_planned_internship_months_replacement(self):
        """计划实习月数 应整体替换为实习时长"""
        result = self._do_fill(
            "姓名-计划实习月数", {},
            name="张三", weekly="实习3个月"
        )
        self.assertEqual(result, "张三-实习3个月")



if __name__ == "__main__":
    unittest.main()
