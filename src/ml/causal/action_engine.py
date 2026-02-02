"""
Causal Action Engine
Connects causal findings to automated business actions

Answers: "Causal model says X caused Y... now what?"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of automated actions"""
    AUTO_REORDER = "auto_reorder"
    PRICE_ADJUSTMENT = "price_adjustment"
    PROMOTION_TRIGGER = "promotion_trigger"
    ALERT_MANAGER = "alert_manager"
    FORECAST_UPDATE = "forecast_update"
    INVENTORY_TRANSFER = "inventory_transfer"


class ActionPriority(Enum):
    """Action priority levels"""
    CRITICAL = "critical"      # Execute immediately
    HIGH = "high"             # Execute within 1 hour
    MEDIUM = "medium"         # Execute within 24 hours
    LOW = "low"              # Queue for batch processing


@dataclass
class CausalFinding:
    """A causal inference finding"""
    finding_type: str  # 'price_elasticity', 'weather_impact', 'holiday_effect', etc.
    cause: str
    effect: str
    magnitude: float
    confidence: float
    p_value: float
    timestamp: str
    context: Dict[str, Any]


@dataclass
class BusinessAction:
    """An automated business action"""
    action_id: str
    action_type: ActionType
    priority: ActionPriority
    description: str
    triggered_by: CausalFinding
    parameters: Dict[str, Any]
    expected_impact: str
    status: str  # 'pending', 'approved', 'executed', 'rejected'
    created_at: str
    executed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['action_type'] = self.action_type.value
        result['priority'] = self.priority.value
        return result


class CausalActionEngine:
    """
    Converts causal findings into actionable business decisions
    
    Example Flow:
    1. Causal model finds: "10% price increase → 15% sales drop"
    2. Action engine decides: "Revert price to optimal level"
    3. Auto-execute (if approved) or alert manager
    """
    
    def __init__(self, auto_execute_threshold: float = 0.95):
        """
        Args:
            auto_execute_threshold: Confidence threshold for auto-execution (0-1)
        """
        self.auto_execute_threshold = auto_execute_threshold
        self.action_queue: List[BusinessAction] = []
        self.executed_actions: List[BusinessAction] = []
        
    def process_causal_finding(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Main entry point: Process a causal finding and generate actions
        
        Args:
            finding: Causal inference result
            
        Returns:
            List of business actions to take
        """
        actions = []
        
        # Route to specific handler based on finding type
        if finding.finding_type == 'price_elasticity':
            actions.extend(self._handle_price_elasticity(finding))
        
        elif finding.finding_type == 'weather_impact':
            actions.extend(self._handle_weather_impact(finding))
        
        elif finding.finding_type == 'holiday_effect':
            actions.extend(self._handle_holiday_effect(finding))
        
        elif finding.finding_type == 'stockout_risk':
            actions.extend(self._handle_stockout_risk(finding))
        
        elif finding.finding_type == 'demand_surge':
            actions.extend(self._handle_demand_surge(finding))
        
        # Add to queue
        for action in actions:
            if finding.confidence >= self.auto_execute_threshold:
                action.status = 'approved'
                action.priority = ActionPriority.CRITICAL
            
            self.action_queue.append(action)
        
        logger.info(f"Generated {len(actions)} actions from finding: {finding.finding_type}")
        
        return actions
    
    def _handle_price_elasticity(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Handle: "Price change caused sales change"
        Action: Adjust price to optimal level
        """
        actions = []
        
        # Parse finding
        price_change_pct = finding.context.get('price_change_percent', 0)
        sales_change_pct = finding.magnitude
        elasticity = sales_change_pct / price_change_pct if price_change_pct != 0 else 0
        
        # If sales dropped significantly due to price increase
        if sales_change_pct < -10 and price_change_pct > 0:
            
            # Calculate optimal price rollback
            suggested_rollback = min(price_change_pct * 0.5, price_change_pct - 2)  # Rollback 50% or to +2%
            
            action = BusinessAction(
                action_id=f"PRICE_ADJ_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.PRICE_ADJUSTMENT,
                priority=ActionPriority.HIGH,
                description=f"Price increase of {price_change_pct:.1f}% caused {sales_change_pct:.1f}% sales drop. Recommend {suggested_rollback:.1f}% price reduction.",
                triggered_by=finding,
                parameters={
                    'product_id': finding.context.get('product_id'),
                    'current_price': finding.context.get('current_price'),
                    'suggested_price_change_pct': -suggested_rollback,
                    'elasticity': elasticity,
                    'reason': 'causal_inference_price_elasticity'
                },
                expected_impact=f"Expected to recover ~{abs(sales_change_pct * 0.5):.1f}% of lost sales",
                status='pending',
                created_at=datetime.now().isoformat()
            )
            
            actions.append(action)
        
        # If price decrease boosted sales significantly
        elif sales_change_pct > 15 and price_change_pct < 0:
            
            action = BusinessAction(
                action_id=f"PROMO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.PROMOTION_TRIGGER,
                priority=ActionPriority.MEDIUM,
                description=f"Price decrease of {abs(price_change_pct):.1f}% caused {sales_change_pct:.1f}% sales increase. Extend promotion.",
                triggered_by=finding,
                parameters={
                    'product_id': finding.context.get('product_id'),
                    'promotion_extension_days': 7,
                    'elasticity': elasticity
                },
                expected_impact=f"Continue high sales volume",
                status='pending',
                created_at=datetime.now().isoformat()
            )
            
            actions.append(action)
        
        return actions
    
    def _handle_weather_impact(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Handle: "Weather caused demand change"
        Action: Adjust inventory, pricing, promotions
        """
        actions = []
        
        weather_type = finding.context.get('weather_type', 'unknown')
        impact_magnitude = finding.magnitude
        
        # Monsoon causing sales drop
        if weather_type == 'monsoon' and impact_magnitude < -5000:
            
            action = BusinessAction(
                action_id=f"MONSOON_INV_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.INVENTORY_TRANSFER,
                priority=ActionPriority.MEDIUM,
                description=f"Monsoon causing ₹{abs(impact_magnitude):,.0f}/day revenue drop. Reduce perishable inventory orders.",
                triggered_by=finding,
                parameters={
                    'category': 'perishables',
                    'order_reduction_pct': 20,
                    'duration_days': 30,
                    'reason': 'monsoon_demand_reduction'
                },
                expected_impact="Reduce waste and holding costs",
                status='pending',
                created_at=datetime.now().isoformat()
            )
            
            actions.append(action)
        
        # Hot weather boosting beverage sales
        elif weather_type == 'hot' and impact_magnitude > 3000:
            
            action = BusinessAction(
                action_id=f"HEAT_REORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.AUTO_REORDER,
                priority=ActionPriority.HIGH,
                description=f"Hot weather driving ₹{impact_magnitude:,.0f}/day revenue increase. Increase beverage inventory.",
                triggered_by=finding,
                parameters={
                    'category': 'beverages',
                    'order_increase_pct': 30,
                    'fast_delivery': True,
                    'reason': 'weather_driven_demand'
                },
                expected_impact="Prevent stockouts during high demand",
                status='pending',
                created_at=datetime.now().isoformat()
            )
            
            actions.append(action)
        
        return actions
    
    def _handle_holiday_effect(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Handle: "Holiday caused sales surge"
        Action: Pre-stock for next holiday, optimize pricing
        """
        actions = []
        
        holiday_name = finding.context.get('holiday', 'unknown')
        revenue_lift = finding.magnitude
        
        # Significant holiday effect detected
        if revenue_lift > 10000:
            
            # Action 1: Update forecast for next year
            action1 = BusinessAction(
                action_id=f"HOLIDAY_FORECAST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.FORECAST_UPDATE,
                priority=ActionPriority.LOW,
                description=f"{holiday_name} caused ₹{revenue_lift:,.0f}/day lift. Update next year's forecast.",
                triggered_by=finding,
                parameters={
                    'holiday': holiday_name,
                    'expected_lift_pct': (revenue_lift / finding.context.get('baseline_revenue', 50000)) * 100,
                    'apply_to_next_occurrence': True
                },
                expected_impact="Improved forecast accuracy for next year",
                status='pending',
                created_at=datetime.now().isoformat()
            )
            
            # Action 2: Pre-order for next holiday
            days_to_next = finding.context.get('days_to_next_occurrence', 365)
            
            if days_to_next < 60:  # If next occurrence is within 2 months
                action2 = BusinessAction(
                    action_id=f"HOLIDAY_PREORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    action_type=ActionType.AUTO_REORDER,
                    priority=ActionPriority.HIGH,
                    description=f"Next {holiday_name} in {days_to_next} days. Pre-order inventory based on {revenue_lift:,.0f} expected lift.",
                    triggered_by=finding,
                    parameters={
                        'categories': finding.context.get('top_categories', ['all']),
                        'order_increase_pct': 50,
                        'lead_time_days': 14,
                        'reason': 'holiday_preparation'
                    },
                    expected_impact=f"Capture ₹{revenue_lift * 0.8:,.0f} potential revenue",
                    status='pending',
                    created_at=datetime.now().isoformat()
                )
                
                actions.append(action2)
            
            actions.append(action1)
        
        return actions
    
    def _handle_stockout_risk(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Handle: "Low inventory causing lost sales"
        Action: Emergency reorder
        """
        actions = []
        
        stockout_probability = finding.magnitude
        product_id = finding.context.get('product_id')
        
        if stockout_probability > 0.70:  # >70% chance of stockout
            
            action = BusinessAction(
                action_id=f"EMERGENCY_REORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.AUTO_REORDER,
                priority=ActionPriority.CRITICAL,
                description=f"Product {product_id}: {stockout_probability*100:.0f}% stockout risk. Emergency reorder required.",
                triggered_by=finding,
                parameters={
                    'product_id': product_id,
                    'quantity': finding.context.get('optimal_order_qty'),
                    'expedited_shipping': True,
                    'reason': 'stockout_prevention'
                },
                expected_impact=f"Prevent ₹{finding.context.get('lost_revenue_estimate', 0):,.0f} lost sales",
                status='approved' if stockout_probability > 0.85 else 'pending',
                created_at=datetime.now().isoformat()
            )
            
            actions.append(action)
        
        return actions
    
    def _handle_demand_surge(self, finding: CausalFinding) -> List[BusinessAction]:
        """
        Handle: "Unexpected demand surge detected"
        Action: Alert + reorder
        """
        actions = []
        
        surge_magnitude = finding.magnitude  # % increase
        
        if surge_magnitude > 50:  # >50% demand increase
            
            # Alert manager
            action1 = BusinessAction(
                action_id=f"SURGE_ALERT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type=ActionType.ALERT_MANAGER,
                priority=ActionPriority.HIGH,
                description=f"Demand surge detected: {surge_magnitude:.0f}% increase. Investigate cause and adjust operations.",
                triggered_by=finding,
                parameters={
                    'alert_type': 'demand_surge',
                    'magnitude': surge_magnitude,
                    'suspected_causes': finding.context.get('potential_causes', []),
                    'notify': ['operations_manager', 'inventory_manager']
                },
                expected_impact="Rapid response to market changes",
                status='approved',
                created_at=datetime.now().isoformat()
            )
            
            # Auto-reorder if very confident
            if finding.confidence > 0.90:
                action2 = BusinessAction(
                    action_id=f"SURGE_REORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    action_type=ActionType.AUTO_REORDER,
                    priority=ActionPriority.HIGH,
                    description=f"Auto-reorder triggered by {surge_magnitude:.0f}% demand surge",
                    triggered_by=finding,
                    parameters={
                        'order_increase_pct': min(surge_magnitude * 0.7, 100),  # Order 70% of surge or max 100%
                        'fast_delivery': True
                    },
                    expected_impact="Meet unexpected demand",
                    status='pending',
                    created_at=datetime.now().isoformat()
                )
                
                actions.append(action2)
            
            actions.append(action1)
        
        return actions
    
    def execute_action(self, action: BusinessAction) -> Dict[str, Any]:
        """
        Execute an approved action
        
        Returns:
            Execution result
        """
        if action.status != 'approved':
            return {'success': False, 'message': 'Action not approved'}
        
        logger.info(f"Executing action: {action.action_id} ({action.action_type.value})")
        
        try:
            # Route to execution handler
            if action.action_type == ActionType.AUTO_REORDER:
                result = self._execute_auto_reorder(action)
            
            elif action.action_type == ActionType.PRICE_ADJUSTMENT:
                result = self._execute_price_adjustment(action)
            
            elif action.action_type == ActionType.PROMOTION_TRIGGER:
                result = self._execute_promotion(action)
            
            elif action.action_type == ActionType.ALERT_MANAGER:
                result = self._execute_alert(action)
            
            elif action.action_type == ActionType.FORECAST_UPDATE:
                result = self._execute_forecast_update(action)
            
            elif action.action_type == ActionType.INVENTORY_TRANSFER:
                result = self._execute_inventory_transfer(action)
            
            else:
                result = {'success': False, 'message': f'Unknown action type: {action.action_type}'}
            
            # Update action status
            if result.get('success'):
                action.status = 'executed'
                action.executed_at = datetime.now().isoformat()
                self.executed_actions.append(action)
            else:
                action.status = 'failed'
            
            return result
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.status = 'failed'
            return {'success': False, 'message': str(e)}
    
    def _execute_auto_reorder(self, action: BusinessAction) -> Dict[str, Any]:
        """Execute automatic reorder"""
        params = action.parameters
        
        # In production, this would call procurement API
        logger.info(f"AUTO-REORDER: Product {params.get('product_id')}, Qty: {params.get('quantity')}")
        
        return {
            'success': True,
            'message': 'Purchase order created',
            'order_id': f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'details': params
        }
    
    def _execute_price_adjustment(self, action: BusinessAction) -> Dict[str, Any]:
        """Execute price adjustment"""
        params = action.parameters
        
        logger.info(f"PRICE-ADJUST: Product {params.get('product_id')}, Change: {params.get('suggested_price_change_pct')}%")
        
        return {
            'success': True,
            'message': 'Price updated',
            'product_id': params.get('product_id'),
            'new_price': params.get('current_price', 0) * (1 + params.get('suggested_price_change_pct', 0)/100)
        }
    
    def _execute_promotion(self, action: BusinessAction) -> Dict[str, Any]:
        """Execute promotion trigger"""
        params = action.parameters
        
        logger.info(f"PROMOTION: Product {params.get('product_id')}, Extension: {params.get('promotion_extension_days')} days")
        
        return {
            'success': True,
            'message': 'Promotion extended',
            'details': params
        }
    
    def _execute_alert(self, action: BusinessAction) -> Dict[str, Any]:
        """Send alert to manager"""
        params = action.parameters
        
        logger.info(f"ALERT: {params.get('alert_type')} sent to {params.get('notify')}")
        
        # In production, send email/SMS/WhatsApp
        return {
            'success': True,
            'message': 'Alert sent',
            'recipients': params.get('notify', [])
        }
    
    def _execute_forecast_update(self, action: BusinessAction) -> Dict[str, Any]:
        """Update forecast model"""
        params = action.parameters
        
        logger.info(f"FORECAST-UPDATE: {params.get('holiday')} lift: {params.get('expected_lift_pct')}%")
        
        return {
            'success': True,
            'message': 'Forecast model updated',
            'details': params
        }
    
    def _execute_inventory_transfer(self, action: BusinessAction) -> Dict[str, Any]:
        """Execute inventory transfer/adjustment"""
        params = action.parameters
        
        logger.info(f"INVENTORY-TRANSFER: Category {params.get('category')}, Adjustment: {params.get('order_reduction_pct')}%")
        
        return {
            'success': True,
            'message': 'Inventory adjusted',
            'details': params
        }
    
    def get_pending_actions(self, priority: Optional[ActionPriority] = None) -> List[BusinessAction]:
        """Get all pending actions, optionally filtered by priority"""
        pending = [a for a in self.action_queue if a.status == 'pending']
        
        if priority:
            pending = [a for a in pending if a.priority == priority]
        
        return pending
    
    def approve_action(self, action_id: str) -> bool:
        """Manually approve an action"""
        for action in self.action_queue:
            if action.action_id == action_id and action.status == 'pending':
                action.status = 'approved'
                logger.info(f"Action approved: {action_id}")
                return True
        return False
    
    def get_action_summary(self) -> Dict[str, Any]:
        """Get summary of all actions"""
        return {
            'total_actions': len(self.action_queue),
            'pending': len([a for a in self.action_queue if a.status == 'pending']),
            'approved': len([a for a in self.action_queue if a.status == 'approved']),
            'executed': len(self.executed_actions),
            'by_priority': {
                'critical': len([a for a in self.action_queue if a.priority == ActionPriority.CRITICAL]),
                'high': len([a for a in self.action_queue if a.priority == ActionPriority.HIGH]),
                'medium': len([a for a in self.action_queue if a.priority == ActionPriority.MEDIUM]),
                'low': len([a for a in self.action_queue if a.priority == ActionPriority.LOW])
            },
            'by_type': {
                at.value: len([a for a in self.action_queue if a.action_type == at])
                for at in ActionType
            }
        }


# FastAPI Integration
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/causal/actions", tags=["Causal Actions"])

# Global engine instance
_action_engine: Optional[CausalActionEngine] = None

def get_action_engine() -> CausalActionEngine:
    global _action_engine
    if _action_engine is None:
        _action_engine = CausalActionEngine(auto_execute_threshold=0.95)
    return _action_engine


class CausalFindingRequest(BaseModel):
    finding_type: str
    cause: str
    effect: str
    magnitude: float
    confidence: float
    p_value: float
    context: Dict[str, Any]


@router.post("/process")
async def process_causal_finding(request: CausalFindingRequest):
    """Process a causal finding and generate actions"""
    engine = get_action_engine()
    
    finding = CausalFinding(
        finding_type=request.finding_type,
        cause=request.cause,
        effect=request.effect,
        magnitude=request.magnitude,
        confidence=request.confidence,
        p_value=request.p_value,
        timestamp=datetime.now().isoformat(),
        context=request.context
    )
    
    actions = engine.process_causal_finding(finding)
    
    return {
        'finding': asdict(finding),
        'actions_generated': len(actions),
        'actions': [a.to_dict() for a in actions],
        'auto_approved': len([a for a in actions if a.status == 'approved'])
    }


@router.get("/pending")
async def get_pending_actions(priority: Optional[str] = None):
    """Get all pending actions"""
    engine = get_action_engine()
    
    priority_enum = ActionPriority(priority) if priority else None
    pending = engine.get_pending_actions(priority_enum)
    
    return {
        'count': len(pending),
        'actions': [a.to_dict() for a in pending]
    }


@router.post("/approve/{action_id}")
async def approve_action(action_id: str):
    """Approve a pending action"""
    engine = get_action_engine()
    
    success = engine.approve_action(action_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Action not found or not pending")
    
    return {'status': 'approved', 'action_id': action_id}


@router.post("/execute/{action_id}")
async def execute_action(action_id: str):
    """Execute an approved action"""
    engine = get_action_engine()
    
    # Find action
    action = next((a for a in engine.action_queue if a.action_id == action_id), None)
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    result = engine.execute_action(action)
    
    return result


@router.get("/summary")
async def get_action_summary():
    """Get summary of all actions"""
    engine = get_action_engine()
    return engine.get_action_summary()
