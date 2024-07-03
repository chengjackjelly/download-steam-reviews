import csv
import datetime
import os
import pathlib
import re
from http import HTTPStatus
from multiprocessing import Pool
from pathlib import Path
from typing import Tuple

import requests



def get_request(chosen_request_params: dict = None) -> dict:  # type: ignore
    """get request parameter and set appid"""
    request = dict(get_default_request_parameters(chosen_request_params))
    return request


def get_default_request_parameters(chosen_request_params=None):
    """Objective: return a dict of default paramters for a request to Steam API.
    #
    # References:
    #   https://partner.steamgames.com/doc/store/getreviews
    #   https://partner.steamgames.com/doc/store/localization#supported_languages
    #   https://gist.github.com/adambuczek/95906b0c899c5311daeac515f740bf33
    """
    default_request_parameters = {
        "json": "1",
        "language": "english",  # API language code e.g. english or schinese
        "filter": "recent",  # To work with 'start_offset', 'filter' has to be set to either recent or updated, not all.
        "review_type": "all",  # e.g. positive or negative
        "purchase_type": "all",  # e.g. steam or non_steam_purchase
        "num_per_page": "100",  # default is 20, maximum is 100
    }

    if chosen_request_params is not None:
        for element in chosen_request_params:
            default_request_parameters[element] = chosen_request_params[element]

    return default_request_parameters


def get_steam_api_url(app_id: str) -> str:
    """get api for app_id"""
    return f"https://store.steampowered.com/appreviews/{app_id}"


def download_reviews_for_app_id_with_offset(
    app_id: str,
    cursor: str = "*",
    chosen_request_params: dict = None,  # type: ignore
) -> dict:
    """download reviews with offset. only one api request is send here"""
    req_data = get_request(chosen_request_params)
    req_data["cursor"] = cursor

    resq_data = requests.get(get_steam_api_url(app_id), params=req_data, timeout=10)
    status_code = resq_data.status_code
    if status_code == HTTPStatus.OK:
        result = resq_data.json()
    else:
        result = {"success": 0}
        print(f"Faulty response status code{status_code} for appid {app_id}")
    return result


def get_data_path() -> Path:
    """return the directory of where data is stored, create one if not exist"""
    data_path = "data/"

    pathlib.Path(data_path).mkdir(parents=True, exist_ok=True)

    return pathlib.Path(data_path)


def get_dummy_query_summary():
    query_summary = {}
    query_summary["total_reviews"] = -1

    return query_summary


def get_output_filename(app_id: str) -> Path:
    return Path.joinpath(get_data_path(), f"review_{app_id}.csv")


def load_downloaded_review_info(app_id: str) -> Tuple[str, set, int]:
    review_data_file_name = get_output_filename(app_id)
    recommendation_ids = set()
    last_cursor = "*"
    num_reviews = 0
    if review_data_file_name.exists():
        print("Start from the last time....")
        with open(
            review_data_file_name, mode="r", newline="", encoding="utf-8"
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            total_lines = len(rows)
            for ix, row in enumerate(rows):
                recommendation_ids.add(row["recommendationid"])
                if ix == total_lines - 1:
                    last_cursor = row["cursor"]
                    num_reviews = int(row["total_reviews"])
    return last_cursor, recommendation_ids, num_reviews


def filter_reviews_by_id(json_data: dict, exclude_ids: set) -> dict:
    filtered_reviews = [
        item
        for item in json_data["reviews"]
        if item["recommendationid"] not in exclude_ids
    ]
    json_data["reviews"] = filtered_reviews
    return json_data


def download_reviews_for_app_id(
    app_id: str,
    chosen_request_params: dict = None,
    start_cursor: str = "*",  # type: ignore
):
    """download all reviews for a app"""
    offset = 0
    cursor = start_cursor

    requests = get_default_request_parameters(
        chosen_request_params=chosen_request_params
    )
    cursor, dowloaded_review_id, num_reviews = load_downloaded_review_info(app_id)
    review_data_file_name = get_output_filename(app_id)
    offset = len(dowloaded_review_id)
    print(f"already download {offset} for current appid {app_id}, start from {cursor}")
    while (num_reviews == 0) or (offset < num_reviews):
        print(f"Cursor: {cursor}")
        result = download_reviews_for_app_id_with_offset(
            app_id, cursor=cursor, chosen_request_params=requests
        )
        assert result["success"] == 1

        cursor = result["cursor"]
        filtered_result = filter_reviews_by_id(result, dowloaded_review_id)

        if num_reviews == 0:
            num_reviews = result["query_summary"]["total_reviews"]
        if len(result["reviews"]) == 0:
            print(f"all reviews from appid {app_id} have been fetched")
            return
        write_result_to_csv(
            app_id, review_data_file_name, filtered_result, num_reviews, offset == 0
        )
        offset = offset + result["query_summary"]["num_reviews"]


def write_result_to_csv(
    app_id: str, csv_file_name: Path, result: dict, num_reviews: int, first_time: bool
) -> None:
    assert result["success"] == 1
    assert len(result["reviews"]) != 0
    if first_time:
        if os.path.exists(csv_file_name):
            # Remove the file
            os.remove(csv_file_name)
    review_list = []
    for review in result["reviews"]:
        flattened_data = {
            "recommendationid": review["recommendationid"],
            "appid": app_id,
            "steamid": review["author"]["steamid"],
            "num_games_owned": review["author"]["num_games_owned"],
            "num_reviews": review["author"]["num_reviews"],
            "playtime_forever": review["author"]["playtime_forever"],
            "playtime_last_two_weeks": review["author"]["playtime_last_two_weeks"],
            "playtime_at_review": review["author"]["playtime_at_review"],
            "last_played": review["author"]["last_played"],
            "language": review["language"],
            "review": review["review"],
            "timestamp_created": review["timestamp_created"],
            "timestamp_updated": review["timestamp_updated"],
            "voted_up": review["voted_up"],
            "votes_up": review["votes_up"],
            "votes_funny": review["votes_funny"],
            "weighted_vote_score": review["weighted_vote_score"],
            "comment_count": review["comment_count"],
            "steam_purchase": review["steam_purchase"],
            "received_for_free": review["received_for_free"],
            "written_during_early_access": review["written_during_early_access"],
            "hidden_in_steam_china": review["hidden_in_steam_china"],
            "steam_china_location": review["steam_china_location"],
            "cursor": result["cursor"],
            "total_reviews": num_reviews,
        }
        review_list.append(flattened_data)
    csv_columns = list(review_list[0].keys())
    with open(csv_file_name, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        if first_time:
            writer.writeheader()
        for review in review_list:
            writer.writerow(review)
    print(f'{len(result["reviews"])} new reviews have been written into file ')


def get_log_file_name() -> str:
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_file_name = f"log/log_{formatted_date}.txt"
    return log_file_name


def read_appid() -> list:
    with open("appid.txt", "r", encoding="utf-8") as f:
        text = f.read()
        pattern = r"/app/(\d+)/"
        appids = re.findall(pattern, text)
        return list(appids)


def download() -> None:
    appids = read_appid()
    with Pool(5) as p:
        p.map(download_reviews_for_app_id, appids)  # type: ignore
    # for appid in appids:
    #    download_reviews_for_app_id(appid)


if __name__ == "__main__":
    download()
