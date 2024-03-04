# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
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

from __future__ import annotations

import inspect
import os
from types import FrameType

from streamlit.components.types.base_component_registry import BaseComponentRegistry
from streamlit.components.v1.custom_component import CustomComponent
from streamlit.runtime import get_instance


def _get_module_name(caller_frame: FrameType) -> str:
    # Get the caller's module name. `__name__` gives us the module's
    # fully-qualified name, which includes its package.
    module = inspect.getmodule(caller_frame)
    assert module is not None
    module_name = module.__name__

    # If the caller was the main module that was executed (that is, if the
    # user executed `python my_component.py`), then this name will be
    # "__main__" instead of the actual package name. In this case, we use
    # the main module's filename, sans `.py` extension, as the component name.
    if module_name == "__main__":
        file_path = inspect.getfile(caller_frame)
        filename = os.path.basename(file_path)
        module_name, _ = os.path.splitext(filename)

    return module_name


def declare_component(
    name: str,
    path: str | None = None,
    url: str | None = None,
) -> CustomComponent:
    """Create and register a custom component.

    Parameters
    ----------
    name: str
        A short, descriptive name for the component. Like, "slider".
    path: str or None
        The path to serve the component's frontend files from. Either
        `path` or `url` must be specified, but not both.
    url: str or None
        The URL that the component is served from. Either `path` or `url`
        must be specified, but not both.

    Returns
    -------
    CustomComponent
        A CustomComponent that can be called like a function.
        Calling the component will create a new instance of the component
        in the Streamlit app.

    """

    # Get our stack frame.
    current_frame: FrameType | None = inspect.currentframe()
    assert current_frame is not None
    # Get the stack frame of our calling function.
    caller_frame = current_frame.f_back
    assert caller_frame is not None
    module_name = _get_module_name(caller_frame)

    # Build the component name.
    component_name = f"{module_name}.{name}"

    # Create our component object, and register it.
    component = CustomComponent(
        name=component_name, path=path, url=url, module_name=module_name
    )
    get_instance().component_registry.register_component(component)

    return component


# keep for backwards-compatibility
class ComponentRegistry:
    @classmethod
    def instance(cls) -> BaseComponentRegistry:
        """Returns the ComponentRegistry of the runtime instance."""

        return get_instance().component_registry
