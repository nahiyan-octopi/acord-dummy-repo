"""
Rules Routes

API endpoints for validation rules.
"""
from pydantic import BaseModel, Field
from fastapi import APIRouter
from typing import Union

from app.modules.rules.rules_controller import RulesController


class CreateRuleRequest(BaseModel):
    certificate_type: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class UpdateRuleRequest(BaseModel):
    certificate_type: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool


class UpdateRuleBulkRequest(BaseModel):
    id: int = Field(..., gt=0)
    certificate_type: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool


class DeleteRulesRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)


router = APIRouter(prefix="/api/rules", tags=["rules"])
controller = RulesController()


@router.post("/")
async def create_rule(payload: Union[CreateRuleRequest, list[CreateRuleRequest]]):
    """Create one or many validation rules."""
    if isinstance(payload, list):
        return await controller.create_rules_bulk(
            [
                {
                    "certificate_type": item.certificate_type,
                    "product_name": item.product_name,
                    "is_active": item.is_active,
                }
                for item in payload
            ]
        )

    return await controller.create_rule(
        certificate_type=payload.certificate_type,
        product_name=payload.product_name,
        is_active=payload.is_active
    )


@router.get("/")
async def list_rules():
    """Fetch all validation rules."""
    return await controller.list_rules()


@router.get("/{rule_id}")
async def get_rule(rule_id: int):
    """Fetch a single validation rule by id."""
    return await controller.get_rule(rule_id)


@router.put("/{rule_id}")
async def update_rule(rule_id: int, payload: UpdateRuleRequest):
    """Update an existing validation rule by id."""
    return await controller.update_rule(
        rule_id=rule_id,
        certificate_type=payload.certificate_type,
        product_name=payload.product_name,
        is_active=payload.is_active
    )


@router.put("/")
async def update_rules(payload: list[UpdateRuleBulkRequest]):
    """Update multiple validation rules."""
    return await controller.update_rules_bulk(
        [
            {
                "id": item.id,
                "certificate_type": item.certificate_type,
                "product_name": item.product_name,
                "is_active": item.is_active,
            }
            for item in payload
        ]
    )


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete an existing validation rule by id."""
    return await controller.delete_rule(rule_id=rule_id)


@router.delete("/")
async def delete_rules(payload: DeleteRulesRequest):
    """Delete multiple validation rules by ids."""
    return await controller.delete_rules_bulk(rule_ids=payload.ids)
