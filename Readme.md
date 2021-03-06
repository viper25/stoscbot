[![STOSCBot Build](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml/badge.svg)](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml)  [![codecov](https://codecov.io/gh/viper25/stoscbot/branch/main/graph/badge.svg?token=QQ3WXQ2TSQ)](https://codecov.io/gh/viper25/stoscbot)

# STOSC Bot
A Telegram bot (based on [Pyrogram](https://docs.pyrogram.org/)) to manage affairs of the St. Thomas Orthodox Syrian Cathedral (STOSC), Singapore.

![image](https://user-images.githubusercontent.com/327990/142089101-04f782d3-0982-4ac0-83d0-899d714bc1cb.png) ![02](https://user-images.githubusercontent.com/327990/142300513-b2cbde04-f695-40f3-92f3-5e56649550f9.png) ![markup_41332 (1)](https://user-images.githubusercontent.com/327990/145735665-da9a6c31-29cc-4a5e-8824-8cd8653b84f8.png)




## Setup 
<details>

<summary>
Setup virtual environment
</summary>

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
</details>

<details>

<summary>
Dependencies
</summary>

## Install dependencies.

```bash
pip install -r requirements.txt
```

### Upgrade dependencies

Upgrade dependencies, test lcoally and then freeze to `requirements_pro.txt`

```bash
pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip freeze > requirements_pro.txt
```
</details>

<details>
<summary>
Tests
</summary>

## Run Tests

Ensure `pytest` and `pytest-asyncio` is installed so that VSCode and "find" tests. Run the below command to run the tests.

```bash

```bash
pytest --cov=./ --cov-report=xml
coverage report
```
</details>

## Deployment
<details>
<summary>Deploy on a VM</summary>

1. [Do not re-use](https://docs.pyrogram.org/faq/using-multiple-clients-at-once-on-the-same-account) a session file when deploying to a new instance. On a new isntance, delete any existing `.session` file and [generate a new session file](https://docs.pyrogram.org/start/auth#bot-authorization).
2. Keep the `.env` and `.session` files in a `..\credentials\` directory. The [deployment scripts](.github\workflows\python-app.yml) will copy these files to the correct location.
3. Copy the [Google API keys](https://console.cloud.google.com/iam-admin/serviceaccounts/details/104130143367587513093;edit=true/keys?project=api-project-57990973458) to `~/.config/gspread/service_account.json`
4. Subsequently run headless as ` nohup python3 run_stoscbot.py &`
</details>

<details>
<summary>Azure App Service Deployment
</summary>

>Not being used at present

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
3. Set a startup script in Azure Console under `Startup Command`. This is what will be used to start the bot (do not ignore to create the Pyrogram `.session` file). 
4. It is expected the app provide an application running at port 8000. If not, the Azure App Service container will stop after a while (and our bot process will be killed). 
</details>

## TODO

* [Define Default Values in Dictionaries With `.get()` and `.setdefault()`](https://realpython.com/python-coding-interview-tips/#define-default-values-in-dictionaries-with-get-and-setdefault)
* In iterating over long lists, use [generators](https://realpython.com/python-coding-interview-tips/#save-memory-with-generators)
* Check if using `logger` or `loggers` class
* ~~Update Build Numbers and versions~~
* [How to make a sync function to async](https://youtu.be/GpqAQxH1Afc?t=968)