import base64
import collections
import hashlib
import hmac
import json
import math
import os
import random
import string
import time
import urllib

import pandas as pd
import requests


class Gallery:
    def __init__(self, api_location: str, api_key: str, api_secret: str):
        """Initiate a new `Gallery` instance

        Args:
            api_location (str):
                API base URL in the form of https://alteryx.example.com/webapi (OAuth 2.0)
                or https://alteryx.example.com/gallery/api (OAuth 1.0)
            api_key (str): API key
            api_secret (str): API secret
        """
        self.api_location = api_location
        self.api_key = api_key
        self.api_secret = api_secret

    @property
    def api_location(self):
        return self._api_location

    @api_location.setter
    def api_location(self, loc):
        if not loc:
            raise Exception("'api_location' cannot be empty")
        if not isinstance(loc, str):
            raise TypeError(f"Invalid type {type(loc)} for variable 'api_location'")
        self._api_location = loc

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, key):
        if not key:
            raise Exception("'api_key' cannot be empty")
        if not isinstance(key, str):
            raise TypeError(f"Invalid type: {type(key)} for variable 'api_key'")
        self._api_key = key

    @property
    def api_secret(self):
        return self._api_secret

    @api_secret.setter
    def api_secret(self, secret_key):
        if not secret_key:
            raise Exception("'api_secret' cannot be empty")
        if not isinstance(secret_key, str):
            raise TypeError(
                f"Invalid type {type(secret_key)} for variable 'api_secret'"
            )
        self._api_secret = secret_key

    def build_oauth_params(self):
        """
        :return:  A dictionary consisting of params for third-party
        signature generation code based upon the OAuth 1.0a standard.
        """
        return {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": self.generate_nonce(5),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(math.floor(time.time()))),
            "oauth_version": "1.0",
        }

    @staticmethod
    def generate_nonce(length=5):
        """
        :return: Generate pseudorandom number
        """
        tmp_string = string.ascii_uppercase + string.digits + string.ascii_lowercase
        return "".join([str(random.choice(tmp_string)) for i in range(length)])

    def generate_signature(self, http_method, url, params):
        """
        :return: returns HMAC-SHA1 signature
        """
        quote = lambda x: requests.utils.quote(x, safe="~")
        sorted_params = collections.OrderedDict(sorted(params.items()))

        normalized_params = urllib.parse.urlencode(sorted_params)
        base_string = "&".join(
            (http_method.upper(), quote(url), quote(normalized_params))
        )

        secret_bytes = bytes("&".join([self.api_secret, ""]), "ascii")
        base_bytes = bytes(base_string, "ascii")
        sig = hmac.new(secret_bytes, base_bytes, hashlib.sha1)
        return base64.b64encode(sig.digest())

    def subscription(self):
        """
        :return: workflows in a subscription
        """
        method = "GET"
        url = self.api_location + "/v1/workflows/subscription/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def questions(self, app_id):
        """
        :return: Returns the questions for the given Alteryx Analytics App
        """
        method = "GET"
        url = self.api_location + "/v1/workflows/" + app_id + "/questions/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def execute_workflow(self, app_id, **kwargs):
        """
        Queue an app execution job.
        :return:  Returns ID of the job
        """
        method = "POST"
        url = self.api_location + "/v1/workflows/" + app_id + "/jobs/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})

        if "payload" in kwargs:
            output = requests.post(
                url,
                json=kwargs["payload"],
                headers={"Content-Type": "application/json"},
                params=params,
            )
        else:
            output = requests.post(url, params=params)

        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def get_jobs(self, app_id):
        """
        :return: Returns the jobs for the given Alteryx Analytics App
        """
        method = "GET"
        url = self.api_location + "/v1/workflows/" + app_id + "/jobs/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def get_job_status(self, job_id):
        """
        :return: Retrieves the job and its current state
        """
        method = "GET"
        url = self.api_location + "/v1/jobs/" + job_id + "/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def get_job_output(self, job_id, output_id):
        """
        :return: Returns the output for a given job (FileURL)
        """
        method = "GET"
        url = self.api_location + "/v1/jobs/" + job_id + "/output/" + output_id + "/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, output.content.decode("utf8")
        return output, output_content

    def get_workflows(self):
        """
        :return: Returns Workflows
        """
        method = "GET"
        url = self.api_location + "/admin/v1/workflows/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content

    def get_app(self, app_id):
        """
        :return: Returns the App that was requested
        """
        method = "GET"
        url = self.api_location + "/v1/workflows/" + app_id + "/package/"
        params = self.build_oauth_params()
        signature = self.generate_signature(method, url, params)
        params.update({"oauth_signature": signature})
        output = requests.get(url, params=params)
        output, output_content = output, json.loads(output.content.decode("utf8"))
        return output, output_content
