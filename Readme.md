[![STOSCBot Build](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml/badge.svg)](https://github.com/viper25/stoscbot/actions/workflows/python-app.yml)  [![codecov](https://codecov.io/gh/viper25/stoscbot/branch/main/graph/badge.svg?token=QQ3WXQ2TSQ)](https://codecov.io/gh/viper25/stoscbot)

# STOSC Bot

A Telegram bot (based on [Pyrogram](https://docs.pyrogram.org/)) to manage affairs of the St. Thomas Orthodox Syrian
Cathedral (STOSC), Singapore.

> Since [Pyrogram](https://github.com/pyrogram/pyrogram) is no longer in active development, I've switched to a fork of
> Pyrogram called [KurimuzonAkuma](https://github.com/KurimuzonAkuma/pyrogram). Docs are
> at [pyrodocs.kurimuzon.ru](https://pyrodocs.kurimuzon.ru/)

![image](https://user-images.githubusercontent.com/327990/142089101-04f782d3-0982-4ac0-83d0-899d714bc1cb.png) ![02](https://user-images.githubusercontent.com/327990/142300513-b2cbde04-f695-40f3-92f3-5e56649550f9.png) ![markup_41332 (1)](https://user-images.githubusercontent.com/327990/145735665-da9a6c31-29cc-4a5e-8824-8cd8653b84f8.png)

## Setup

Create a `.env` file by modifying the [.env.sample](.env.sample)

```bash
uv sync
uv run python run_stoscbot.py
```

## Run Tests

```bash
uv sync --group test
uv run -m pytest
```

Using [pytest-cov](https://github.com/pytest-dev/pytest-cov)

```bash
pytest --cov=./ --cov-report=xml
coverage report
```
## Bump Version

Bump version explicitly `uv version 0.1.0` or [semantically](https://docs.astral.sh/uv/reference/cli/#uv-version--bump) `uv version --bump minor`

## Deployment

We use [GitHub Actions](https://github.com/viper25/stoscbot/actions) to deploy, but the basic deploy steps are lsited
below
<details>
<summary>Deploy on a VM</summary>

1. Update server timezone to local timezone
2. [Do not re-use](https://docs.pyrogram.org/faq/using-multiple-clients-at-once-on-the-same-account) a session file when
   deploying to a new instance. On a new instance, delete any existing `.session` file
   and [generate a new session file](https://docs.pyrogram.org/start/auth#bot-authorization).
3. Keep the `.env` and `.session` files in a `..\credentials\` directory.
   The [deployment scripts](.github\workflows\python-app.yml) will copy these files to the correct location.
4. Subsequently, run headless as ` nohup python3 run_stoscbot.py &`

</details>

## Activity

![Alt](https://repobeats.axiom.co/api/embed/8f7c105c760f4c1728a380d4940249878f8775b4.svg "Repobeats analytics image")

## TODO

* Make better decorators. See https://youtu.be/QH5fw9kxDQA?t=843
    * Add arguments to decorators(https://youtu.be/QH5fw9kxDQA?t=1164)
* [Define Default Values in Dictionaries With `.get()` and `.setdefault()`](https://realpython.com/python-coding-interview-tips/#define-default-values-in-dictionaries-with-get-and-setdefault)
* In iterating over long lists,
  use [generators](https://realpython.com/python-coding-interview-tips/#save-memory-with-generators)
* Check if using `logger` or `loggers` class
* [How to make a async function to async](https://youtu.be/GpqAQxH1Afc?t=968)
* Split the GitHub Actions Job `Build_Lint_Test_Coverage` to two jobs: `Build_Lint` and `Test_Coverage`. Use cache
* Change to dictionary `_get` e.g. `income = _item.get('income', 0.0)`

## Reference

* [Pyrogram version updates](https://github.com/pyrogram/pyrogram/compare/v2.0.34...v2.0.35) 