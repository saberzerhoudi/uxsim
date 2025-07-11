#!/usr/bin/env python3
"""
Practical UXSim Examples for Real-World Scenarios
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from uxsim import Simulation
from uxsim.core.types import Persona, SimulationConfig
from uxsim.environments.recipes.amazon import AMAZON_RECIPES, get_amazon_config


# Example 1: Market Research
async def market_research_simulation():
    """Use UXSim to research product markets and pricing"""
    
    researcher = Persona(
        name="Market Researcher",
        background="""You are a professional market researcher analyzing the laptop market. 
        You need to gather comprehensive data on product features, pricing, customer reviews, 
        and market positioning for different laptop brands and models.""",
        intent="Research the gaming laptop market: compare prices, features, and reviews for RTX 4070+ laptops",
        age=35,
        demographics={"role": "researcher", "focus": "market_analysis"}
    )
    
    config = SimulationConfig(
        max_steps=40,
        environment_type="web_browser",
        environment_config={
            **get_amazon_config(),
            "headless": True,
            "recipes": AMAZON_RECIPES
        },
        policy_type="agent",
        policy_config={
            "save_traces": True,
            "enable_reflection": True,  # Important for analysis
            "save_agent_state": True
        },
        output_dir="runs/market_research"
    )
    
    simulation = Simulation(config)
    
    try:
        print("📊 Market Research Simulation Starting...")
        await simulation.initialize()
        results = await simulation.run_with_persona(researcher)
        
        # The agent's memory will contain market insights
        print("📈 Research completed! Check the output directory for detailed findings.")
        return results
    finally:
        await simulation.cleanup()


# Example 2: Price Comparison
async def price_comparison_simulation():
    """Use UXSim for automated price comparison"""
    
    bargain_hunter = Persona(
        name="Smart Shopper",
        background="""You are an experienced online shopper who always finds the best deals. 
        You systematically compare prices, check reviews, look for discounts, and evaluate 
        value propositions before making purchase decisions.""",
        intent="Find the best price for Apple AirPods Pro, compare different sellers and deals",
        demographics={"shopping_style": "price_conscious", "experience": "expert"}
    )
    
    config = SimulationConfig(
        max_steps=25,
        environment_type="web_browser",
        environment_config={
            **get_amazon_config(),
            "headless": True
        },
        policy_type="agent",
        output_dir="runs/price_comparison"
    )
    
    simulation = Simulation(config)
    
    try:
        print("💰 Price Comparison Simulation Starting...")
        await simulation.initialize()
        results = await simulation.run_with_persona(bargain_hunter)
        print("💸 Best deals identified! Check logs for price analysis.")
        return results
    finally:
        await simulation.cleanup()


# Example 3: User Experience Testing
async def ux_testing_simulation():
    """Use UXSim to test user experience flows"""
    
    # Simulate a user with accessibility needs
    accessibility_user = Persona(
        name="Accessibility-Focused User",
        background="""You are a user who relies on screen readers and keyboard navigation. 
        You need websites to be accessible, with clear navigation, good contrast, 
        and proper labeling of interface elements.""",
        intent="Navigate Amazon to find and purchase large-print books, testing accessibility",
        demographics={"accessibility_needs": ["screen_reader", "high_contrast"]}
    )
    
    config = SimulationConfig(
        max_steps=20,
        environment_type="web_browser",
        environment_config={
            **get_amazon_config(),
            "headless": False,  # Visual testing
            "max_wait_time": 15  # Allow more time for accessibility
        },
        policy_type="agent",
        policy_config={
            "save_traces": True,
            "save_agent_state": True
        },
        output_dir="runs/ux_testing"
    )
    
    simulation = Simulation(config)
    
    try:
        print("♿ UX Accessibility Testing Starting...")
        await simulation.initialize()
        results = await simulation.run_with_persona(accessibility_user)
        print("✅ Accessibility test completed! Review logs for UX insights.")
        return results
    finally:
        await simulation.cleanup()


# Example 4: A/B Testing Different Personas
async def persona_comparison():
    """Compare how different personas behave in the same scenario"""
    
    personas = [
        Persona(
            name="Budget Student",
            background="College student on tight budget, very price-sensitive",
            intent="Find textbooks for computer science courses under $50 each"
        ),
        Persona(
            name="Working Professional", 
            background="Busy professional who values time over money",
            intent="Find computer science reference books, prioritizing quality and quick delivery"
        )
    ]
    
    results = {}
    
    for persona in personas:
        config = SimulationConfig(
            max_steps=20,
            environment_type="web_browser",
            environment_config={
                **get_amazon_config(),
                "headless": True
            },
            policy_type="agent",
            output_dir=f"runs/persona_test_{persona.name.lower().replace(' ', '_')}"
        )
        
        simulation = Simulation(config)
        
        try:
            print(f"👤 Testing {persona.name}...")
            await simulation.initialize()
            result = await simulation.run_with_persona(persona)
            results[persona.name] = result
        finally:
            await simulation.cleanup()
    
    print("\n📊 Persona Comparison Results:")
    for name, result in results.items():
        print(f"  {name}: {result.get('total_steps', 0)} steps")
    
    return results


def main():
    """Choose which example to run"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UXSim Real-World Examples")
    parser.add_argument(
        "--scenario",
        choices=["research", "price", "ux", "personas"],
        default="research",
        help="Which scenario to run"
    )
    
    args = parser.parse_args()
    
    scenarios = {
        "research": market_research_simulation,
        "price": price_comparison_simulation,
        "ux": ux_testing_simulation,
        "personas": persona_comparison
    }
    
    print(f"🚀 Running {args.scenario} scenario...")
    asyncio.run(scenarios[args.scenario]())


if __name__ == "__main__":
    main() 