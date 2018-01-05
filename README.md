# Steepshot Telegram bot

This bot allows you to post photos to [Steepshot](<https://steepshot.io>) using your Steem-account.
Click [here](<https://t.me/SteepshotBot>) to start posting your great pics!

##### How to deploy telegram bot in your host

1. Enter your domain name in "settings.py" **line 20**.

For example:
```python
20. WEBHOOK_HOST = 'bot.mydomain.org'
```

2. Change the file "nginx.conf.j2", **lines 5,6**. Enter path to your ssl certificate.

For example:
```bash
5. ssl_certificate /path/to/file/fullchain.pem;
6. ssl_certificate_key /path/to/file/privkey.pem;
```

3. Change deploy variables in "deploy_settings.py" file, **lines 3,6 and 42**.

For example:
```python
3. HOST = '138.10.24.35'
...
6. CURRENT_HOST = 'bot.mydomain.org'
...
42. DB_PASSWORD = 'NiCE0OqyPtxZ'
```

4. If you deploying first time you need to run the following command:

```bash
fab production first_time_deploy
```

otherwise

```bash
fab production deploy
```

**NOTE**

During deploying you will see the following message: *Please enter your token:*.
It means that you need enter your private telegram bot token.

