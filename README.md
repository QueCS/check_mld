# Check Military Lost and Destroyed

Python scripts checking Military Lost and Destroyed point variation on [OGame public APIs](https://forum.origin.ogame.gameforge.com/forum/thread/44-ogame-api/).

At each API update (every hour or so) the bot will fetch the APIs, compare previous (localy stored as JSON) and current values and send the difference over the past hour to the [Discord webhook](https://hookdeck.com/webhooks/platforms/how-to-get-started-with-discord-webhooks) of your choice.

## Getting started

Clone the repository at the desired location.
```bash
git clone https://github.com/QueCS/check_mld.git
```
\
Hop into it.
```bash
cd check_mld
```
\
Set the appropriate python virtual environment used in further steps.
```bash
python3 -m venv .venv
```
\
Install necessary dependencies in the virtual environment.
```bash
.venv/bin/pip3 install -r requirements.txt
```
\
Adjust the configuration file using the text editor of your liking and save it as `config.toml`.\
Both `md` and `ml` configurations work the same.

`md_server` = '*server_nb*' (e.g. '123')\
`md_community` = '*community_id*' (e.g. 'fr')\
`md_webhook` = '*discord_webhook*' (do NOT share this token with ANYBODY)

You can adjust data and log directories but you will need to copy over the provided data and log files.

`md_log_dir` = '*directory of your choice*'\
`md_file_dir` = '*directory of your choice*'

You can configure the format of the output, see [here](https://gist.github.com/matthewzring/9f7bbfd102003963f9be7dbcf7d40e51#syntax-highlighting) for supported language formats.

`syntax` = '*language of your choice*' (e.g. 'cpp')

\
Finally, launch the bots using the virtual environment.
```bash
.venv/bin/python3 src/md_bot.py &
.venv/bin/python3 src/ml_bot.py &
```
\
Note that in most cases, exiting the current terminal will kill the execution of the bot.\
To avoid that you can [disown](https://linuxcommand.org/lc3_man_pages/disownh.html) it (among other methods).
```bash
$ jobs
[1]+  6392 Running          .venv/bin/python3 src/md_bot.py &
[2]+  6393 Running          .venv/bin/python3 src/ml_bot.py &

$ disown 6392 6393
```

## One-liner installation
```bash
git clone https://github.com/QueCS/check_mld.git && cd check_mld && python3 -m venv .venv && .venv/bin/pip3 install -r requirements.txt
```

## Disclaimer

[OGame](https://gameforge.com/play/ogame) is a registered trademark of [Gameforge Productions GmbH](https://gameforge.com).\
I am not affiliated with, endorsed by, or in any way officially connected to Gameforge Productions GmbH.
