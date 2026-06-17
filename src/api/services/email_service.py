from __future__ import annotations

import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Callable

from fastapi import BackgroundTasks

from config.logger import logger
from config.settings import settings


class EmailService:
    """Serviço de envio de emails via SMTP."""

    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.from_email = settings.EMAIL_FROM or self.user
        self.from_name = settings.EMAIL_FROM_NAME

    def _generate_code(self, length: int = 6) -> str:
        """Gera código numérico aleatório de verificação."""
        return ''.join(secrets.choice('0123456789') for _ in range(length))

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Cria e configura conexão SMTP."""
        smtp = smtplib.SMTP(self.host, self.port)
        smtp.ehlo()
        if self.use_tls:
            smtp.starttls()
            smtp.ehlo()
        if self.user and self.password:
            smtp.login(self.user, self.password)
        return smtp

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Envia email via SMTP."""
        if not all([self.host, self.user, self.password]):
            logger.error("Configuração SMTP incompleta. Verifique as variáveis de ambiente.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email

        # Adiciona versão texto simples
        if text_content:
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

        # Adiciona versão HTML
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg)
            logger.info("Email enviado com sucesso para %s", to_email)
            return True
        except Exception as e:
            logger.error("Erro ao enviar email para %s: %s", to_email, e)
            return False

    def _get_verification_email_template(self, name: str, code: str) -> str:
        """Retorna template HTML para email de verificação."""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificação de Email - MeraKia</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #165c7d 0%, #7d3716 100%);
            padding: 40px 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #165c7d 0%, #7d3716 100%);
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .header p {{
            color: rgba(255,255,255,0.9);
            font-size: 16px;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 16px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 30px;
        }}
        .code-box {{
            background: linear-gradient(135deg, #165c7d 0%, #7d3716 100%);
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .code-label {{
            color: rgba(255,255,255,0.9);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }}
        .code {{
            color: #ffffff;
            font-size: 42px;
            font-weight: 700;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        .instructions {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .instructions h3 {{
            color: #333;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .instructions ol {{
            color: #666;
            font-size: 14px;
            padding-left: 20px;
            line-height: 1.8;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 20px;
        }}
        .warning p {{
            color: #856404;
            font-size: 14px;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        .footer p {{
            color: #999;
            font-size: 13px;
            margin-bottom: 5px;
        }}
        .footer .brand {{
            color: #165c7d;
            font-weight: 600;
        }}
        @media (max-width: 480px) {{
            .header h1 {{ font-size: 24px; }}
            .code {{ font-size: 32px; letter-spacing: 6px; }}
            .content {{ padding: 30px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MeraKia</h1>
            <p>Verificação de Email</p>
        </div>
        <div class="content">
            <p class="greeting">Olá, <strong>{name}</strong>!</p>
            <p class="message">
                Bem-vindo(a) à MeraKia! Para ativar sua conta e começar a usar nossa plataforma,
                precisamos verificar seu endereço de email. Use o código abaixo:
            </p>
            <div class="code-box">
                <p class="code-label">Seu Código de Verificação</p>
                <p class="code">{code}</p>
            </div>
            <div class="instructions">
                <h3>Como verificar seu email:</h3>
                <ol>
                    <li>Faça login na plataforma MeraKia</li>
                    <li>Acesse a seção "Verificar Email" nas configurações</li>
                    <li>Digite o código acima</li>
                    <li>Pronto! Sua conta será ativada</li>
                </ol>
            </div>
            <div class="warning">
                <p><strong>Importante:</strong> Este código expira em 30 minutos. Se não verificar a tempo, poderá solicitar um novo código na plataforma.</p>
            </div>
        </div>
        <div class="footer">
            <p>Se você não criou uma conta na MeraKia, ignore este email.</p>
            <p class="brand">MeraKia - Inteligência Artificial para Artesanato</p>
        </div>
    </div>
</body>
</html>
"""

    def send_verification_email(self, to_email: str, name: str) -> tuple[bool, str]:
        """
        Envia email de verificação e retorna o código gerado.
        Retorna: (sucesso, codigo)
        """
        code = self._generate_code(6)
        subject = "Verifique seu email - MeraKia"
        html_content = self._get_verification_email_template(name, code)
        text_content = f"""
Olá, {name}!

Bem-vindo(a) à MeraKia! Para ativar sua conta, use o código de verificação:

CÓDIGO: {code}

Este código expira em 30 minutos.

Se você não criou uma conta na MeraKia, ignore este email.

MeraKia - Inteligência Artificial para Artesanato
"""

        success = self._send_email(to_email, subject, html_content, text_content)
        return success, code if success else ""

    def send_verification_email_background(
        self,
        background_tasks: BackgroundTasks,
        to_email: str,
        name: str,
        on_complete: Optional[Callable[[str, str], None]] = None,
    ) -> str:
        """
        Agenda envio de email de verificação em background.
        Retorna o código gerado imediatamente.
        """
        code = self._generate_code(6)
        subject = "Verifique seu email - MeraKia"
        html_content = self._get_verification_email_template(name, code)
        text_content = f"""
Olá, {name}!

Bem-vindo(a) à MeraKia! Para ativar sua conta, use o código de verificação:

CÓDIGO: {code}

Este código expira em 30 minutos.

Se você não criou uma conta na MeraKia, ignore este email.

MeraKia - Inteligência Artificial para Artesanato
"""

        def _send_and_callback():
            success = self._send_email(to_email, subject, html_content, text_content)
            if success and on_complete:
                try:
                    on_complete(to_email, code)
                except Exception as e:
                    logger.error("Erro no callback de email: %s", e)
            elif not success:
                logger.error("Falha ao enviar email de verificação para %s", to_email)

        background_tasks.add_task(_send_and_callback)
        return code


email_service = EmailService()
