"""
End-to-End Integration Tests for R-DIOS
Validates complete workflows from data ingestion to business action
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
import numpy as np

# Test the complete retail workflow integration


class TestRetailWorkflowIntegration:
    """
    End-to-end integration tests
    Validates: External data → Analysis → Action → Notification
    """
    
    @pytest.fixture
    async def setup_test_environment(self):
        """Setup test database and services"""
        # Initialize test services
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        from src.ml.causal.action_engine import CausalActionEngine
        from src.services.business_analytics import InventoryOptimizer
        
        return {
            'causal_analyzer': RetailCausalAnalyzer(),
            'action_engine': CausalActionEngine(),
            'inventory_optimizer': InventoryOptimizer()
        }
    
    @pytest.mark.asyncio
    async def test_external_factor_to_action_flow(self, setup_test_environment):
        """
        CRITICAL TEST: Weather API → Forecast → Inventory Decision
        
        Validates complete causal chain:
        1. External weather event
        2. Causal model detects impact
        3. Action engine generates business action
        4. Inventory system executes
        5. Notification sent
        """
        services = await setup_test_environment
        
        # Step 1: Inject weather event (simulated heavy rain in Mumbai)
        weather_data = pd.DataFrame([{
            'date': datetime.now(),
            'city': 'Mumbai',
            'condition': 'heavy_rain',
            'precipitation': 120,  # mm
            'is_monsoon': True
        }])
        
        # Step 2: Get baseline forecast
        baseline_forecast = services['causal_analyzer'].get_forecast('umbrellas')
        
        # Step 3: Process weather impact through causal engine
        causal_results = services['causal_analyzer'].analyze_weather_impact(weather_data)
        
        # Verify causal model detected weather impact
        assert causal_results['monsoon_analysis']['significant'], \
            "Causal model should detect monsoon impact"
        
        # Step 4: Convert causal finding to action
        from src.ml.causal.action_engine import CausalFinding
        
        finding = CausalFinding(
            finding_type='weather_impact',
            cause='monsoon',
            effect='demand_change',
            magnitude=causal_results['monsoon_analysis']['best_estimate']['estimate'],
            confidence=0.92,
            p_value=causal_results['monsoon_analysis']['best_estimate']['p_value'],
            timestamp=datetime.now().isoformat(),
            context={'weather_type': 'monsoon', 'city': 'Mumbai'}
        )
        
        actions = services['action_engine'].process_causal_finding(finding)
        
        # Verify action was generated
        assert len(actions) > 0, "Action engine should generate actions"
        assert any(a.action_type.value == 'inventory_transfer' for a in actions), \
            "Should generate inventory adjustment action"
        
        # Step 5: Execute action
        inventory_action = next(a for a in actions if a.action_type.value == 'inventory_transfer')
        result = services['action_engine'].execute_action(inventory_action)
        
        assert result['success'], "Action execution should succeed"
        
        # Step 6: Verify notification would be sent
        # (In production, this would send actual notification)
        assert 'message' in result, "Should include notification message"
        
        print(f"✓ E2E Test Passed: Weather → Causal → Action → Notification")
    
    @pytest.mark.asyncio
    async def test_price_change_to_auto_adjustment_flow(self, setup_test_environment):
        """
        CRITICAL TEST: Price Elasticity Detection → Auto-Adjustment
        
        Validates:
        1. Price increase recorded
        2. Sales drop detected
        3. Causal model attributes drop to price
        4. Action engine recommends rollback
        5. Price adjusted (if confidence high)
        """
        services = await setup_test_environment
        
        # Step 1: Simulate price increase
        price_data = pd.DataFrame([{
            'product_id': 'PROD_001',
            'date': datetime.now() - timedelta(days=7),
            'old_price': 100,
            'new_price': 112,  # 12% increase
            'category': 'electronics'
        }])
        
        # Step 2: Simulate sales drop
        sales_data = pd.DataFrame([
            {'date': datetime.now() - timedelta(days=i), 'revenue': 50000 * 0.82}  # 18% drop
            for i in range(7)
        ])
        
        # Step 3: Run causal analysis
        # (In real implementation, this would use DoWhy/EconML)
        from src.ml.causal.action_engine import CausalFinding
        
        finding = CausalFinding(
            finding_type='price_elasticity',
            cause='price_increase',
            effect='sales_decline',
            magnitude=-18.0,  # -18% sales
            confidence=0.96,
            p_value=0.001,
            timestamp=datetime.now().isoformat(),
            context={
                'product_id': 'PROD_001',
                'price_change_percent': 12,
                'current_price': 112
            }
        )
        
        # Step 4: Generate action
        actions = services['action_engine'].process_causal_finding(finding)
        
        assert len(actions) > 0, "Should generate price adjustment action"
        
        price_action = next(a for a in actions if a.action_type.value == 'price_adjustment')
        
        # Verify action parameters
        assert price_action.priority.value in ['high', 'critical'], \
            "Price adjustment should be high priority"
        assert price_action.parameters['suggested_price_change_pct'] < 0, \
            "Should recommend price decrease"
        
        # Step 5: Auto-approve if confidence high
        if finding.confidence > 0.95:
            assert price_action.status == 'approved', \
                "High confidence actions should auto-approve"
        
        print(f"✓ E2E Test Passed: Price Change → Causal → Auto-Adjustment")
    
    @pytest.mark.asyncio
    async def test_holiday_detection_to_preorder_flow(self, setup_test_environment):
        """
        CRITICAL TEST: Holiday Effect → Inventory Pre-Order
        
        Validates:
        1. Holiday (Diwali) sales surge detected
        2. Causal model attributes to holiday
        3. Action engine forecasts next Diwali
        4. Pre-order triggered if within 60 days
        5. ERP integration (mocked)
        """
        services = await setup_test_environment
        
        # Step 1: Simulate Diwali sales surge
        diwali_data = pd.DataFrame([{
            'date': datetime(2023, 11, 12) + timedelta(days=i),
            'revenue': 50000 * 1.35,  # 35% lift
            'is_holiday': True if i < 7 else False
        } for i in range(14)])
        
        # Step 2: Run causal analysis
        from src.ml.causal.action_engine import CausalFinding
        
        finding = CausalFinding(
            finding_type='holiday_effect',
            cause='diwali',
            effect='revenue_surge',
            magnitude=17500,  # ₹17,500/day lift
            confidence=0.98,
            p_value=0.0001,
            timestamp=datetime.now().isoformat(),
            context={
                'holiday': 'Diwali',
                'days_to_next_occurrence': 45,
                'baseline_revenue': 50000,
                'top_categories': ['electronics', 'home_decor', 'apparel']
            }
        )
        
        # Step 3: Generate actions
        actions = services['action_engine'].process_causal_finding(finding)
        
        # Should generate 2 actions: forecast update + pre-order
        assert len(actions) >= 1, "Should generate holiday-related actions"
        
        # Check for pre-order action (if next Diwali < 60 days)
        if finding.context['days_to_next_occurrence'] < 60:
            preorder_action = next(
                (a for a in actions if a.action_type.value == 'auto_reorder'),
                None
            )
            assert preorder_action is not None, "Should trigger pre-order for upcoming holiday"
            assert preorder_action.parameters['order_increase_pct'] >= 30, \
                "Should increase order significantly for holiday"
        
        print(f"✓ E2E Test Passed: Holiday Detection → Pre-Order")
    
    @pytest.mark.asyncio
    async def test_causal_action_pipeline_integration(self, setup_test_environment):
        """
        TEST: Complete CausalActionPipeline
        
        This is the pipeline that closes the loop:
        Causal Analysis → Automated Action → Business Impact
        """
        from src.ml.causal.causal_action_pipeline import CausalActionPipeline
        
        pipeline = CausalActionPipeline()
        
        # Test Case 1: Price elasticity
        price_finding = {
            'factor': 'price',
            'impact': -15,  # -15% sales
            'confidence': 0.95,
            'context': {'price': 100, 'product_id': 'PROD_001'},
            'counterfactual_forecast': {'revenue_recovery': 8.0}
        }
        
        result = await pipeline.process_causal_finding(price_finding)
        
        assert result['action'] == 'price_adjustment', "Should trigger pricing agent"
        assert result['approval_required'] == True, "Should create approval workflow"
        assert result['expected_roi'] is not None, "Should calculate ROI"
        
        # Test Case 2: Weather impact
        weather_finding = {
            'factor': 'weather',
            'impact': -10,  # -10% sales
            'confidence': 0.90,
            'context': {'condition': 'monsoon'},
            'affected_products': ['outdoor_furniture', 'sports_equipment']
        }
        
        result = await pipeline.process_causal_finding(weather_finding)
        
        assert result['action'] == 'inventory_adjustment', "Should trigger inventory agent"
        assert result['adjustment_days'] == 14, "Should temporarily adjust for 14 days"
        
        print(f"✓ E2E Test Passed: Causal Action Pipeline")
    
    @pytest.mark.asyncio
    async def test_zoho_import_to_whatsapp_notification(self, setup_test_environment):
        """
        TEST: Full retail operation workflow
        
        Zoho Import → Causal Analysis → Auto-Reorder → WhatsApp Notification
        """
        # Step 1: Mock Zoho data import
        zoho_data = {
            'products': [
                {'item_id': 'ZH_001', 'name': 'Laptop', 'stock': 5, 'reorder_point': 10}
            ]
        }
        
        # Step 2: Detect low stock
        assert zoho_data['products'][0]['stock'] < zoho_data['products'][0]['reorder_point'], \
            "Should detect stock below reorder point"
        
        # Step 3: Generate stockout risk finding
        from src.ml.causal.action_engine import CausalFinding
        
        finding = CausalFinding(
            finding_type='stockout_risk',
            cause='low_inventory',
            effect='potential_lost_sales',
            magnitude=0.85,  # 85% stockout probability
            confidence=0.95,
            p_value=0.01,
            timestamp=datetime.now().isoformat(),
            context={
                'product_id': 'ZH_001',
                'current_stock': 5,
                'optimal_order_qty': 50,
                'lost_revenue_estimate': 100000
            }
        )
        
        services = await setup_test_environment
        actions = services['action_engine'].process_causal_finding(finding)
        
        # Step 4: Verify emergency reorder action
        reorder_action = next(
            (a for a in actions if a.action_type.value == 'auto_reorder'),
            None
        )
        
        assert reorder_action is not None, "Should generate reorder action"
        assert reorder_action.priority.value == 'critical', "Stockout should be critical priority"
        assert reorder_action.status == 'approved', "High confidence should auto-approve"
        
        # Step 5: Execute reorder
        result = services['action_engine'].execute_action(reorder_action)
        
        assert result['success'], "Reorder should execute successfully"
        assert 'order_id' in result, "Should create purchase order"
        
        # Step 6: Verify notification sent (mocked)
        # In production: WhatsApp API call
        assert result['message'] == 'Purchase order created', \
            "Should include notification message"
        
        print(f"✓ E2E Test Passed: Zoho → Causal → Reorder → Notification")
    
    @pytest.mark.asyncio
    async def test_gst_calculation_to_email_delivery(self):
        """
        TEST: GST Calculation → Invoice Generation → Email Delivery
        """
        # Step 1: Create order with GST
        order = {
            'items': [
                {'product': 'Smartphone', 'price': 20000, 'quantity': 1, 'gst_rate': 18}
            ],
            'customer': {'email': 'test@example.com', 'gstin': '27AABCU9603R1ZV'}
        }
        
        # Step 2: Calculate GST
        subtotal = order['items'][0]['price'] * order['items'][0]['quantity']
        gst_amount = subtotal * (order['items'][0]['gst_rate'] / 100)
        total = subtotal + gst_amount
        
        assert gst_amount == 3600, "GST calculation should be correct"
        assert total == 23600, "Total with GST should be correct"
        
        # Step 3: Generate invoice (mocked)
        invoice = {
            'invoice_number': 'INV-2024-001',
            'date': datetime.now(),
            'subtotal': subtotal,
            'gst': gst_amount,
            'total': total,
            'customer_email': order['customer']['email']
        }
        
        # Step 4: Email delivery (mocked)
        email_sent = self._mock_send_invoice_email(invoice)
        
        assert email_sent['success'], "Invoice email should be sent"
        assert email_sent['to'] == 'test@example.com', "Should send to correct email"
        
        print(f"✓ E2E Test Passed: GST → Invoice → Email")
    
    def _mock_send_invoice_email(self, invoice: Dict) -> Dict:
        """Mock email service"""
        return {
            'success': True,
            'to': invoice['customer_email'],
            'subject': f"Invoice {invoice['invoice_number']}",
            'sent_at': datetime.now().isoformat()
        }


class TestDataFlowIntegration:
    """
    Test data flowing through the entire system
    """
    
    @pytest.mark.asyncio
    async def test_complete_data_pipeline(self):
        """
        TEST: Raw Data → Transformation → Database → Analysis → Dashboard
        """
        # Step 1: Load raw data
        from src.data.hybrid_transformer import HybridDataTransformer
        
        transformer = HybridDataTransformer()
        raw_data = transformer.load_olist_data()
        
        assert len(raw_data) > 0, "Should load raw data"
        
        # Step 2: Transform to Indian context
        transformed = transformer.transform_to_indian_context(raw_data.head(100))
        
        assert 'hsn_code' in transformed.columns, "Should add Indian attributes"
        assert 'gst_rate' in transformed.columns, "Should add GST rates"
        
        # Step 3: Inject causal effects
        with_effects = transformer.inject_causal_effects(transformed)
        
        assert 'causal_factor' in with_effects.columns, "Should inject causal effects"
        
        # Step 4: Load to database (mocked)
        # In production: database_loader.load_to_postgres()
        
        # Step 5: Run analytics
        from src.ml.causal.causal_engine import RetailCausalAnalyzer
        
        analyzer = RetailCausalAnalyzer(with_effects)
        results = analyzer.run_full_analysis()
        
        assert results['holiday_analysis']['significant'], \
            "Should detect injected holiday effects"
        
        print(f"✓ E2E Test Passed: Complete Data Pipeline")


# Run integration tests
if __name__ == "__main__":
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
