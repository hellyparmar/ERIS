"""
Example Conversations - Retail AI Assistant RAG System

This file demonstrates realistic conversations showing:
1. Query classification
2. Entity extraction
3. SQL generation
4. LLM response generation
5. Source citations
6. Follow-up conversations
"""

from app.ml.rag.query_classifier import QueryClassifier
from app.ml.rag.sql_generator import SQLGenerator
from app.ml.rag.enhanced_rag import EnhancedRAGService
from datetime import datetime, timedelta


def example_conversation_1():
    """
    Example 1: Sales Analysis Conversation
    User wants to understand recent sales performance
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Sales Analysis Conversation")
    print("="*80)
    
    classifier = QueryClassifier()
    sql_gen = SQLGenerator()
    rag = EnhancedRAGService()
    
    # User Question 1
    user_q1 = "What were our total sales last week?"
    print(f"\nUser: {user_q1}")
    
    # Step 1: Classify query
    intent = classifier.get_query_intent(user_q1)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    print(f"[ENTITIES] Extracted: {intent['entities']}")
    
    # Step 2: Generate SQL
    sql = sql_gen.natural_to_sql(user_q1, intent['entities'])
    print(f"[SQL GENERATED]\n{sql}")
    
    # Step 3: Validate safety
    is_safe, _ = sql_gen.is_safe_query(sql)
    print(f"[SAFETY CHECK] Query is safe: {is_safe}")
    
    # Step 4: Search RAG for context
    rag_results = rag.search(user_q1, top_k=3)
    print(f"[RAG RESULTS] Found {len(rag_results)} relevant documents")
    
    # Simulated LLM Response
    print(f"\n[ASSISTANT RESPONSE]")
    print("Based on our data, here's your sales performance for last week:")
    print("• Total Sales: ₹125,450")
    print("• Number of Transactions: 284")
    print("• Average Transaction: ₹442")
    print("• Top Performing Outlet: Mumbai (₹52,300)")
    print("• Top Product: Coffee (₹41,200)")
    print("[Sources: Sales Database, Product Index]")
    print("[Confidence: 0.98 | Response Time: 0.23s]")


def example_conversation_2():
    """
    Example 2: Anomaly Investigation Conversation
    User investigates unusual patterns
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Anomaly Investigation Conversation")
    print("="*80)
    
    classifier = QueryClassifier()
    sql_gen = SQLGenerator()
    rag = EnhancedRAGService()
    
    # User Question 1
    user_q1 = "Why did tea sales drop at Delhi outlet on Monday?"
    print(f"\nUser: {user_q1}")
    
    # Step 1: Classify
    intent = classifier.get_query_intent(user_q1)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    print(f"[ENTITIES] Product: {intent['entities'].get('product_name')}")
    print(f"[ENTITIES] Outlet: {intent['entities'].get('outlet')}")
    print(f"[ENTITIES] Timeframe: {intent['entities'].get('date_range')}")
    
    # Step 2: Generate SQL
    sql = sql_gen.natural_to_sql(user_q1, intent['entities'])
    print(f"[SQL GENERATED]\n{sql}")
    
    # Step 3: Search for insights
    rag_results = rag.search("tea sales anomaly Delhi", top_k=5)
    print(f"[RAG SEARCH] Found {len(rag_results)} insights")
    
    # Simulated Response
    print(f"\n[ASSISTANT RESPONSE]")
    print("Tea sales at Delhi outlet on Monday (March 24) showed a 45% decline.")
    print("\nPotential Causes:")
    print("1. Supply Disruption: Stock was replenished late (2:30 PM)")
    print("2. Local Event: Marathon in Delhi reduced foot traffic")
    print("3. Competitive Action: Competitor offered discount")
    print("4. Seasonal Pattern: Mondays typically 15% lower")
    print("\nRecommendation: Investigate supplier delays and monitor foot traffic.")
    print("[Sources: Sales History, Supply Logs, Market Insights]")
    print("[Confidence: 0.82 | Anomaly Score: 0.91]")
    
    # Follow-up question
    user_q2 = "What's the historical tea sales trend?"
    print(f"\n\nUser: {user_q2}")
    
    intent = classifier.get_query_intent(user_q2)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    
    sql = sql_gen.natural_to_sql(user_q2, intent['entities'])
    print(f"[SQL GENERATED] Time-series query for tea category")
    
    print(f"\n[ASSISTANT RESPONSE]")
    print("Tea sales trend (Last 12 Weeks):")
    print("Week 1 (Mar 1-7):   ₹8,500  | 284 units")
    print("Week 2 (Mar 8-14):  ₹8,200  | 274 units")
    print("Week 3 (Mar 15-21): ₹8,100  | 270 units")
    print("Week 4 (Mar 22-28): ₹6,800  | 227 units  ← Declining trend")
    print("\nTrend: 8.2% decline in 4 weeks (₹1,700 loss)")
    print("Action Items: Review pricing, boost promotions, check competition")
    print("[Forecast: Continued decline without intervention]")


def example_conversation_3():
    """
    Example 3: Comparative Analysis Conversation
    User compares outlets performance
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Comparative Analysis Conversation")
    print("="*80)
    
    classifier = QueryClassifier()
    sql_gen = SQLGenerator()
    
    # User Question
    user_q = "Compare sales performance across all outlets this month"
    print(f"\nUser: {user_q}")
    
    # Classify
    intent = classifier.get_query_intent(user_q)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    print(f"[INTENT] Comparison across: outlets")
    
    # Generate SQL
    sql = sql_gen.natural_to_sql(user_q, intent['entities'])
    print(f"[SQL GENERATED]\nGROUP BY outlet, aggregating total_amount")
    
    # Response
    print(f"\n[ASSISTANT RESPONSE]")
    print("March Sales Comparison Across Outlets:")
    print("\nRank | Outlet      | Sales      | Units | Avg Order | Trend")
    print("-----|-------------|------------|-------|-----------|-------")
    print("  1  | Mumbai      | ₹185,400   | 521   | ₹356      | ↑ 12%")
    print("  2  | Delhi       | ₹152,300   | 445   | ₹342      | ↓  5%")
    print("  3  | Bangalore   | ₹128,900   | 391   | ₹330      | ↑  8%")
    print("  4  | Hyderabad   | ₹95,200    | 284   | ₹335      | ↓  2%")
    print("  5  | Pune        | ₹78,500    | 235   | ₹334      | ↑ 15%")
    print("\nKey Insights:")
    print("• Mumbai leads with 33% of total sales")
    print("• Pune showing strongest growth (15%)")
    print("• Delhi declining, needs attention")
    print("• All outlets show similar avg order value (~₹335)")


def example_conversation_4():
    """
    Example 4: Forecasting & Recommendation Conversation
    User asks for predictive insights
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Forecasting & Recommendation Conversation")
    print("="*80)
    
    classifier = QueryClassifier()
    
    # User Question 1: Forecast
    user_q1 = "What will our sales be next month?"
    print(f"\nUser: {user_q1}")
    
    intent = classifier.get_query_intent(user_q1)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    
    print(f"\n[ASSISTANT RESPONSE]")
    print("Sales Forecast for April 2026:")
    print("Base Forecast: ₹890,000")
    print("Confidence Interval: ₹820,000 - ₹960,000")
    print("\nMonthly Breakdown:")
    print("Week 1: ₹210,000 (Normal)")
    print("Week 2: ₹235,000 (Easter - +10%)")
    print("Week 3: ₹225,000 (Post-holiday normalization)")
    print("Week 4: ₹220,000 (Month-end)")
    print("\nFactors Considered:")
    print("✓ Seasonal patterns")
    print("✓ Holiday calendar (Easter)")
    print("✓ Recent trend analysis")
    print("✓ Promotional calendar")
    
    # User Question 2: Recommendation
    user_q2 = "What should I do to increase sales?"
    print(f"\n\nUser: {user_q2}")
    
    intent = classifier.get_query_intent(user_q2)
    print(f"[CLASSIFICATION] Query Type: {intent['query_type']}")
    
    print(f"\n[ASSISTANT RESPONSE]")
    print("Strategic Recommendations to Boost Sales:")
    print("\n1. IMMEDIATE ACTIONS (This Week):")
    print("   • Launch 'Tea & Coffee' bundle promotion")
    print("   • Offer 15% discount on low-performing categories")
    print("   • Increase social media ads")
    print("   → Expected Impact: +8% sales")
    
    print("\n2. SHORT TERM (Next 2 Weeks):")
    print("   • Restock high-performing outlets (Mumbai, Pune)")
    print("   • Introduce new seasonal offerings")
    print("   • Staff training for upselling")
    print("   → Expected Impact: +12% sales")
    
    print("\n3. MEDIUM TERM (April):")
    print("   • Expand Delhi outlet (currently declining)")
    print("   • Launch loyalty program")
    print("   • Analyze competitor pricing")
    print("   → Expected Impact: +15% sales")
    
    print("\nPriority: Focus on Delhi (high growth potential)")


def example_conversation_5():
    """
    Example 5: Multi-turn Conversation with Context
    Shows how system maintains conversation context
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Multi-turn Conversation (With Context)")
    print("="*80)
    
    classifier = QueryClassifier()
    
    conversation_context = []
    
    # Turn 1
    user_q1 = "Show me sales for March"
    print(f"\nUser: {user_q1}")
    intent1 = classifier.get_query_intent(user_q1)
    print(f"[Q1 CLASSIFICATION] Type: {intent1['query_type']}")
    print("[ASSISTANT] March Sales: ₹640,800 across all outlets")
    conversation_context.append({"question": user_q1, "intent": intent1})
    
    # Turn 2
    user_q2 = "Compare to February"
    print(f"\nUser: {user_q2}")
    intent2 = classifier.get_query_intent(user_q2)
    print(f"[Q2 CLASSIFICATION] Type: {intent2['query_type']}")
    print(f"[CONTEXT AWARENESS] Comparing March to February")
    print("[ASSISTANT]")
    print("March vs February Comparison:")
    print("March:    ₹640,800 | 1,912 units")
    print("February: ₹578,200 | 1,745 units")
    print("Change:   +₹62,600 (+10.8%) | +167 units (+9.6%)")
    conversation_context.append({"question": user_q2, "intent": intent2})
    
    # Turn 3
    user_q3 = "Why is it higher?"
    print(f"\nUser: {user_q3}")
    intent3 = classifier.get_query_intent(user_q3)
    print(f"[Q3 CLASSIFICATION] Type: {intent3['query_type']}")
    print(f"[CONTEXT AWARENESS] Analyzing March vs Feb drivers")
    print("[ASSISTANT]")
    print("March performed better due to:")
    print("1. Holi Festival (+15% seasonal boost)")
    print("2. New product launch (Herbal Tea)")
    print("3. Extended promotional campaign")
    print("4. Improved staffing levels")
    print("5. Better weather (increased foot traffic)")
    print("\nTop contributors:")
    print("• Festival promotions: +₹38,200 (61%)")
    print("• New products: +₹15,000 (24%)")
    print("• Regular growth: +₹9,400 (15%)")


def example_conversation_6():
    """
    Example 6: Complex Entity Extraction
    Shows how system extracts multiple entities from complex questions
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Complex Entity Extraction")
    print("="*80)
    
    classifier = QueryClassifier()
    
    complex_question = "How did premium coffee sales at Mumbai outlet perform compared to last month's week 3?"
    print(f"\nUser: {complex_question}")
    
    intent = classifier.get_query_intent(complex_question)
    print(f"\n[CLASSIFICATION] Query Type: {intent['query_type']}")
    
    print(f"\n[ENTITY EXTRACTION]")
    entities = intent['entities']
    print(f"  Product Name:  {entities.get('product_name', 'Not detected')}")
    print(f"  Category/Type: Premium")
    print(f"  Outlet:        {entities.get('outlet', 'Not detected')}")
    print(f"  Date Range:    {entities.get('date_range', 'Not detected')}")
    print(f"  Time Period:   {entities.get('time_period', 'Not detected')}")
    print(f"  Metric:        {entities.get('metric', 'Not detected')}")
    
    print(f"\n[ASSISTANT RESPONSE]")
    print("Premium Coffee Sales Comparison:")
    print("\nCurrent Period (March 22-28):")
    print("• Sales: ₹12,450")
    print("• Units: 98")
    print("• Avg Price: ₹127")
    
    print("\nLast Month's Week 3 (Feb 15-21):")
    print("• Sales: ₹11,200")
    print("• Units: 92")
    print("• Avg Price: ₹122")
    
    print("\nComparison:")
    print("↑ Sales: +₹1,250 (+11.2%)")
    print("↑ Units: +6 (+6.5%)")
    print("↑ Avg Price: +₹5 (+4.1%)")
    print("\nAnalysis: Growth driven by both volume and price optimization")


def run_all_examples():
    """Run all example conversations."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " RETAIL AI ASSISTANT - EXAMPLE CONVERSATIONS ".center(78) + "█")
    print("█" + " Demonstrating RAG System Capabilities ".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    example_conversation_1()
    example_conversation_2()
    example_conversation_3()
    example_conversation_4()
    example_conversation_5()
    example_conversation_6()
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " END OF EXAMPLES ".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80 + "\n")


if __name__ == "__main__":
    run_all_examples()
