# scripts/migrate_config_to_db.py

import json
import logging
import os
import sys

import yaml  # Using PyYAML

# --- Add project root to path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ----------------------------------

try:
    from sqlalchemy.exc import IntegrityError
    from src.opmas.config import get_config, load_config  # Load bootstrap config
    from src.opmas.db_models import Agent, AgentRule, OpmasConfig, Playbook, PlaybookStep
    from src.opmas.db_utils import get_db_session, init_db
except ImportError as e:
    print(f"Error: Failed to import OPMAS modules: {e}", file=sys.stderr)
    print("Ensure script is run from project root and dependencies are installed.", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrate_config")

# --- Configuration File Paths (Relative to project root) ---
CORE_CONFIG_YAML = "config/opmas_config.yaml"
AGENT_RULES_YAML = "config/agent_rules.yaml"
# Assuming playbooks are still in knowledge_base.yaml for migration
PLAYBOOKS_YAML = "config/knowledge_base.yaml"
# ---------------------------------------------------------


def load_yaml_file_safe(filepath):
    """Safely loads a YAML file."""
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
            logger.info(f"Successfully loaded YAML data from: {filepath}")
            return data
    except FileNotFoundError:
        logger.warning(f"YAML file not found: {filepath}. Skipping migration for this file.")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None


def migrate_core_config(session, yaml_data):
    """Migrates core config settings from YAML to opmas_config table."""
    if not yaml_data or "logging" not in yaml_data:
        logger.warning(
            "Core config YAML missing or lacks 'logging' section. Cannot migrate settings."
        )
        return

    config_settings = {
        "logging.level": yaml_data.get("logging", {}).get("level", "INFO"),
        "logging.format_type": yaml_data.get("logging", {}).get("format_type", "standard")
        # Add other core settings here if needed
    }

    logger.info("Migrating core config settings...")
    for key, value in config_settings.items():
        try:
            existing = session.query(OpmasConfig).filter_by(key=key).first()
            if existing:
                if json.dumps(existing.value) != json.dumps(value):  # Compare JSON representations
                    logger.info(f"Updating core config: {key}")
                    existing.value = value
                else:
                    logger.info(f"Core config '{key}' already exists and matches. Skipping.")
            else:
                logger.info(f"Adding core config: {key}")
                new_config = OpmasConfig(key=key, value=value)
                session.add(new_config)
        except Exception as e:
            logger.error(f"Error migrating core config key '{key}': {e}", exc_info=True)
            session.rollback()  # Rollback this specific failure if desired, or let the main loop handle it
            raise  # Re-raise to stop the whole migration on error


def migrate_agents_and_rules(session, yaml_data):
    """Migrates agents and their rules from YAML to DB."""
    if not yaml_data or "agent_rules" not in yaml_data:
        logger.warning(
            "Agent rules YAML missing or lacks 'agent_rules' section. Skipping rule migration FROM YAML."
        )
        return

    rules_by_agent = yaml_data.get("agent_rules", {})  # Use .get for safety

    logger.info("Migrating rules from YAML...")
    for agent_name, rules in rules_by_agent.items():
        # --- Find Agent (MUST exist from ensure_core_agents_exist or previously) ---
        agent = session.query(Agent).filter_by(name=agent_name).first()
        if not agent:
            logger.warning(
                f"Agent '{agent_name}' found in YAML but not in DB. Skipping rule migration for this agent. Ensure agents are created first."
            )
            continue

        # --- Migrate Rules for this Agent (Existing logic) ---
        if not isinstance(rules, list):
            logger.warning(f"Rules for agent '{agent_name}' are not a list. Skipping rules.")
            continue

        for rule_dict in rules:
            if not isinstance(rule_dict, dict):
                logger.warning(
                    f"Invalid rule format for agent '{agent_name}' (not a dict): {rule_dict}. Skipping."
                )
                continue

            rule_name = rule_dict.get("name")
            if not rule_name:
                logger.warning(
                    f"Rule for agent '{agent_name}' missing 'name': {rule_dict}. Skipping."
                )
                continue

            # Rule config is the entire dictionary for that rule
            rule_config_json = rule_dict

            existing_rule = (
                session.query(AgentRule)
                .filter_by(agent_id=agent.agent_id, rule_name=rule_name)
                .first()
            )
            if existing_rule:
                if json.dumps(existing_rule.rule_config, sort_keys=True) != json.dumps(
                    rule_config_json, sort_keys=True
                ):
                    logger.info(f"Updating rule '{rule_name}' for agent '{agent_name}'")
                    existing_rule.rule_config = rule_config_json
                else:
                    logger.info(
                        f"Rule '{rule_name}' for agent '{agent_name}' already exists and matches. Skipping."
                    )
            else:
                logger.info(f"Adding rule '{rule_name}' for agent '{agent_name}'")
                new_rule = AgentRule(
                    agent_id=agent.agent_id,
                    rule_name=rule_name,
                    rule_config=rule_config_json,
                    is_enabled=rule_config_json.get("enabled", True),  # Sync enabled status
                )
                session.add(new_rule)


def migrate_playbooks(session, yaml_data):
    """Migrates playbooks and steps from YAML to DB."""
    if not yaml_data or "action_playbooks" not in yaml_data:
        logger.warning(
            "Playbook YAML missing or lacks 'action_playbooks' section. Skipping playbook migration."
        )
        return

    playbooks_dict = yaml_data["action_playbooks"]

    logger.info("Migrating playbooks and steps...")
    for finding_type, steps in playbooks_dict.items():
        try:
            # Assume playbook name is derived from finding type for now
            playbook_name = finding_type.replace("Rate", " Rate Playbook")  # Basic naming
            playbook_description = f"Playbook for handling {finding_type} findings."

            # --- Ensure Playbook Exists ---
            playbook = session.query(Playbook).filter_by(finding_type=finding_type).first()
            if not playbook:
                logger.info(f"Creating playbook for finding type: {finding_type}")
                playbook = Playbook(
                    finding_type=finding_type, name=playbook_name, description=playbook_description
                )
                session.add(playbook)
                session.flush()  # Get playbook_id
            else:
                logger.info(
                    f"Playbook for '{finding_type}' already exists (ID: {playbook.playbook_id}). Updating steps."
                )
                # Delete existing steps for simplicity, then re-add. More robust merge is complex.
                logger.warning(
                    f"Deleting existing steps for playbook '{finding_type}' before re-adding."
                )
                session.query(PlaybookStep).filter_by(playbook_id=playbook.playbook_id).delete()
                session.flush()

            # --- Migrate Steps ---
            if not isinstance(steps, list):
                logger.warning(
                    f"Steps for playbook '{finding_type}' are not a list. Skipping steps."
                )
                continue

            for i, step_dict in enumerate(steps):
                if not isinstance(step_dict, dict):
                    logger.warning(
                        f"Invalid step format for playbook '{finding_type}' (not a dict): {step_dict}. Skipping."
                    )
                    continue

                action_type = step_dict.get("action_type")
                if not action_type:
                    logger.warning(
                        f"Step {i} for playbook '{finding_type}' missing 'action_type'. Skipping."
                    )
                    continue

                logger.info(f"Adding step {i+1} ('{action_type}') to playbook '{finding_type}'")
                new_step = PlaybookStep(
                    playbook_id=playbook.playbook_id,
                    step_order=i + 1,  # Use 1-based index for order
                    action_type=action_type,
                    command_template=step_dict.get("command"),  # Optional
                    description=step_dict.get("description"),  # Optional
                    timeout_seconds=step_dict.get("timeout_seconds"),  # Optional
                    step_config=step_dict.get("step_config"),  # Optional, store as JSON
                )
                session.add(new_step)

        except Exception as e:
            logger.error(f"Error migrating playbook/steps for '{finding_type}': {e}", exc_info=True)
            session.rollback()
            raise


def ensure_core_agents_exist(session):
    """Checks for core agents and creates them if they don't exist."""
    logger.info("Ensuring core agents exist in the database...")
    core_agents = [
        {
            "name": "WiFiAgent",
            "module_path": "src.opmas.agents.wifi_agent",
            "description": "Agent specializing in Wi-Fi related log analysis.",
            "is_enabled": True,
        },
        # Add other essential agents here if needed (e.g., OrchestratorAgent if it needs DB config)
        # {
        #     "name": "OrchestratorAgent",
        #     "module_path": "src.opmas.orchestrator",
        #     "description": "Orchestrates responses based on findings.",
        #     "is_enabled": True
        # },
    ]

    for agent_data in core_agents:
        try:
            agent_name = agent_data["name"]
            agent = session.query(Agent).filter_by(name=agent_name).first()
            if not agent:
                logger.info(f"Core agent '{agent_name}' not found. Creating...")
                new_agent = Agent(**agent_data)
                session.add(new_agent)
                logger.info(f"Core agent '{agent_name}' created.")
            else:
                logger.info(f"Core agent '{agent_name}' already exists.")
                # Optional: Update existing agent's fields if needed
                # agent.is_enabled = agent_data.get('is_enabled', agent.is_enabled)
                # agent.description = agent_data.get('description', agent.description)
        except Exception as e:
            logger.error(
                f"Error ensuring core agent '{agent_data.get('name', 'UNKNOWN')}': {e}",
                exc_info=True,
            )
            session.rollback()
            raise  # Stop migration on error


def main():
    logger.info("--- OPMAS Configuration Migrator --- ")

    # 1. Load bootstrap config (for DB connection)
    try:
        logger.info("Loading bootstrap configuration...")
        load_config()
        logger.info("Bootstrap configuration loaded.")
    except Exception as e:
        logger.critical(f"Failed to load bootstrap configuration: {e}", exc_info=True)
        sys.exit(1)

    # 2. Ensure DB is initialized (optional, but good practice)
    try:
        logger.info("Ensuring database schema exists...")
        init_db()  # Create tables if they don't exist
    except Exception as e:
        logger.critical(f"Failed during pre-migration DB initialization: {e}", exc_info=True)
        sys.exit(1)

    # 3. Load YAML data (will be None if files are missing, handled by functions)
    logger.info("Loading YAML configuration files (if they exist)...")
    core_config_data = load_yaml_file_safe(CORE_CONFIG_YAML)
    agent_rules_data = load_yaml_file_safe(AGENT_RULES_YAML)  # May be None now
    playbooks_data = load_yaml_file_safe(PLAYBOOKS_YAML)  # May be None now

    # 4. Perform migration within a single transaction
    logger.info("Starting migration process...")
    try:
        with get_db_session() as session:
            # --- MODIFIED ORDER ---
            # Ensure core agents exist first
            ensure_core_agents_exist(session)

            # Then migrate core config, rules (from YAML if present), and playbooks (from YAML if present)
            migrate_core_config(session, core_config_data)
            migrate_agents_and_rules(
                session, agent_rules_data
            )  # Now only adds/updates rules if agent exists
            migrate_playbooks(session, playbooks_data)  # Assumes playbook source YAML exists

            session.commit()  # Commit the transaction
            logger.info("Migration process completed successfully.")
    except Exception as e:
        logger.critical(f"Migration failed: {e}", exc_info=True)
        logger.info("Transaction rolled back.")
        sys.exit(1)


if __name__ == "__main__":
    main()
