import requests
import logging


class GQLError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)

        self.errors = errors


class GQLClient:
    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        self._logger = logging.getLogger(__name__)

    def query(self, query: str, variables: dict):
        try:
            logging.info(f"Making graphql request to {self._endpoint}")
            data = {
                "query": query,
                "variables": variables
            }
            self._logger.debug(f"GraphQL request to {self._endpoint}: {data!r}")
            resp = requests.post(self._endpoint, json=data, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects,
                requests.exceptions.ChunkedEncodingError, requests.exceptions.ContentDecodingError,
                requests.exceptions.StreamConsumedError, requests.exceptions.RetryError,
                requests.exceptions.UnrewindableBodyError) as e:
            self._logger.error(f"GraphQL request error: {e}")
            raise GQLError(e.message, [])
        if resp.status_code != requests.codes.ok:
            self._logger.error(f"GraphQL request returned status code {resp.status_code}")
            raise GQLError(f"{resp.status_code} error", [])
        self._logger.debug(f"GraphQL request returned {resp.content!r}")
        try:
            data = resp.json()
        except ValueError:
            self._logger.error(f"GraphQL request returned invalid JSON")
            raise GQLError("Error in decoding JSON", [])
        data = data.get("data")
        errors = data.get("errors")
        if data is None:
            self._logger.error("GraphQL request didn't return data")
            raise GQLError("Invalid data in response", [])
        if errors is not None and len(errors) > 0:
            self._logger.error(f"GraphQL request returned GraphQL errors: {errors!r}")
            raise GQLError("Error encountered from server", errors)
        return data