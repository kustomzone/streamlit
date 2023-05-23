# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Callable, Dict, List

import tornado.httputil
import tornado.web

from streamlit import config
from streamlit.logger import get_logger
from streamlit.runtime.uploaded_file_manager import (
    NewUploadedFileRec,
    UploadedFileManager,
)
from streamlit.web.server import routes, server_util

LOGGER = get_logger(__name__)


class NewUploadFileRequestHandler(tornado.web.RequestHandler):
    """Implements the POST /upload_file endpoint."""

    def initialize(
        self,
        file_mgr: UploadedFileManager,
        is_active_session: Callable[[str], bool],
    ):
        """
        Parameters
        ----------
        file_mgr : UploadedFileManager
            The server's singleton UploadedFileManager. All file uploads
            go here.
        is_active_session:
            A function that returns true if a session_id belongs to an active
            session.
        """
        self._file_mgr = file_mgr
        self._is_active_session = is_active_session

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS, DELETE")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        if config.get_option("server.enableXsrfProtection"):
            self.set_header(
                "Access-Control-Allow-Origin",
                server_util.get_url(config.get_option("browser.serverAddress")),
            )
            self.set_header("Access-Control-Allow-Headers", "X-Xsrftoken, Content-Type")
            self.set_header("Vary", "Origin")
            self.set_header("Access-Control-Allow-Credentials", "true")
        elif routes.allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")

    def options(self, **kwargs):
        """/OPTIONS handler for preflight CORS checks.

        When a browser is making a CORS request, it may sometimes first
        send an OPTIONS request, to check whether the server understands the
        CORS protocol. This is optional, and doesn't happen for every request
        or in every browser. If an OPTIONS request does get sent, and is not
        then handled by the server, the browser will fail the underlying
        request.

        The proper way to handle this is to send a 204 response ("no content")
        with the CORS headers attached. (These headers are automatically added
        to every outgoing response, including OPTIONS responses,
        via set_default_headers().)

        See https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
        """
        self.set_status(204)
        self.finish()

    def post(self, **kwargs):
        """
        Receive an uploaded file and add it to our UploadedFileManager.
        Return the file's ID, so that the client can refer to it.
        """

        args: Dict[str, List[bytes]] = {}
        files: Dict[str, List[Any]] = {}

        session_id = self.path_kwargs["session_id"]
        file_url = self.request.full_url()

        tornado.httputil.parse_body_arguments(
            content_type=self.request.headers["Content-Type"],
            body=self.request.body,
            arguments=args,
            files=files,
        )

        # TODO[KAREN] MAYBE CHECK THAT SESSION IS ACTIVE SESSION

        # Create an UploadedFile object for each file.
        # We assign an initial, invalid file_id to each file in this loop.
        # The file_mgr will assign unique file IDs and return in `add_file`,
        # below.
        uploaded_files: List[NewUploadedFileRec] = []

        for _, flist in files.items():
            for file in flist:
                uploaded_files.append(
                    NewUploadedFileRec(
                        file_url=file_url,
                        name=file["filename"],
                        type=file["content_type"],
                        data=file["body"],
                    )
                )

        if len(uploaded_files) != 1:
            self.send_error(
                400, reason=f"Expected 1 file, but got {len(uploaded_files)}"
            )
            return

        self._file_mgr.add_file_modern(session_id=session_id, file=uploaded_files[0])
        self.set_status(204)

    def delete(self, **kwargs):
        """DELETE FILE"""
        session_id = self.path_kwargs["session_id"]
        file_url = self.request.full_url()

        self._file_mgr.remove_file_modern(session_id=session_id, file_url=file_url)
        self.set_status(204)
