from unittest.mock import patch

from app.services.email_service import send_email


@patch.dict(
    "os.environ",
    {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM_EMAIL": "test@example.com",
    },
)
@patch("app.services.email_service.smtplib.SMTP")
def test_send_email_success(mock_smtp):
    mock_server = mock_smtp.return_value.__enter__.return_value

    result = send_email(
        "recipient@example.com",
        "Test Subject",
        "Test email body",
    )

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with(
        "test@example.com",
        "test-password",
    )
    mock_server.send_message.assert_called_once()


@patch.dict(
    "os.environ",
    {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "test@example.com",
        "SMTP_PASSWORD": "test-password",
        "SMTP_FROM_EMAIL": "test@example.com",
    },
)
@patch("app.services.email_service.smtplib.SMTP")
def test_send_email_failure(mock_smtp):
    mock_smtp.side_effect = OSError("SMTP connection failed")

    result = send_email(
        "recipient@example.com",
        "Test Subject",
        "Test email body",
    )

    assert result is False


@patch.dict("os.environ", {}, clear=True)
def test_send_email_missing_configuration():
    result = send_email(
        "recipient@example.com",
        "Test Subject",
        "Test email body",
    )

    assert result is False