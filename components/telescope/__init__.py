import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
telescope_component = components.declare_component("prism_telescope", path=_COMPONENT_DIR)


def telescope(angle=180, width=None, key=None, theme="dark"):
    return telescope_component(angle=angle, theme=theme, key=key, default=angle)
