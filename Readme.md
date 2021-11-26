[![STOSCBot Build](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml/badge.svg)](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml)

# STOSC Bot
St. Thomas Orthodox Syrian Cathedral's Telegram Bot

![image](https://user-images.githubusercontent.com/327990/142089101-04f782d3-0982-4ac0-83d0-899d714bc1cb.png) ![02](https://user-images.githubusercontent.com/327990/142300513-b2cbde04-f695-40f3-92f3-5e56649550f9.png)



## Setup your virtual environment. 
```bash
python -m venv .venv
```

Activate (on Windows):
```dos
.venv\Scripts\activate.bat
```

On Linux:

Change `config.ini` for server. 

```bash
source .venv/bin/activate
nohup python3 run_stoscbot.py &
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Upgrade dependencies

```bash
pip install --upgrade -r requirements.txt
```


[Reference](https://docs.pyrogram.org/)

Good Reference on structuring Python project: 
https://github.com/Fumaz/TTSBot

Pyrogram uses persistent connections via TCP sockets to interact with the server and instead of actively asking for updates every time (polling), Pyrogram will simply sit down and wait for the server to send updates by itself the very moment they are available (server push).

## Deployment
<details>
<summary>Deploy on a VM</summary>

1. Create a new session file when deploying to a new instance. To do so, delete any existing `.session` file and run `python3 run_stoscbot.py` and enter the bot ID to create new `*.session` files. Ensure [config.ini](https://docs.pyrogram.org/topics/config-file#the-config-ini-file) is present.
2. Copy the [Google API keys](https://console.cloud.google.com/iam-admin/serviceaccounts/details/104130143367587513093;edit=true/keys?project=api-project-57990973458) to `~/.config/gspread/service_account.json`
3. Subsequently run headless as ` nohup python3 run_stoscbot.py &`
</details>

<details>
<summary>Azure App Service Deployment
</summary>


1. In `.vscode\settings.json` set files to be ignored under the key `appService.zipIgnorePattern`.

    ```json
    {
        "appService.defaultWebAppToDeploy": "/subscriptions/xxx-xxx-xxx-xxx-xxx/resourceGroups/STOSC/providers/Microsoft.Web/sites/stosc-bot-2",
        "appService.deploySubpath": ".",
        "appService.zipIgnorePattern": [
            ".venv{,/**}",
            ".vscode{,/**}",
            ".github{,/**}",
            "__pycache__{,/**}",
            ".git{,/**}",
            ".env{,/**}"
        ],
    }
    ```
2. Add Timezone as an Application Settings variable i.e. `TZ=Asia/Singapore`
3. Set a startup script in Azure Console under `Startup Command`. This is what will be used to start the bot (do not ignore the `.session` file). 
4. It is expected the app provide an application running at port 8000. If not, the Azure App Service container will stop after a while (and our bot process will be killed). 
</details>