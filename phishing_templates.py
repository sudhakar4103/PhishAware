import json
import logging
import os


logger = logging.getLogger(__name__)

_TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), 'data', 'phishing_templates.json')


def get_phishing_templates():
    """Load phishing templates from the static JSON file."""
    try:
        with open(_TEMPLATES_PATH, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        logger.error('Phishing templates file not found: %s', _TEMPLATES_PATH)
        return []
    except json.JSONDecodeError as exc:
        logger.error('Invalid phishing templates JSON: %s', exc)
        return []


def get_phishing_template_by_id(template_id):
    """Return a single template dict by id, or None if not found."""
    if not template_id:
        return None

    templates = get_phishing_templates()
    for template in templates:
        if template.get('id') == template_id:
            return template
    return None
