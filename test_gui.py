"""
GUI logic tests — verify App methods without launching real tkinter windows.
"""
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import tkinter as tk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import App, extract_info

# Hidden root window for tk.StringVar to work in tests
_ROOT = tk.Tk()
_ROOT.withdraw()


# ---------------------------------------------------------------------------
# Helper: build a "headless" App with mocked UI bits
# ---------------------------------------------------------------------------
def _make_app():
    """Return an App whose tk-dependent attrs are mocks, skipping UI build."""
    root = MagicMock()
    with patch("main.load_config", return_value={"email": "", "auth_code": "", "resume_path": ""}), \
         patch("main.load_history", return_value=[]):
        app = App.__new__(App)
        app.root = root
        app.config = {"email": "", "auth_code": "", "resume_path": "",
                      "personal": {"name": "", "phone": "", "school": "",
                                   "internship_duration": "", "arrival_time": "",
                                   "undergrad_school": "", "grad_school": "",
                                   "undergrad_major": "", "grad_major": "",
                                   "graduation_time": ""}}
        app.personal = app.config["personal"]
        app.records = []

        # StringVars (needs hidden root, created above)
        app.resume_path = tk.StringVar(value="")
        app.naming_format = tk.StringVar(value="")
        app.to_email = tk.StringVar(value="")
        app.email_user = tk.StringVar(value="")
        app.email_domain = tk.StringVar(value="")
        app.sender_email = tk.StringVar(value="")
        app.auth_code = tk.StringVar(value="")
        app.user_name = tk.StringVar(value="")
        app.user_phone = tk.StringVar(value="")
        app.user_school = tk.StringVar(value="")
        app.company_var = tk.StringVar(value="")
        app.position_var = tk.StringVar(value="")
        app.email_subject = tk.StringVar(value="实习申请")
        app.internship_duration = tk.StringVar(value="")
        app.arrival_time = tk.StringVar(value="")
        app.undergrad_school = tk.StringVar(value="")
        app.grad_school = tk.StringVar(value="")
        app.undergrad_major = tk.StringVar(value="")
        app.grad_major = tk.StringVar(value="")
        app.graduation_time = tk.StringVar(value="")

        # Mock job_text ScrolledText
        app.job_text = MagicMock()
        app.job_text.get.return_value = ""

        # Mock log area
        app.log_area = MagicMock()
        app.logs = []
        def fake_log(msg):
            app.logs.append(msg)
        app._log = fake_log

        return app


class TestUpdateSenderEmail(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()

    def test_both_present_concatenates(self):
        self.app.email_user.set("test")
        self.app.email_domain.set("@163.com")
        self.app._update_sender_email()
        self.assertEqual(self.app.sender_email.get(), "test@163.com")

    def test_only_user_no_domain(self):
        self.app.email_user.set("test")
        self.app.email_domain.set("")
        self.app._update_sender_email()
        self.assertEqual(self.app.sender_email.get(), "test")

    def test_only_domain_no_user(self):
        self.app.email_user.set("")
        self.app.email_domain.set("@qq.com")
        self.app._update_sender_email()
        self.assertEqual(self.app.sender_email.get(), "@qq.com")

    def test_both_empty(self):
        self.app.email_user.set("")
        self.app.email_domain.set("")
        self.app._update_sender_email()
        self.assertEqual(self.app.sender_email.get(), "")


class TestAppFillTemplate(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.app.user_name.set("王潇霄")
        self.app.user_phone.set("15994986362")
        self.app.user_school.set("对外经济贸易大学")
        self.app.sender_email.set("me@163.com")

    def test_name_school_position(self):
        fmt = "姓名-学校-岗位"
        result = self.app._fill_template(fmt, {"position": "投资经理助理", "company": "红杉资本"})
        self.assertEqual(result, "王潇霄-对外经济贸易大学-投资经理助理")

    def test_all_placeholders(self):
        fmt = "姓名+联系方式+学校+邮箱+应聘岗位"
        result = self.app._fill_template(fmt, {"position": "数据分析师", "company": "腾讯"})
        self.assertEqual(result, "王潇霄+15994986362+对外经济贸易大学+me@163.com+数据分析师")

    def test_company_placeholder(self):
        fmt = "公司-岗位-姓名"
        result = self.app._fill_template(fmt, {"position": "运营实习生", "company": "小红书"})
        self.assertEqual(result, "小红书-运营实习生-王潇霄")

    def test_no_info_placeholder_unchanged(self):
        fmt = "岗位-学校"
        result = self.app._fill_template(fmt, {})
        self.assertEqual(result, "岗位-对外经济贸易大学")

    def test_empty_personal_fields_skip_replacement(self):
        """Placeholders whose value is empty should stay in the template."""
        self.app.user_phone.set("")
        fmt = "姓名-手机号"
        result = self.app._fill_template(fmt, {})
        # phone is empty, so '手机号' stays as-is
        self.assertIn("手机号", result)

    def test_position_variants_all_replaced(self):
        """Both 岗位, 职位, 应聘岗位 should all map to the position value."""
        fmt = "应聘岗位_岗位_职位"
        result = self.app._fill_template(fmt, {"position": "产品经理"})
        self.assertEqual(result, "产品经理_产品经理_产品经理")


class TestAppSendValidation(unittest.TestCase):
    """Test the input validation in _send without touching SMTP."""

    def setUp(self):
        self.app = _make_app()

    def _call_send_and_capture_errors(self):
        """Call _send and return log lines containing '请填写'."""
        self.app.logs = []
        self.app._send()
        return [m for m in self.app.logs if "请填写" in m]

    def test_all_fields_empty_shows_all_errors(self):
        msgs = self._call_send_and_capture_errors()
        self.assertEqual(len(msgs), 1)
        self.assertIn("发件邮箱", msgs[0])
        self.assertIn("授权码", msgs[0])
        self.assertIn("对方邮箱", msgs[0])
        self.assertIn("命名格式", msgs[0])
        self.assertIn("原始简历", msgs[0])

    def test_missing_auth_code_only(self):
        self.app.sender_email.set("me@163.com")
        self.app.to_email.set("hr@company.com")
        self.app.naming_format.set("姓名-学校-岗位")
        self.app.resume_path.set("/fake/resume.pdf")
        msgs = self._call_send_and_capture_errors()
        self.assertIn("授权码", msgs[0])

    def test_missing_naming_format_only(self):
        self.app.sender_email.set("me@163.com")
        self.app.auth_code.set("secret")
        self.app.to_email.set("hr@company.com")
        self.app.resume_path.set("/fake/resume.pdf")
        msgs = self._call_send_and_capture_errors()
        self.assertIn("命名格式", msgs[0])

    def test_invalid_to_email_format(self):
        self.app.email_user.set("me")
        self.app.email_domain.set("@163.com")
        self.app.auth_code.set("secret")
        self.app.to_email.set("not-an-email")
        self.app.naming_format.set("简历")
        self.app.resume_path.set(__file__)  # existing file, passes file check
        self.app.logs = []
        self.app._send()
        warnings = [m for m in self.app.logs if "格式不正确" in m]
        self.assertEqual(len(warnings), 1)

    def test_resume_file_missing(self):
        self.app.sender_email.set("me@163.com")
        self.app.auth_code.set("secret")
        self.app.to_email.set("hr@company.com")
        self.app.naming_format.set("简历")
        self.app.resume_path.set("/nonexistent/file.pdf")
        self.app.logs = []
        self.app._send()
        errors = [m for m in self.app.logs if "原始简历文件不存在" in m]
        self.assertEqual(len(errors), 1)

    @patch("main.shutil.copy2")
    @patch("main.threading.Thread")
    def test_valid_inputs_proceed_to_send(self, mock_thread, mock_copy):
        """When all fields are valid, _send should not log validation errors."""
        self.app.email_user.set("me")
        self.app.email_domain.set("@163.com")
        self.app.auth_code.set("secret")
        self.app.to_email.set("hr@company.com")
        self.app.naming_format.set("姓名-学校")
        self.app.resume_path.set(__file__)
        self.app.job_text.get.return_value = "【字节】算法工程师 JD描述"
        self.app.send_btn = MagicMock()
        self.app.logs = []
        self.app._send()
        error_msgs = [m for m in self.app.logs if "请填写" in m or "格式不正确" in m]
        self.assertEqual(error_msgs, [])


class TestAppExtract(unittest.TestCase):
    """Test _extract method (smart extraction trigger)."""

    def setUp(self):
        self.app = _make_app()
        self.app.job_text.get.return_value = ""

    def test_empty_text_logs_warning(self):
        self.app.job_text.get.return_value = ""
        self.app._extract()
        self.assertTrue(any("请先粘贴" in m for m in self.app.logs))

    def test_populates_email_field(self):
        self.app.job_text.get.return_value = "联系邮箱: hr@abc.com"
        self.app._extract()
        self.assertEqual(self.app.to_email.get(), "hr@abc.com")

    def test_populates_naming_format(self):
        self.app.job_text.get.return_value = "简历命名格式：姓名_院校_应聘方向"
        self.app._extract()
        self.assertEqual(self.app.naming_format.get(), "姓名_院校_应聘方向")

    def test_no_extraction_shows_warning(self):
        self.app.job_text.get.return_value = "x"  # single char, no extractable info
        self.app._extract()
        self.assertTrue(any("未能提取到有效信息" in m for m in self.app.logs))


if __name__ == "__main__":
    unittest.main()
