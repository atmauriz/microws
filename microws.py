import argparse
import json
import logging
import os
import shlex
import subprocess

from flask import Flask, jsonify, request, abort

################################
# LOGGING SETUP ################
################################
logging.basicConfig(level=logging.DEBUG)

################################
# STATIC VARIABLES #############
################################
CONTENT_FILENAME = None
CONTENT_DATA = None
KEYS_ = ["udid", "data"]
BASE_COMMAND_LINE = "echo"


################################
# SHORTCUTs utils ##############
################################
def load_content_from_file(file_: str) -> str:
    """
    Load content from file.

    :param file_: path to content file
    :return: str
    """
    if not os.path.exists(file_):
        raise FileNotFoundError(f"{file_} does not exist")
    logging.info(f"Processing read content file from: {file_}")
    with open(file_, "r") as data:
        return data.read()


def content_as_json(content: str) -> dict:
    """
    Try to return the content passed as dictionary python object.

    :param content: data into file
    :return: dict
    """
    logging.info(f"Convert json string data into dictionary python object")
    return json.loads(content)


def validate_json(data: dict, keys_: list) -> None:
    """
    Validate if json contains expected keywords.

    :param data: data from request
    :param keys_: list of keywords in data content from post request
    :return: None
    """
    errors = []
    for key in keys_:
        if key not in data:
            errors.append(key)
    if errors:
        raise DataContentError(f"Your data content does not contain the required keywords: {' '.join(errors)}")


def fork_foreach_data(data: dict) -> None:
    """
    Fork a subprocess in your local machine for each element in the data list

    :param data: data received from post request
    :return: None
    """
    udid, coordinate_list = data["udid"], data["data"]
    for coordinate in coordinate_list:
        subprocess.Popen(args=[
            BASE_COMMAND_LINE, " ", "idevicesetlocation", "--udid", udid, "--", coordinate["lat"], coordinate["lon"]
        ])


def print_json(content: dict) -> None:
    """
    Pretty print json.

    :param content:
    :return: None
    """
    print(json.dumps(content, indent=2))


class DataContentError(KeyError):
    """
    DataContent exception raised in case of invalid JSON data.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


####################################
# FLASK BUSINESS LOGIC #############
####################################
app = Flask(__name__)


@app.route("/coordinates", methods=["GET", "POST"])
def coordinates():
    if request.method == "GET":
        return jsonify(CONTENT_DATA)

    if request.method == "POST":
        data = request.json
        print_json(data)

        try:
            validate_json(data=data, keys_=KEYS_)
        except DataContentError as dce:
            logging.exception(dce)
            return abort(406)

        logging.info("Processing data received from request")
        fork_foreach_data(data=data)

        return jsonify({"status": "ok", "message": "Process completed successfully!"})


if __name__ == '__main__':
    ####################################
    # ARGUMENTs PARSER CLI #############
    ####################################
    parser = argparse.ArgumentParser(description="Coordinates helper")
    parser.add_argument("--data", help="Path to data file", required=True)
    arguments = parser.parse_args()

    ####################################
    # LOADING DATA #####################
    ####################################
    CONTENT_FILENAME = arguments.data
    CONTENT_DATA = load_content_from_file(file_=CONTENT_FILENAME)
    CONTENT_DATA = content_as_json(content=CONTENT_DATA)

    app.run(debug=True)

    # DEBUG CONSOLE OUTPUT
    # print_json(CONTENT_DATA)
