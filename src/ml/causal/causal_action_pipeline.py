"""
Causal Action Pipeline
Connects causal insights directly to automated business actions

This is the "closing the loop" component that answers:
"Causal model found X... now what happens?"
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ActionContext:
    """Context for action execution"""
    action: str
    confidence: float
    expected_roi: float
    approval_required: bool
    estimated_impact: Dict[str, Any]
    recommended_parameters: Dict[str, Any]


class PricingAgent:
    """Automated pricing adjustment agent"""
    
    async def suggest_adjustment(
        self,
        current_price: float,
        recommended_change: float,
        expected_lift: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest price adjustment based on causal finding
        
        Args:
            current_price: Current product price
            recommended_change: Recommended % change (negative = decrease)
            expected_lift: Expected revenue recovery
        
        Returns:
            Price adjustment recommendation
        """
        new_price = current_price * (1 + recommended_change / 100)
        
        return {
            'current_price': current_price,
            'recommended_price': new_price,
            'change_percent': recommended_change,
            'expected_revenue_recovery': expected_lift.get('revenue_recovery', 0),
            'confidence': 0.95,
            'action_type': 'price_adjustment'
        }


class InventoryAgent:
    """Automated inventory management agent"""
    
    async def reduce_reorder_quantity(
        self,
        products: list,
        temporary_adjustment_days: int
    ) -> Dict[str, Any]:
        """
        Temporarily adjust reorder quantities
        
        Args:
            products: List of affected products
            temporary_adjustment_days: Duration of adjustment
        
        Returns:
            Inventory adjustment plan
        """
        return {
            'affected_products': products,
            'adjustment_type': 'reduce_reorder',
            'duration_days': temporary_adjustment_days,
            'reduction_percent': 20,
            'reason': 'external_factor_impact',
            'action_type': 'inventory_adjustment'
        }


class CausalActionPipeline:
    """
    Main pipeline connecting causal insights to automated actions
    
    This is the critical component that closes the loop:
    Causal Analysis → Automated Action → Business Impact
    """
    
    def __init__(self):
        self.pricing_agent = PricingAgent()
        self.inventory_agent = InventoryAgent()
        self.action_history = []
        
    async def process_causal_finding(self, finding: Dict[str, Any]) -> ActionContext:
        """
        Process a causal finding and determine appropriate action
        
        Args:
            finding: Causal inference result with:
                - factor: Causal factor ('price', 'weather', 'holiday', etc.)
                - impact: Impact magnitude (% or absolute)
                - confidence: Model confidence (0-1)
                - context: Additional context
                - counterfactual_forecast: Expected outcome if action taken
        
        Returns:
            ActionContext with recommended action
        """
        factor = finding.get('factor')
        impact = finding.get('impact')
        confidence = finding.get('confidence')
        context = finding.get('context', {})
        
        # Route to appropriate agent based on causal factor
        
        # CASE 1: Price Elasticity Detected
        if factor == 'price' and impact < -10:
            logger.info(f"Price impact detected: {impact}%. Triggering pricing agent.")
            
            # Trigger pricing agent
            price_suggestion = await self.pricing_agent.suggest_adjustment(
                current_price=context.get('price', 100),
                recommended_change=-5,  # Reduce by 5%
                expected_lift=finding.get('counterfactual_forecast', {})
            )
            
            # Create approval workflow
            action_context = await self.create_approval_request(
                action='price_adjustment',
                confidence=confidence,
                roi_forecast=finding.get('revenue_impact', 0),
                parameters=price_suggestion
            )
            
            self.action_history.append({
                'timestamp': datetime.now().isoformat(),
                'finding': finding,
                'action': action_context
            })
            
            return action_context
        
        # CASE 2: Weather Impact Detected
        elif factor == 'weather' and impact < -8:
            logger.info(f"Weather impact detected: {impact}%. Adjusting inventory.")
            
            # Can't control weather, but can adjust inventory
            inventory_plan = await self.inventory_agent.reduce_reorder_quantity(
                products=finding.get('affected_products', []),
                temporary_adjustment_days=14
            )
            
            action_context = ActionContext(
                action=inventory_plan['action_type'],
                confidence=confidence,
                expected_roi=0,  # Cost savings (avoid excess inventory)
                approval_required=confidence < 0.90,
                estimated_impact={
                    'inventory_reduction': inventory_plan['reduction_percent'],
                    'cost_savings': 'TBD based on SKU costs'
                },
                recommended_parameters=inventory_plan
            )
            
            self.action_history.append({
                'timestamp': datetime.now().isoformat(),
                'finding': finding,
                'action': action_context
            })
            
            return action_context
        
        # CASE 3: Holiday Effect Detected
        elif factor == 'holiday' and impact > 20:
            logger.info(f"Holiday effect detected: +{impact}%. Preparing inventory.")
            
            # Pre-order for upcoming holiday
            preorder_plan = {
                'action': 'auto_reorder',
                'reason': 'upcoming_holiday',
                'order_increase_pct': impact * 0.7,  # Order 70% of expected surge
                'lead_time_days': finding.get('days_until_holiday', 30)
            }
            
            action_context = ActionContext(
                action='auto_reorder',
                confidence=confidence,
                expected_roi=impact * finding.get('baseline_revenue', 50000),
                approval_required=False if confidence > 0.95 else True,
                estimated_impact={
                    'revenue_opportunity': impact * finding.get('baseline_revenue', 50000),
                    'inventory_increase': preorder_plan['order_increase_pct']
                },
                recommended_parameters=preorder_plan
            )
            
            return action_context
        
        # CASE 4: Demand Surge (Unknown Cause)
        elif factor == 'demand_surge' and impact > 30:
            logger.info(f"Demand surge detected: +{impact}%. Alerting manager.")
            
            alert_plan = {
                'action': 'alert_manager',
                'priority': 'high',
                'message': f'Unexpected {impact}% demand surge detected',
                'investigation_required': True
            }
            
            action_context = ActionContext(
                action='alert_manager',
                confidence=confidence,
                expected_roi=0,
                approval_required=False,
                estimated_impact={'alert_sent': True},
                recommended_parameters=alert_plan
            )
            
            return action_context
        
        # Default: No action recommended
        else:
            logger.info(f"No automated action for factor={factor}, impact={impact}")
            
            return ActionContext(
                action='monitor',
                confidence=confidence,
                expected_roi=0,
                approval_required=False,
                estimated_impact={'monitoring': True},
                recommended_parameters={'reason': 'impact_below_threshold'}
            )
    
    async def create_approval_request(
        self,
        action: str,
        confidence: float,
        roi_forecast: float,
        parameters: Dict[str, Any]
    ) -> ActionContext:
        """
        Create approval workflow for actions requiring human review
        
        Args:
            action: Type of action
            confidence: Model confidence
            roi_forecast: Expected ROI
            parameters: Action parameters
        
        Returns:
            ActionContext with approval workflow
        """
        # Determine if auto-approval threshold met
        auto_approve = confidence >= 0.95 and roi_forecast > 0
        
        approval_context = ActionContext(
            action=action,
            confidence=confidence,
            expected_roi=roi_forecast,
            approval_required=not auto_approve,
            estimated_impact={
                'roi_forecast': roi_forecast,
                'confidence_level': 'high' if confidence > 0.90 else 'medium'
            },
            recommended_parameters=parameters
        )
        
        if auto_approve:
            logger.info(f"Action auto-approved: {action} (confidence={confidence:.2f})")
        else:
            logger.info(f"Action requires approval: {action} (confidence={confidence:.2f})")
            # In production: Send to approval queue/manager dashboard
        
        return approval_context
    
    def get_action_history(self, limit: int = 50) -> list:
        """Get recent action history"""
        return self.action_history[-limit:]
    
    def get_action_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        total_actions = len(self.action_history)
        
        if total_actions == 0:
            return {'total_actions': 0}
        
        auto_approved = sum(
            1 for a in self.action_history 
            if not a['action'].approval_required
        )
        
        avg_confidence = sum(
            a['action'].confidence for a in self.action_history
        ) / total_actions
        
        total_expected_roi = sum(
            a['action'].expected_roi for a in self.action_history
        )
        
        return {
            'total_actions': total_actions,
            'auto_approved': auto_approved,
            'auto_approval_rate': auto_approved / total_actions,
            'avg_confidence': avg_confidence,
            'total_expected_roi': total_expected_roi,
            'action_types': self._count_action_types()
        }
    
    def _count_action_types(self) -> Dict[str, int]:
        """Count actions by type"""
        counts = {}
        for record in self.action_history:
            action_type = record['action'].action
            counts[action_type] = counts.get(action_type, 0) + 1
        return counts


# FastAPI Integration
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/causal/pipeline", tags=["Causal Action Pipeline"])

# Global pipeline instance
_pipeline: Optional[CausalActionPipeline] = None

def get_pipeline() -> CausalActionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = CausalActionPipeline()
    return _pipeline


class CausalFindingInput(BaseModel):
    factor: str
    impact: float
    confidence: float
    context: Dict[str, Any]
    counterfactual_forecast: Optional[Dict[str, Any]] = None
    revenue_impact: Optional[float] = None
    affected_products: Optional[list] = None


@router.post("/process")
async def process_finding(finding: CausalFindingInput):
    """Process a causal finding and generate action"""
    pipeline = get_pipeline()
    
    finding_dict = finding.dict()
    action_context = await pipeline.process_causal_finding(finding_dict)
    
    return {
        'action': action_context.action,
        'confidence': action_context.confidence,
        'expected_roi': action_context.expected_roi,
        'approval_required': action_context.approval_required,
        'estimated_impact': action_context.estimated_impact,
        'parameters': action_context.recommended_parameters
    }


@router.get("/history")
async def get_action_history(limit: int = 50):
    """Get action history"""
    pipeline = get_pipeline()
    return {'history': pipeline.get_action_history(limit)}


@router.get("/metrics")
async def get_pipeline_metrics():
    """Get pipeline performance metrics"""
    pipeline = get_pipeline()
    return pipeline.get_action_metrics()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        pipeline = CausalActionPipeline()
        
        # Example 1: Price elasticity finding
        price_finding = {
            'factor': 'price',
            'impact': -15,  # -15% sales drop
            'confidence': 0.96,
            'context': {'price': 120, 'product_id': 'PROD_001'},
            'counterfactual_forecast': {'revenue_recovery': 8.5},
            'revenue_impact': 50000
        }
        
        result = await pipeline.process_causal_finding(price_finding)
        print(f"\nPrice Elasticity Action:")
        print(f"  Action: {result.action}")
        print(f"  Approval Required: {result.approval_required}")
        print(f"  Expected ROI: ₹{result.expected_roi:,.0f}")
        
        # Example 2: Weather impact
        weather_finding = {
            'factor': 'weather',
            'impact': -12,
            'confidence': 0.88,
            'context': {'condition': 'heavy_rain'},
            'affected_products': ['outdoor_gear', 'footwear']
        }
        
        result = await pipeline.process_causal_finding(weather_finding)
        print(f"\nWeather Impact Action:")
        print(f"  Action: {result.action}")
        print(f"  Parameters: {result.recommended_parameters}")
        
        # Show metrics
        metrics = pipeline.get_action_metrics()
        print(f"\nPipeline Metrics:")
        print(f"  Total Actions: {metrics['total_actions']}")
        print(f"  Auto-Approval Rate: {metrics['auto_approval_rate']*100:.1f}%")
    
    asyncio.run(demo())
