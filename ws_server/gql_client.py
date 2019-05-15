import requests
import logging


class GQLError(Exception):
    def __init__(self, message):
        super().__init__(message)


class GQLClient:
    def __init__(self, endpoint: str):
        self._endpoint = endpoint

    def query(self, query: str, variables: dict):
        try:
            logging.info(f"Making graphql request to {self._endpoint}")
            data = {
                "query": query,
                "variables": variables
            }
            logging.debug(f"GraphQL request to {self._endpoint}: {data!r}")
            resp = requests.post(self._endpoint, json=data, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects,
                requests.exceptions.ChunkedEncodingError, requests.exceptions.ContentDecodingError,
                requests.exceptions.StreamConsumedError, requests.exceptions.RetryError,
                requests.exceptions.UnrewindableBodyError) as e:
            logging.warning(f"GraphQL request error: {e}")
            raise GQLError(e.message)
        if resp.status_code != requests.codes.ok:
            logging.warning(f"GraphQL request returned status code {resp.status_code}")
            raise GQLError(f"{resp.status_code} error")
        logging.debug(f"GraphQL request returned {resp.content!r}")
        try:
            data = resp.json()
        except ValueError:
            logging.warning(f"GraphQL request returned invalid JSON")
            raise GQLError("Error in decoding JSON")
        logging.debug(f"GraphQL request returned {data!r} decoded as JSON")
        errors = data.get("errors")
        resp_data = data.get("data")
        if resp_data is None:
            logging.warning("GraphQL request didn't return data")
            raise GQLError("Invalid data in response")
        if errors is not None and len(errors) > 0:
            logging.warning(f"GraphQL request returned GraphQL errors: {errors!r}")
        return data
