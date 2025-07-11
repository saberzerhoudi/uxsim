#!/usr/bin/env python3
"""
Example: Using UXSim directly for custom Amazon shopping scenarios
"""

import asyncio
import sys
from pathlib import Path

# Add UXSim to path
sys.path.insert(0, str(Path(__file__).parent))

from uxsim import Simulation
from uxsim.core.types import Persona, SimulationConfig
from uxsim.environments.recipes.amazon import AMAZON_RECIPES, get_amazon_config


async def custom_amazon_simulation():
    """Example of using UXSim directly for a custom scenario"""
    
    # 1. Create a custom persona
    persona = Persona(
        name="Holiday Shopper",
        background="""You are Jessica, a 30-year-old marketing professional preparing for the holiday season. 
        You need to buy gifts for family members and are looking for items that are popular, well-reviewed, 
        and available for quick delivery. You have a moderate budget and prefer trusted brands.""",
        intent="Find popular holiday gifts under $100 each for family members, focusing on electronics and books",
        age=30,
        gender="female",
        income=[60000, 80000]
    )
    
    # 2. Configure the environment with Amazon recipes
    amazon_config = get_amazon_config()
    amazon_config["headless"] = True  # Run without browser window
    amazon_config["recipes"] = AMAZON_RECIPES
    
    # 3. Create simulation configuration
    config = SimulationConfig(
        max_steps=30,  # Limit to 30 steps for this example
        environment_type="web_browser",
        environment_config=amazon_config,
        policy_type="agent", 
        policy_config={
            "save_traces": True,
            "enable_reflection": True,
            "enable_memory_update": True
        },
        llm_provider="openai",
        output_dir="runs/custom_holiday_shopper",
        save_traces=True
    )
    
    # 4. Create and run simulation
    simulation = Simulation(config)
    
    try:
        print("🎄 Starting Holiday Shopping Simulation...")
        print(f"Persona: {persona.name}")
        print(f"Intent: {persona.intent}")
        
        # Initialize the simulation
        await simulation.initialize()
        
        # Run the simulation
        results = await simulation.run_with_persona(persona)
        
        print("\n🎉 Simulation completed!")
        print(f"Steps taken: {results.get('total_steps', 0)}")
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Output saved to: {config.output_dir}")
        
        return results
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        raise
    finally:
        await simulation.cleanup()


async def quick_product_search():
    """Example of a quick product search simulation"""
    
    # Simple persona for quick testing
    persona = Persona(
        name="Quick Shopper",
        background="A busy professional who needs to quickly find specific products",
        intent="Find wireless noise-canceling headphones with good reviews"
    )
    
    # Minimal configuration
    config = SimulationConfig(
        max_steps=15,
        environment_type="web_browser", 
        environment_config={
            "start_url": "https://www.amazon.com",
            "headless": True,
            "recipes": AMAZON_RECIPES
        },
        policy_type="agent",
        policy_config={"enable_reflection": False},  # Disable for speed
        output_dir="runs/quick_search"
    )
    
    simulation = Simulation(config)
    
    try:
        print("⚡ Quick product search...")
        await simulation.initialize()
        results = await simulation.run_with_persona(persona)
        print(f"✅ Found results in {results.get('total_steps', 0)} steps")
        return results
    finally:
        await simulation.cleanup()


def main():
    """Choose which example to run"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UXSim Usage Examples")
    parser.add_argument(
        "--example",
        choices=["custom", "quick"],
        default="custom",
        help="Which example to run"
    )
    
    args = parser.parse_args()
    
    if args.example == "custom":
        asyncio.run(custom_amazon_simulation())
    elif args.example == "quick":
        asyncio.run(quick_product_search())


if __name__ == "__main__":
    main() 