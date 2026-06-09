"""
Mock SMTP tests — verify email assembly and sending flow without real network.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import send_email, get_smtp_config


class TestSendEmailSmtpFlow(unittest.TestCase):
    def setUp(self):
        self.sender = "me@163.com"
        self.auth = "test_auth_code"
        self.to = "hr@company.com"
        self.subject = "字节跳动 - 前端实习生 实习申请"
        self.body = "您好，请查收附件简历。"
        self.fake_pdf = b"%PDF-1.4 fake pdf content"

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_ssl_send_flow_163(self, mock_ssl, mock_file):
        """163 uses port 465 → SMTP_SSL, no starttls."""
        send_email(self.sender, self.auth, self.to, self.subject,
                   self.body, "/fake/resume.pdf")

        # SMTP_SSL should be called with correct server and port
        mock_ssl.assert_called_once_with("smtp.163.com", 465, timeout=30)
        server = mock_ssl.return_value
        # login then sendmail
        server.login.assert_called_once_with(self.sender, self.auth)
        self.assertEqual(server.sendmail.call_count, 1)
        # quit always called
        server.quit.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP")
    def test_tls_send_flow_outlook(self, mock_smtp, mock_file):
        """Outlook uses port 587 → SMTP + starttls."""
        send_email("me@outlook.com", self.auth, self.to, self.subject,
                   self.body, "/fake/resume.pdf")

        mock_smtp.assert_called_once_with("smtp-mail.outlook.com", 587, timeout=30)
        server = mock_smtp.return_value
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("me@outlook.com", self.auth)
        self.assertEqual(server.sendmail.call_count, 1)
        server.quit.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_email_content_assembly(self, mock_ssl, mock_file):
        """Verify the assembled email has correct headers, attachment name, and MIME structure."""
        send_email(self.sender, self.auth, self.to, "Test Subject",
                   "Hello, world!", "/fake/resume.pdf")

        server = mock_ssl.return_value
        call_args = server.sendmail.call_args
        self.assertEqual(call_args[0][0], self.sender)
        self.assertEqual(call_args[0][1], self.to)
        raw_msg = call_args[0][2]

        self.assertIn("From: me@163.com", raw_msg)
        self.assertIn("To: hr@company.com", raw_msg)
        self.assertIn("Subject:", raw_msg)
        # Attachment filename present
        self.assertIn("resume.pdf", raw_msg)
        # MIME multipart structure
        self.assertIn("multipart/mixed", raw_msg)
        self.assertIn("Content-Type: application/pdf", raw_msg)

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_attachment_file_is_read(self, mock_ssl, mock_file):
        send_email(self.sender, self.auth, self.to, self.subject,
                   self.body, "/path/to/my_resume.pdf")

        mock_file.assert_called_once_with("/path/to/my_resume.pdf", "rb")

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_server_quit_on_success(self, mock_ssl, mock_file):
        send_email(self.sender, self.auth, self.to, self.subject,
                   self.body, "/fake/resume.pdf")
        mock_ssl.return_value.quit.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_server_quit_on_login_failure(self, mock_ssl, mock_file):
        """quit() must be called even when login raises."""
        mock_ssl.return_value.login.side_effect = Exception("auth failed")
        with self.assertRaises(Exception):
            send_email(self.sender, self.auth, self.to, self.subject,
                       self.body, "/fake/resume.pdf")
        mock_ssl.return_value.quit.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_unknown_domain_uses_ssl(self, mock_ssl, mock_file):
        """Unknown domains default to port 465 → SMTP_SSL."""
        send_email("me@customcorp.com", self.auth, self.to,
                   self.subject, self.body, "/fake/resume.pdf")
        mock_ssl.assert_called_once_with("smtp.customcorp.com", 465, timeout=30)

    @patch("builtins.open", new_callable=mock_open, read_data=b"%PDF-1.4 fake pdf content")
    @patch("smtplib.SMTP_SSL")
    def test_sendmail_args(self, mock_ssl, mock_file):
        send_email(self.sender, self.auth, "hr@target.cn",
                   "主题", "正文", "/fake/resume.pdf")
        server = mock_ssl.return_value
        server.sendmail.assert_called_once_with(
            self.sender, "hr@target.cn", unittest.mock.ANY
        )


if __name__ == "__main__":
    unittest.main()
