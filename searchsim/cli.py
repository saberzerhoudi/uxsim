import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

import click

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed

from .core.types import SimulationConfig, Persona
from .simulation import Simulation
from .llm import set_provider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """SearchSim: Advanced Search Simulation Framework
    
    Get started:
    1. searchsim setup-env    # Create .env file
    2. searchsim examples     # See usage examples  
    3. searchsim run -p persona.json  # Run simulation
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option('--persona', '-p', required=True, help='Path to persona JSON file')
@click.option('--output', '-o', default='output', help='Output directory')
@click.option('--policy', default='agent', 
              type=click.Choice(['component', 'cognitive_loop', 'agent']),
              help='Decision policy to use (agent = full UXAgent-style cognitive loop)')
@click.option('--environment', default='web_browser',
              type=click.Choice(['mock', 'web_browser']),
              help='Environment type')
@click.option('--max-steps', default=50, help='Maximum simulation steps')
@click.option('--llm-provider', default='openai',
              type=click.Choice(['openai', 'aws']),
              help='LLM provider')
@click.option('--headless/--no-headless', default=None,
              help='Run browser in headless mode (web_browser env only). Uses HEADLESS env var if not specified.')
@click.option('--start-url', default='https://www.amazon.com',
              help='Starting URL for web browser environment')
@click.option('--record', is_flag=True, help='Record the browser session (experimental)')
@click.option('--cookie', nargs=2, help='Set cookie as name value pair')
def run(persona, output, policy, environment, max_steps, llm_provider, headless, start_url, record, cookie):
    """Run a simulation with specified parameters"""
    
    async def _run():
        try:
            # Set up LLM provider
            set_provider(llm_provider)
            
            # Create environment config
            env_config = {}
            if environment == 'web_browser':
                # Determine headless setting: CLI flag -> env var -> default False (GUI mode like UXAgent)
                if headless is None:
                    # Default to GUI mode like UXAgent unless explicitly set to headless
                    headless_setting = os.getenv("HEADLESS", "false").lower() == "true"
                else:
                    headless_setting = headless
                
                env_config = {
                    'headless': headless_setting,
                    'start_url': start_url,
                    'max_wait_time': 10,
                    'record': record
                }
                
                # Add cookie if provided
                if cookie:
                    env_config['cookie'] = {'name': cookie[0], 'value': cookie[1]}
                
                click.echo(f"🌐 Browser mode: {'Headless' if headless_setting else 'GUI'}")
                click.echo(f"🔗 Starting URL: {start_url}")
            
            # Policy configuration
            policy_config = {}
            if policy == 'agent':
                # UXAgent-style full cognitive agent
                policy_config = {
                    'save_traces': True,
                    'save_agent_state': True,
                    'enable_reflection': True,
                    'enable_memory_update': True
                }
                click.echo(f"🧠 Using full cognitive agent policy (UXAgent-style)")
            elif policy == 'cognitive_loop':
                policy_config = {
                    'save_traces': True
                }
                click.echo(f"🔄 Using cognitive loop policy")
            else:
                click.echo(f"⚡ Using component policy")
            
            # Create simulation config
            config = SimulationConfig(
                max_steps=max_steps,
                environment_type=environment,
                environment_config=env_config,
                policy_type=policy,
                policy_config=policy_config,
                llm_provider=llm_provider,
                output_dir=output,
                save_traces=True
            )
            
            click.echo(f"🚀 Starting simulation:")
            click.echo(f"   • Policy: {policy}")
            click.echo(f"   • Environment: {environment}")
            click.echo(f"   • Max steps: {max_steps}")
            click.echo(f"   • LLM Provider: {llm_provider}")
            
            # Create and run simulation
            simulation = Simulation(config)
            results = await simulation.run(persona)
            
            click.echo(f"\n✅ Simulation completed!")
            click.echo(f"📊 Steps: {results['total_steps']}/{results['config']['max_steps']}")
            click.echo(f"⏱️  Duration: {results['duration_seconds']:.2f}s")
            click.echo(f"🎯 Success: {results['completed']}")
            click.echo(f"📁 Results saved to: {output}/")
            
            if results.get('agent_state', {}).get('memory_count', 0) > 0:
                click.echo(f"🧠 Memories created: {results['agent_state']['memory_count']}")
            
            # Show trace files created (UXAgent-style output)
            output_path = Path(output)
            if output_path.exists():
                trace_files = list(output_path.glob("*.json")) + list(output_path.glob("*.txt")) + list(output_path.glob("*.html"))
                if trace_files:
                    click.echo(f"📋 Trace files created:")
                    for f in sorted(trace_files)[:5]:  # Show first 5
                        click.echo(f"   • {f.name}")
                    if len(trace_files) > 5:
                        click.echo(f"   • ... and {len(trace_files) - 5} more files")
            
        except Exception as e:
            click.echo(f"❌ Simulation failed: {e}", err=True)
            import traceback
            traceback.print_exc()
            raise click.ClickException(str(e))
    
    asyncio.run(_run())


@cli.command()
@click.option('--config', '-c', required=True, help='Path to batch configuration YAML file')
def batch(config):
    """Run batch simulations from configuration file"""
    
    async def _batch():
        try:
            import yaml
            
            with open(config, 'r') as f:
                batch_config = yaml.safe_load(f)
            
            personas = batch_config.get('personas', [])
            base_config = batch_config.get('simulation_config', {})
            
            click.echo(f"🚀 Starting batch simulation with {len(personas)} personas")
            
            results = []
            for i, persona_path in enumerate(personas, 1):
                click.echo(f"\n--- Running simulation {i}/{len(personas)} ---")
                click.echo(f"Persona: {persona_path}")
                
                # Create config for this run
                config = SimulationConfig.from_dict({
                    **base_config,
                    'output_dir': f"{base_config.get('output_dir', 'output')}/sim_{i:03d}"
                })
                
                # Run simulation
                simulation = Simulation(config)
                result = await simulation.run(persona_path)
                results.append(result)
                
                click.echo(f"✅ Completed in {result['duration_seconds']:.2f}s")
            
            # Save batch results
            batch_output = Path(base_config.get('output_dir', 'output')) / 'batch_results.json'
            with open(batch_output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            click.echo(f"\n🎉 Batch simulation completed!")
            click.echo(f"📊 Total simulations: {len(results)}")
            click.echo(f"📁 Batch results saved to: {batch_output}")
            
        except Exception as e:
            click.echo(f"❌ Batch simulation failed: {e}", err=True)
            raise click.ClickException(str(e))
    
    asyncio.run(_batch())


@cli.command()
@click.option('--name', required=True, help='Persona name')
@click.option('--intent', required=True, help='What the persona wants to accomplish')
@click.option('--age', type=int, help='Age of the persona')
@click.option('--gender', help='Gender of the persona')
@click.option('--background', help='Background description')
@click.option('--output', '-o', help='Output file path (default: {name}_persona.json)')
def create_persona(name, intent, age, gender, background, output):
    """Create a new persona file"""
    try:
        # Generate background if not provided
        if not background:
            background = f"""Persona: {name}

Background:
{name} is a person interested in {intent}. They are looking to accomplish their goal efficiently and effectively.

Demographics:
Age: {age or 'Unknown'}
Gender: {gender or 'Unknown'}

Shopping Habits:
{name} prefers to research thoroughly before making decisions. They value quality and functionality over trends.

Professional Life:
{name} leads a busy life and appreciates tools and services that save time and provide value.

Personal Style:
{name} has a practical approach to life and prefers straightforward, honest interactions."""
        
        # Create persona data
        persona_data = {
            "name": name,
            "persona": background,
            "intent": intent,
            "age": age,
            "gender": gender
        }
        
        # Determine output file
        if not output:
            safe_name = name.lower().replace(' ', '_')
            output = f"{safe_name}_persona.json"
        
        # Save persona
        with open(output, 'w') as f:
            json.dump(persona_data, f, indent=2)
        
        click.echo(f"✅ Persona created: {output}")
        click.echo(f"👤 Name: {name}")
        click.echo(f"🎯 Intent: {intent}")
        
    except Exception as e:
        click.echo(f"❌ Failed to create persona: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--output', '-o', default='.env', help='Output file path (default: .env)')
@click.option('--force', is_flag=True, help='Overwrite existing file')
def setup_env(output, force):
    """Create a template .env file for environment variables"""
    try:
        env_path = Path(output)
        
        if env_path.exists() and not force:
            click.echo(f"❌ File {output} already exists. Use --force to overwrite.")
            return
        
        env_template = """# SearchSim Environment Variables
# Copy this file to .env and fill in your actual values

# Required: OpenAI API Key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional: Browser display mode (false = show browser GUI, true = headless)
HEADLESS=false

# Optional: AWS credentials (only needed if using AWS Bedrock)
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional: Other LLM providers
# ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Logging level
# LOG_LEVEL=INFO
"""
        
        with open(env_path, 'w') as f:
            f.write(env_template)
        
        click.echo(f"✅ Environment template created: {output}")
        click.echo(f"📝 Edit the file and add your actual API keys")
        click.echo(f"🔑 Get OpenAI API key: https://platform.openai.com/api-keys")
        
    except Exception as e:
        click.echo(f"❌ Failed to create environment file: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command()
def examples():
    """Show example commands and configurations"""
    click.echo("""
🚀 SearchSim Examples

=== QUICK SETUP ===

0. Create environment file:
   searchsim setup-env
   # Then edit .env file with your API keys

=== SETUP ===

1. Environment Variables (Recommended):
   Create a .env file in your project root:
   
   OPENAI_API_KEY=sk-your-actual-api-key-here
   HEADLESS=false
   AWS_ACCESS_KEY_ID=your-aws-key-if-using-aws
   AWS_SECRET_ACCESS_KEY=your-aws-secret-if-using-aws

   Or export them in your shell:
   export OPENAI_API_KEY="sk-your-actual-api-key-here"
   export HEADLESS=false

=== BASIC USAGE ===

1. Mock environment simulation:
   searchsim run -p persona.json --policy cognitive_loop --environment mock

2. Web browser simulation (with GUI):
   export HEADLESS=false
   searchsim run -p persona.json --policy cognitive_loop --environment web_browser

3. Web browser simulation (headless):
   searchsim run -p persona.json --environment web_browser --start-url https://amazon.com

4. Component-based simulation:
   searchsim run -p persona.json --policy component --environment mock --max-steps 30

=== PERSONA CREATION ===

5. Create a persona:
   searchsim create-persona --name "Alex" --intent "buy wireless headphones" --age 28 --gender "male"

=== BATCH PROCESSING ===

6. Batch simulation:
   searchsim batch -c batch_config.yaml

Example batch_config.yaml:
---
personas:
  - personas/persona1.json
  - personas/persona2.json
simulation_config:
  max_steps: 50
  environment_type: web_browser
  policy_type: cognitive_loop
  llm_provider: openai
  output_dir: batch_output
  environment_config:
    headless: false
    start_url: "https://www.google.com"

=== EXAMPLE FILES ===

Example persona.json:
{
  "name": "Sarah",
  "persona": "Persona: Sarah\\n\\nBackground:\\nSarah is a 32-year-old software engineer...",
  "intent": "find a good laptop for programming",
  "age": 32,
  "gender": "female"
}

Example .env file:
OPENAI_API_KEY=sk-proj-your-actual-key-here
HEADLESS=false
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key

=== MIGRATION FROM UXAGENT ===

UXAgent command:
python3 -m simulated_web_agent.main --persona "persona.json" --output "output" --llm-provider openai

Equivalent SearchSim command:
searchsim run -p persona.json -o output --policy cognitive_loop --environment web_browser --llm-provider openai

=== TROUBLESHOOTING ===

• If you see "Missing OpenAI API key", set OPENAI_API_KEY environment variable
• If browser doesn't show, set HEADLESS=false in environment or use --no-headless flag
• For AWS Bedrock, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
• Use --verbose flag for detailed logging
""")


@cli.command()
@click.option('--persona', '-p', help='Path to persona file to validate')
@click.option('--config', '-c', help='Path to config file to validate')
def validate(persona, config):
    """Validate persona or configuration files"""
    try:
        if persona:
            with open(persona, 'r') as f:
                persona_data = json.load(f)
            
            # Validate persona
            required_fields = ['intent']
            missing_fields = [field for field in required_fields if field not in persona_data]
            
            if missing_fields:
                click.echo(f"❌ Missing required fields: {missing_fields}", err=True)
                return
            
            # Try to create Persona object
            persona_obj = Persona.from_dict(persona_data)
            click.echo(f"✅ Persona valid: {persona_obj.name}")
            click.echo(f"🎯 Intent: {persona_obj.intent}")
        
        if config:
            import yaml
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Validate config structure
            required_sections = ['simulation_config']
            missing_sections = [section for section in required_sections if section not in config_data]
            
            if missing_sections:
                click.echo(f"❌ Missing required sections: {missing_sections}", err=True)
                return
            
            click.echo(f"✅ Configuration valid")
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        raise click.ClickException(str(e))


if __name__ == '__main__':
    cli() 