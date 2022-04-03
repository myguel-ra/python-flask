import json
from . import config
from dataclasses import dataclass
import flask
import requests
from flask.json import jsonify
from flask import Flask, Response, g, request
from http import HTTPStatus
import random
import logging

app = Flask(__name__)
url = config.RATELIMIT_URL
data = config.RATELIMIT_REQUEST


if __name__ != "__main__":
    # Assume we're running under gunicorn, and set up logging.
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.logger.info('RATELIMIT_URL ' + url)


def is_limited(user, route):
    data['descriptors'][0]['entries'][0]['value'] = route
    data['descriptors'][1]['entries'][0]['value'] = route
    data['descriptors'][1]['entries'][1]['value'] = user

    response = requests.post(url, data=json.dumps(data))

    return json.loads(response.text)['overallCode'] == 'OVER_LIMIT'


@app.before_request
def add_user_to_context():
    """Store current user as g.user for use in route handlers."""
    # Read from Wave-Logged-In-User header.
    user = request.headers.get("Wave-Logged-In-User")

    if user is None:
        # Pick a random fake user so we always have a user.
        user = random.choice(
            [
                "edouard.mendy@wave.com",
                "meta.camara@wave.com",
                "fatimata.tamboura@wave.com",
            ]
        )

    g.user = user

    if str(request.url_rule) != '/health' and is_limited(user, str(request.url_rule)):
        return flask.make_response(jsonify(errors='request limit exceeded'), HTTPStatus.TOO_MANY_REQUESTS)


@app.route("/health", methods=["GET"])
def health() -> Response:
    return flask.make_response("ok")


@app.route("/customers/search", methods=["GET"])
def search_customers() -> Response:
    prefix = request.args.get("nameprefix", None)

    if prefix is None:
        error = {
            "message": "nameprefix query parameter is required",
            "code": "missing-prefix",
        }
        return flask.make_response(jsonify(errors=[error]), HTTPStatus.BAD_REQUEST)

    customers = find_customer_by_name_prefix(prefix)
    return jsonify(data={"customers": customers})


@app.route("/transactions/search", methods=["GET"])
def search_transactions() -> Response:
    customer_id = request.args.get("customer_id", None)

    if customer_id is None:
        error = {
            "message": "customer_id query parameter is required",
            "code": "missing-customer-id",
        }
        return flask.make_response(jsonify(errors=[error]), HTTPStatus.BAD_REQUEST)

    transactions = find_transactions_by_customer(customer_id)

    return jsonify(data={"transactions": transactions})


@dataclass
class Customer:
    id: int
    name: str


def find_customer_by_name_prefix(prefix: str) -> [Customer]:
    import time

    time.sleep(0.2)  # Fake work :-)
    return [Customer(id=7, name="Fatou Sene")]


@dataclass
class Transaction:
    id: int
    customer: Customer
    amount: int


def find_transactions_by_customer(customer_id: int) -> [Customer]:
    import time

    time.sleep(0.2)  # Fake work :-)
    return [Transaction(id=9, amount=1500, customer=Customer(id=7, name="Fatou Sene"))]
