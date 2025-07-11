#!/usr/bin/env python3
"""
Amazon Shopping Simulation
A complete implementation of the UXAgent Amazon use case using UXSim framework.

This script demonstrates:
1. UXAgent-compatible agent with full cognitive loop
2. Amazon-specific web parsing recipes
3. Real browser automation with Selenium
4. Comprehensive logging and tracing
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the UXSim package to the path
sys.path.insert(0, str(Path(__file__).parent))

from uxsim import Simulation
from uxsim.core.types import Persona, SimulationConfig
from uxsim.environments.web_browser_env import WebBrowserEnv
from uxsim.environments.recipes.amazon import AMAZON_RECIPES, get_amazon_config
from uxsim.policies.agent_policy import AgentPolicy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('amazon_simulation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_amazon_personas() -> Dict[str, Persona]:
    """Create Amazon-specific personas for testing"""
    return {
        "budget_shopper": Persona(
            name="Budget-Conscious Shopper",
            background="""You are Sarah, a 28-year-old graduate student living on a tight budget. You're very price-conscious 
            and always look for deals, discounts, and the best value for money. You read reviews carefully 
            before making any purchase and prefer products with good ratings and reasonable prices.""",
            intent="Find a good quality wireless bluetooth headphones under $50 with good reviews",
            age=28,
            gender="female",
            income=[20000, 30000]
        ),
        
        "tech_enthusiast": Persona(
            name="Tech Enthusiast", 
            background="""You are Alex, a 35-year-old software engineer who loves the latest technology. You're willing 
            to pay premium prices for cutting-edge features and high-quality products. You research 
            specifications thoroughly and prefer products from well-known brands.""",
            intent="Find the latest high-end gaming laptop with RTX 4080 or better graphics card",
            age=35,
            gender="male",
            income=[80000, 120000]
        ),
        
        "parent_shopper": Persona(
            name="Parent Shopper",
            background="""You are Maria, a 42-year-old mother of two teenagers. You're looking for practical, 
            safe, and durable products for your family. You value convenience, fast shipping, 
            and products that offer good value for families.""",
            intent="Find educational books and supplies for high school students, preferably with Prime shipping",
            age=42,
            gender="female", 
            income=[50000, 70000]
        )
    }


async def run_amazon_simulation(persona_name: str = "budget_shopper", headless: bool = False):
    """Run a complete Amazon shopping simulation"""
    
    logger.info(f"Starting Amazon simulation with persona: {persona_name}")
    
    # Create personas
    personas = create_amazon_personas()
    if persona_name not in personas:
        raise ValueError(f"Unknown persona: {persona_name}. Available: {list(personas.keys())}")
    
    persona = personas[persona_name]
    
    # Get Amazon configuration
    amazon_config = get_amazon_config()
    amazon_config["headless"] = headless
    amazon_config["recipes"] = AMAZON_RECIPES
    
    # Create simulation configuration
    sim_config = SimulationConfig(
        max_steps=50,
        environment_type="web_browser",
        environment_config=amazon_config,
        policy_type="agent",
        policy_config={
            "save_traces": True,
            "save_agent_state": True,
            "enable_reflection": True,
            "enable_memory_update": True
        },
        llm_provider="openai",
        output_dir=f"runs/amazon_{persona_name}",
        save_traces=True
    )
    
    # Create and run simulation
    simulation = Simulation(sim_config)
    
    try:
        logger.info("Initializing simulation...")
        await simulation.initialize()
        
        logger.info(f"Running simulation with {persona.name}")
        logger.info(f"Intent: {persona.intent}")
        
        results = await simulation.run_with_persona(persona)
        
        logger.info("Simulation completed successfully!")
        logger.info(f"Total steps: {results.get('total_steps', 0)}")
        logger.info(f"Final status: {results.get('status', 'unknown')}")
        
        # Print summary
        print("\n" + "="*60)
        print("AMAZON SIMULATION SUMMARY")
        print("="*60)
        print(f"Persona: {persona.name}")
        print(f"Intent: {persona.intent}")
        print(f"Total Steps: {results.get('total_steps', 0)}")
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Output Directory: {sim_config.output_dir}")
        print("="*60)
        
        return results
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise
    finally:
        await simulation.cleanup()


async def run_all_personas(headless: bool = False):
    """Run simulations for all personas"""
    personas = create_amazon_personas()
    results = {}
    
    for persona_name in personas.keys():
        logger.info(f"\n{'='*60}")
        logger.info(f"Running simulation for {persona_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = await run_amazon_simulation(persona_name, headless)
            results[persona_name] = result
        except Exception as e:
            logger.error(f"Failed to run simulation for {persona_name}: {e}")
            results[persona_name] = {"error": str(e)}
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Amazon shopping simulation")
    parser.add_argument(
        "--persona", 
        choices=["budget_shopper", "tech_enthusiast", "parent_shopper", "all"],
        default="budget_shopper",
        help="Persona to use for simulation"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure output directories exist
    Path("runs").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    try:
        if args.persona == "all":
            results = asyncio.run(run_all_personas(args.headless))
            print("\n" + "="*60)
            print("ALL SIMULATIONS SUMMARY")
            print("="*60)
            for persona, result in results.items():
                if "error" in result:
                    print(f"{persona}: FAILED - {result['error']}")
                else:
                    print(f"{persona}: SUCCESS - {result.get('total_steps', 0)} steps")
            print("="*60)
        else:
            asyncio.run(run_amazon_simulation(args.persona, args.headless))
            
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 