import json
import re

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ValidationError

def load_yaml_config(
    config_path: str,
    config_type: BaseModel,
) -> BaseModel:
    """Loads configuration from a YAML file."""
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data = yaml.safe_load(config_file)
    try:
        return config_type(**config_data)
    except ValidationError as e:
        raise ValueError(f"Error parsing configuration: {e}") from e


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


def clean_and_parse_llm_json_output(llm_output: str) -> dict:
    """
    Cleans up the output of an LLM and returns a JSON object.

    Args:
        llm_output: The raw output of an LLM.

    Returns:
        dict: A dictionary representing the cleaned and parsed JSON object.
    """
    start_index = llm_output.find("{")
    end_index = llm_output.rfind("}") + 1
    cleaned_output = llm_output[start_index:end_index].strip()
    cleaned_output = re.sub(r"\n|\r", "", cleaned_output)

    cleaned_output = re.sub(r"\s+", " ", cleaned_output)

    try:
        json_data = json.loads(cleaned_output)
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON output from LLM. Instead got {llm_output}"}

    return json_data
