from jinja2 import Template

WELCOME_EMAIL_TEMPLATE = Template(
    """
<html>
  <body style="font-family: 'Inter', sans-serif; color: #ffffff; background: #0d0f1a;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px;">

      <h1 style="font-family: 'Instrument Serif', serif; font-size: 28px; text-align: center;">
        Welcome to Velorah
      </h1>

      <p style="text-align: center; color: #a6aeba; margin-top: 20px;">
        Hi {{ full_name }},
      </p>

      <p style="color: #a6aeba; line-height: 1.6; margin: 20px 0;">
        Thank you for signing up for the {{ plan_tier | title }} plan.
        {% if trial_ends %}Your 14-day free trial started today and ends {{ trial_ends }}.{% endif %}
      </p>

      <div style="background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.1);
                  border-radius: 12px; padding: 24px; margin: 30px 0;">
        <h2 style="font-family: 'Instrument Serif', serif; font-size: 18px; margin: 0 0 16px 0;">
          Your Plan Includes:
        </h2>
        <ul style="color: #a6aeba; line-height: 2;">
          {% for feature in features %}
            <li>&#10003; {{ feature }}</li>
          {% endfor %}
        </ul>
      </div>

      <div style="text-align: center; margin: 40px 0;">
        <a href="{{ dashboard_url }}"
           style="background: rgba(255, 255, 255, 0.1); color: #ffffff; padding: 12px 32px;
                  border-radius: 24px; text-decoration: none; display: inline-block;
                  border: 1px solid rgba(255, 255, 255, 0.2);">
          Launch Studio
        </a>
      </div>

      <p style="color: #7a7e8a; font-size: 12px; text-align: center; margin-top: 40px;">
        Questions? Contact <a href="mailto:{{ support_email }}" style="color: #ffffff;">{{ support_email }}</a>
      </p>

    </div>
  </body>
</html>
"""
)

PAYMENT_FAILED_TEMPLATE = Template(
    """
<html>
  <body style="font-family: 'Inter', sans-serif; color: #ffffff; background: #0d0f1a;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px;">

      <h1 style="font-family: 'Instrument Serif', serif; font-size: 28px; color: #ff6b6b;">
        Payment Failed
      </h1>

      <p style="color: #a6aeba; margin-top: 20px;">
        Hi {{ full_name }},
      </p>

      <p style="color: #a6aeba; line-height: 1.6;">
        Your recent payment of ${{ '%.2f' | format(amount) }} failed. Your {{ plan_tier | title }} subscription is now paused.
      </p>

      <div style="background: rgba(255, 107, 107, 0.1); border: 1px solid rgba(255, 107, 107, 0.3);
                  border-radius: 12px; padding: 16px; margin: 20px 0;">
        <p style="color: #ff6b6b; margin: 0;">
          <strong>Action required:</strong> update your payment method to continue.
        </p>
      </div>

      <div style="text-align: center; margin: 30px 0;">
        <a href="{{ billing_url }}"
           style="background: rgba(255, 255, 255, 0.1); color: #ffffff; padding: 12px 32px;
                  border-radius: 24px; text-decoration: none; display: inline-block;
                  border: 1px solid rgba(255, 255, 255, 0.2);">
          Update Payment Method
        </a>
      </div>

    </div>
  </body>
</html>
"""
)

PASSWORD_RESET_TEMPLATE = Template(
    """
<html>
  <body style="font-family: 'Inter', sans-serif; color: #ffffff; background: #0d0f1a;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px;">

      <h1 style="font-family: 'Instrument Serif', serif; font-size: 28px; text-align: center;">
        Reset your password
      </h1>

      <p style="color: #a6aeba; margin-top: 20px;">
        Hi {{ full_name }},
      </p>

      <p style="color: #a6aeba; line-height: 1.6;">
        We received a request to reset your password. This link expires in {{ expires_minutes }} minutes.
        If you didn't request this, you can safely ignore this email.
      </p>

      <div style="text-align: center; margin: 30px 0;">
        <a href="{{ reset_url }}"
           style="background: rgba(255, 255, 255, 0.1); color: #ffffff; padding: 12px 32px;
                  border-radius: 24px; text-decoration: none; display: inline-block;
                  border: 1px solid rgba(255, 255, 255, 0.2);">
          Reset Password
        </a>
      </div>

    </div>
  </body>
</html>
"""
)

PASSWORD_CHANGED_TEMPLATE = Template(
    """
<html>
  <body style="font-family: 'Inter', sans-serif; color: #ffffff; background: #0d0f1a;">
    <div style="max-width: 600px; margin: 0 auto; padding: 40px;">

      <h1 style="font-family: 'Instrument Serif', serif; font-size: 28px; text-align: center;">
        Your password was changed
      </h1>

      <p style="color: #a6aeba; margin-top: 20px;">
        Hi {{ full_name }},
      </p>

      <p style="color: #a6aeba; line-height: 1.6;">
        This is a confirmation that your Velorah account password was just changed. If this wasn't you,
        contact <a href="mailto:{{ support_email }}" style="color: #ffffff;">{{ support_email }}</a> immediately.
      </p>

    </div>
  </body>
</html>
"""
)
