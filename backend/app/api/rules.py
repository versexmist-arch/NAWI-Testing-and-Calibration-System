from fastapi import APIRouter
from rules import load_rules_config

router = APIRouter(prefix="/rules", tags=["OIML Rules Configuration"])


@router.get("")
def get_configured_rules():
    config = load_rules_config()
    return {
        "rule_configuration_version": config.get("version"),
        "name": config.get("name"),
        "description": config.get("description"),
        "rules_count": len(config.get("rules", [])),
        "rules": config.get("rules", []),
    }

