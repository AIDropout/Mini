import json
import re
from datetime import datetime
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ValidationError


def render_jinja_template(template_name: str, template_dir: str, **kwargs) -> str:
    """
    Load a Jinja2 template from a specified directory.

    Args:
        template_name: The name of the template file (e.g., "template.j2").
        template_dir: The directory path where the template file is located.

    Returns:
        rendered_text: The Jinja2 template render.
    """
    env = Environment(
        loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
    )

    template = env.get_template(template_name)
    rendered_text = template.render(**kwargs)
    return rendered_text


def get_current_time_readable() -> str:
    current_time = datetime.now()
    return current_time.strftime("%-I:%M%p %A, %b %-d, %Y")
