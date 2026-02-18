"""
Rules Controller

Handles request validation and response formatting for rules APIs.
"""
from app.services.rules.rules_service import RulesService
from app.utils.response_utils import APIResponse, validation_error, server_error


class RulesController:
    """Controller for rules endpoints."""

    def __init__(self):
        self.service = RulesService()

    async def delete_rules_bulk(self, rule_ids: list[int]):
        """Delete multiple rules endpoint handler."""
        if not rule_ids:
            return validation_error("At least one rule id is required")

        try:
            deleted_rules = self.service.delete_rules_bulk(rule_ids=rule_ids)
            return APIResponse.success(
                data={"rules": deleted_rules, "count": len(deleted_rules)},
                message="Validation rules deleted successfully"
            )
        except LookupError as error:
            return APIResponse.error(
                message=str(error),
                status_code=404,
                error_code="NOT_FOUND"
            )
        except ValueError as error:
            return validation_error(str(error))
        except Exception as error:
            return server_error(f"Failed to delete validation rules: {str(error)}")

    async def create_rules_bulk(self, rules_payload: list[dict]):
        """Create multiple rules endpoint handler."""
        if not rules_payload:
            return validation_error("At least one rule is required")

        try:
            created_rules = self.service.create_rules_bulk(rules_payload)
            return APIResponse.success(
                data={"rules": created_rules, "count": len(created_rules)},
                message="Validation rules created successfully"
            )
        except ValueError as error:
            return validation_error(str(error))
        except Exception as error:
            return server_error(f"Failed to create validation rules: {str(error)}")

    async def update_rules_bulk(self, rules_payload: list[dict]):
        """Update multiple rules endpoint handler."""
        if not rules_payload:
            return validation_error("At least one rule is required")

        try:
            updated_rules = self.service.update_rules_bulk(rules_payload)
            return APIResponse.success(
                data={"rules": updated_rules, "count": len(updated_rules)},
                message="Validation rules updated successfully"
            )
        except LookupError as error:
            return APIResponse.error(
                message=str(error),
                status_code=404,
                error_code="NOT_FOUND"
            )
        except ValueError as error:
            return validation_error(str(error))
        except Exception as error:
            return server_error(f"Failed to update validation rules: {str(error)}")

    async def get_rule(self, rule_id: int):
        """Get rule by id endpoint handler."""
        if rule_id <= 0:
            return validation_error("rule_id must be a positive integer")

        try:
            rule = self.service.get_rule(rule_id)
            return APIResponse.success(
                data={"rule": rule},
                message="Validation rule fetched successfully"
            )
        except LookupError as error:
            return APIResponse.error(
                message=str(error),
                status_code=404,
                error_code="NOT_FOUND"
            )
        except Exception as error:
            return server_error(f"Failed to fetch validation rule: {str(error)}")

    async def list_rules(self):
        """List rules endpoint handler."""
        try:
            rules = self.service.list_rules()
            return APIResponse.success(
                data={"rules": rules, "count": len(rules)},
                message="Validation rules fetched successfully"
            )
        except Exception as error:
            return server_error(f"Failed to fetch validation rules: {str(error)}")

    async def create_rule(self, certificate_type: str, product_name: str, is_active: bool = True):
        """Create rule endpoint handler."""
        if certificate_type is None or not certificate_type.strip():
            return validation_error("certificate_type is required")

        if product_name is None or not product_name.strip():
            return validation_error("product_name is required")

        try:
            created_rule = self.service.create_rule(
                certificate_type=certificate_type,
                product_name=product_name,
                is_active=is_active
            )
            return APIResponse.success(
                data={"rule": created_rule},
                message="Validation rule created successfully"
            )
        except ValueError as error:
            return validation_error(str(error))
        except Exception as error:
            return server_error(f"Failed to create validation rule: {str(error)}")

    async def update_rule(self, rule_id: int, certificate_type: str, product_name: str, is_active: bool):
        """Update rule endpoint handler."""
        if rule_id <= 0:
            return validation_error("rule_id must be a positive integer")

        if certificate_type is None or not certificate_type.strip():
            return validation_error("certificate_type is required")

        if product_name is None or not product_name.strip():
            return validation_error("product_name is required")

        try:
            updated_rule = self.service.update_rule(
                rule_id=rule_id,
                certificate_type=certificate_type,
                product_name=product_name,
                is_active=is_active
            )
            return APIResponse.success(
                data={"rule": updated_rule},
                message="Validation rule updated successfully"
            )
        except LookupError as error:
            return APIResponse.error(
                message=str(error),
                status_code=404,
                error_code="NOT_FOUND"
            )
        except ValueError as error:
            return validation_error(str(error))
        except Exception as error:
            return server_error(f"Failed to update validation rule: {str(error)}")

    async def delete_rule(self, rule_id: int):
        """Delete rule endpoint handler."""
        if rule_id <= 0:
            return validation_error("rule_id must be a positive integer")

        try:
            deleted_rule = self.service.delete_rule(rule_id=rule_id)
            return APIResponse.success(
                data={"rule": deleted_rule},
                message="Validation rule deleted successfully"
            )
        except LookupError as error:
            return APIResponse.error(
                message=str(error),
                status_code=404,
                error_code="NOT_FOUND"
            )
        except Exception as error:
            return server_error(f"Failed to delete validation rule: {str(error)}")
