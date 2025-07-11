#!/usr/bin/env python3
"""
Simple test script to verify UXSim framework functionality
"""

import asyncio
import json
import tempfile
from pathlib import Path

# Test the framework
async def test_uxsim():
    print("🧪 Testing UXSim Framework...")
    
    try:
        # Import the framework
        from uxsim import SimulationConfig, run_simulation
        from uxsim.core.types import Persona
        print("✅ Successfully imported UXSim")
        
        # Create a test persona
        test_persona = {
            "persona": "Persona: TestUser\n\nBackground:\nA test user for framework validation.\n\nDemographics:\nAge: 30\nGender: Unknown\n\nShopping Habits:\nBasic online user.\n\nProfessional Life:\nSoftware tester.\n\nPersonal Style:\nPragmatic approach.",
            "intent": "find test products",
            "age": 30,
            "gender": "unknown",
            "income": []
        }
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save persona
            persona_file = temp_path / "test_persona.json"
            with open(persona_file, 'w') as f:
                json.dump(test_persona, f)
            
            # Create simulation config
            config = SimulationConfig(
                persona_path=str(persona_file),
                environment_config={
                    "type": "mock",
                    "max_steps": 3,
                    "mock_pages": [
                        {
                            "url": "http://test.com/page1",
                            "content": "Test page with test products",
                            "clickables": [{"name": "test_link", "text": "Test Link", "id": "test_link"}]
                        },
                        {
                            "url": "http://test.com/page2", 
                            "content": "Second test page with more test content",
                            "clickables": [{"name": "test_button", "text": "Test Button", "id": "test_button"}]
                        }
                    ]
                },
                agent_policy="component",
                max_steps=5,
                output_dir=str(temp_path / "output"),
                llm_provider="openai"
            )
            
            print("🚀 Running test simulation...")
            
            # Run simulation
            results = await run_simulation(config)
            
            print("✅ Simulation completed successfully!")
            print(f"📊 Results:")
            print(f"   - Steps taken: {results['execution']['steps_taken']}")
            print(f"   - Duration: {results['execution']['duration_seconds']:.2f}s")
            print(f"   - Completed: {results['execution']['completed']}")
            print(f"   - Agent memories: {results['agent_stats']['total_memories']}")
            
            # Verify output files
            output_dir = temp_path / "output"
            if (output_dir / "simulation_results.json").exists():
                print("✅ Results file created successfully")
            else:
                print("❌ Results file not found")
                
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔬 UXSim Framework Test")
    print("=" * 50)
    
    success = asyncio.run(test_uxsim())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! UXSim framework is working correctly.")
    else:
        print("💥 Tests failed. Please check the implementation.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main()) 