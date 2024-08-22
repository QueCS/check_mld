import os
import tomllib
import time
import json
import highscores as hs
import players as pl
import datetime
import logging
import dhooks

os.chdir(f"{os.path.dirname(__file__)}")

with open("../config.toml", "rb") as config_file:
    config = tomllib.load(config_file)

md_log_dir = config.get("MD_BOT", {}).get("md_log_dir")
md_file_dir = config.get("MD_BOT", {}).get("md_file_dir")
server = config.get("MD_BOT", {}).get("md_server")
community = config.get("MD_BOT", {}).get("md_community")
md_hook = dhooks.Webhook(config.get("MD_BOT", {}).get("md_webhook"))
syntax = config.get("PL_FORMAT", {}).get("syntax")

logging.basicConfig(
    filename=f"{md_log_dir}",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)


def main():
    init_md_file(server, community, md_file_dir)
    check_md(server, community)


def check_md(server: int, community: str):
    logging.info("Starting up check_md")

    while True:
        time.sleep(60)

        with open(md_file_dir, "r") as file:
            old_md = json.load(file)
        old_ts = int(old_md.get("timestamp"))

        current_time = datetime.datetime.now()
        current_ts = int(current_time.timestamp())

        retry_count = 0
        max_retries = 6

        if current_ts > old_ts + 3600:
            new_md, payload = compare_md(server, community, old_md, old_ts)

            if payload is False:
                continue

            logging.info("Sending payload")

            while retry_count < max_retries:
                try:
                    md_hook.send(payload)
                    logging.info("Done\n")
                    update_md_file(new_md, md_file_dir)
                    break
                except Exception as exception:
                    logging.warning(f"Calling hook.send(): {exception}")
                    logging.warning(
                        f"Payload not sent, waiting 10s and trying again ({retry_count}/{max_retries})"
                    )
                    retry_count += 1
                    time.sleep(10)

            if retry_count == max_retries:
                logging.warning(
                    "Maximum dhook retries reached. Re-computing differences\n"
                )

            continue


def compare_md(server: int, community: str, old_md, old_ts):
    md_api = hs.get_highscore_api(server, community, 1, 6)
    if md_api is None:
        return False, False
    new_ts = md_api.timestamp()

    if old_ts == new_ts:
        logging.info(
            f"Timestamps match: {old_ts} == {new_ts}, API not updated, exiting\n"
        )
        return False
    logging.info(
        f"Timestamps differ: {old_ts} != {new_ts}, API updated, computing differences"
    )

    new_md = md_api.data_dict()

    pl_api = pl.get_players_api(server, community)

    payload = ""

    common_keys = old_md.keys() & new_md.keys()
    for key in common_keys:
        if key not in ("timestamp", "server"):
            name = pl_api.name_from_id(key)
            if name is None:
                name = key
            diff = new_md[key]["score"] - old_md[key]["score"]
            if diff != 0:
                payload += f"\n{name.ljust(22)} + {diff:,}"

    lines = payload.strip().split("\n")
    sorted_lines = sorted(
        lines,
        key=lambda x: float(x.split("+")[-1].replace(",", "").strip()),
        reverse=True,
    )
    payload = "\n".join(sorted_lines)

    if len(payload) > 1800:
        payload = truncate_payload(payload, 1800, "[TRUNCATED]")

    update_datetime = datetime.datetime.fromtimestamp(new_ts)
    payload = f"```{syntax}\n{update_datetime}\n\n{payload}\n```"

    payload = payload.replace(",", ".")

    return new_md, payload


def update_md_file(data, dir):
    logging.info(f"Updating {dir}")
    with open(md_file_dir, "w") as file:
        json.dump(data, file)
    logging.info("Done\n")


def init_md_file(server, community, dir):
    logging.info(f"Bot initial start-up, initializing {dir}")
    md_api = hs.get_highscore_api(server, community, 1, 6)
    md_api.json_export(dir)
    logging.info("Initialization complete\n")


def truncate_payload(string, max_length, cutoff_string):
    lines = string.split("\n")
    remaining_lines = []
    current_length = 0

    for line in lines:
        if current_length + len(line) + len(cutoff_string) <= max_length:
            remaining_lines.append(line)
            current_length += len(line)

    shortened_string = "\n".join(remaining_lines) + f"\n{cutoff_string}"
    return shortened_string


if __name__ == "__main__":
    main()
