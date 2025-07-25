# UXSim: Towards a Hybrid User Search Simulation

![UXSim Workflow](figure/uxsim_workflow.png)

> **Notice (Coming Soon)**  
> The UXSim web interface will be available on **27 July**. It will support experiment execution, analysis, and the ability to share simulation runs without exposing sensitive training data.  
> The repository is currently undergoing refactoring to simplify usage based on early public feedback.

## Abstract

Simulating nuanced user experiences within complex interactive search systems poses distinct challenge for traditional methodologies, which often rely on static user proxies or, more recently, on standalone large language model (LLM) agents that may lack deep, verifiable grounding. The true dynamism and personalization inherent in human-computer interaction demand a more integrated approach. This work introduces **UXSim**, a novel framework that integrates both approaches. It leverages grounded data from traditional simulators to inform and constrain the reasoning of an adaptive LLM agent. This synthesis enables more accurate and dynamic simulations of user behavior while also providing a pathway for the explainable validation of the underlying cognitive processes.

## Key Features

- **Unified Architecture**: Single simulation runner with pluggable components
- **Multiple Decision Policies**: From simple component-based to sophisticated cognitive loops
- **Flexible Environments**: Mock, web browser, abstract search, and API environments
- **Rich Agent Memory**: Embedding-based memory with importance scoring
- **Persona-Driven**: Realistic user personas guide agent behavior
- **Extensible Design**: Easy to add new components and environments

## Architecture

UXSim follows a **Unified Modularity** design with these core components:

### 1. Central Simulation Runner
- **`simulation.py`**: Manages the main agent-environment interaction loop
- Simple, consistent interface regardless of underlying complexity

### 2. Agent System
- **`agent.py`**: Central agent with persona, memory, and cognitive state
- **Decision Policies**: Pluggable strategies for action selection
  - `ComponentPolicy`: Classic simulation using individual components
  - `CognitiveLoopPolicy`: Full Perceive-Plan-Reflect-Act cognitive cycle

### 3. Simulator Components
- **Query Generators**: Create search queries from persona intent
- **Action Selectors**: Choose actions from available page elements
- **Relevance Classifiers**: Determine content relevance to user goals

### 4. Environments
- **Mock Environment**: Fast, deterministic testing environment
- **Web Browser Environment**: High-fidelity browser automation (Playwright/Selenium)
- **Abstract Search Environment**: Internal search indices (Whoosh)
- **API Environment**: External search engine APIs

## Quick Start

### Installation

```bash
# Basic installation
pip install uxsim

# With web browser support
pip install uxsim[web]

# With LLM support
pip install uxsim[llm]

# Full installation
pip install uxsim[all]
```

### Environment Setup

UXSim requires API keys for LLM providers and supports various environment variables:

#### Quick Setup
```bash
uxsim setup-env

# Edit .env file with your actual keys
nano .env
```

#### Required API Keys
- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **AWS Bedrock** (optional): Configure [AWS credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

#### Environment Variables
Create a `.env` file in your project root:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional: Browser display mode (false = show browser GUI)
HEADLESS=false

# Optional: AWS credentials (for AWS Bedrock)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
```

Or export them in your shell:
```bash
export OPENAI_API_KEY="sk-proj-your-actual-key-here"
export HEADLESS=false
```

#### Browser Setup
For web browser simulations, ensure Chrome is installed:
- **macOS**: `brew install google-chrome`
- **Ubuntu**: `sudo apt install google-chrome-stable`
- **Windows**: Download from [Google Chrome](https://www.google.com/chrome/)

### Basic Usage

1. **Create a persona**:
```bash
uxsim create-persona --name "Sarah" --intent "buy wireless headphones" --age 28
```

2. **Run a mock simulation** (fast, no API keys needed):
```bash
uxsim run -p sarah_persona.json --policy component --environment mock
```

3. **Run a web browser simulation** (requires API key):
```bash
# Set up environment variables first
export OPENAI_API_KEY="sk-proj-your-actual-key"
export HEADLESS=false  # Show browser GUI

# Run with cognitive loop policy
uxsim run -p sarah_persona.json --policy cognitive_loop --environment web_browser
```

4. **View results**:
```bash
ls output/
# simulation_results.json, agent_memory.json, step_trace.json
```

### Python API

```python
import asyncio
from uxsim import SimulationConfig, run_simulation

# Configure simulation
config = SimulationConfig(
    persona_path="persona.json",
    environment_config={"type": "mock"},
    agent_policy="component",
    max_steps=20,
    output_dir="results"
)

# Run simulation
results = asyncio.run(run_simulation(config))
print(f"Completed in {results['execution']['steps_taken']} steps")
```

## Example Scenarios

### Scenario A: Classic, Fast Simulation
```yaml
# exp_classic_trec.yml
agent_policy: "component"
environment:
  type: "abstract_search"
  index_path: "trec_index"
max_steps: 10
```

**Workflow**: Agent uses `TrecQueryGenerator` → `AbstractSearchEnv` processes with Whoosh → Fast, reproducible results

### Scenario B: High-Fidelity Agent Emulation
```yaml
# exp_agent_google.yml
agent_policy: "cognitive_loop"
environment:
  type: "web_browser"
  start_url: "https://www.google.com"
  headless: false
max_steps: 50
```

**Workflow**: Agent uses full cognitive cycle → `WebBrowserEnv` controls real browser → Realistic user simulation

## Decision Policies

### Component Policy
Chains individual components for classic simulation:
- **Query Generator** → **Action Selector** → **Relevance Classifier**
- Fast, deterministic, scalable
- Perfect for batch experiments

### Cognitive Loop Policy
Implements full cognitive cycle:
1. **Perceive**: Extract meaningful insights from observations
2. **Plan**: Generate/update plans based on current situation
3. **Reflect**: Analyze past actions and generate insights
4. **Act**: Select concrete actions based on plans

## Personas

Personas drive agent behavior with rich characteristics:

```json
{
  "persona": "Persona: Sarah\n\nBackground:\nTech-savvy marketing professional...",
  "intent": "buy wireless headphones for work calls",
  "age": 28,
  "gender": "female",
  "demographics": {...},
  "shopping_habits": "Research-oriented, values quality...",
  "professional_life": "Marketing manager at tech startup...",
  "personal_style": "Minimalist, functional preferences..."
}
```

## Configuration

### YAML Configuration
```yaml
name: "My Simulation"
agent_policy: "cognitive_loop"
environment:
  type: "web_browser"
  start_url: "https://example.com"
  headless: true
max_steps: 30
output_dir: "results"
```

### Batch Simulations
```json
{
  "personas": ["persona1.json", "persona2.json"],
  "simulation_config": {
    "agent_policy": "component",
    "environment_config": {"type": "mock"},
    "max_steps": 20
  }
}
```

## Output and Analysis

UXSim generates comprehensive results:

```json
{
  "persona": {
    "name": "Sarah",
    "intent": "buy wireless headphones",
    "demographics": {...}
  },
  "execution": {
    "steps_taken": 15,
    "duration_seconds": 45.2,
    "completed": true
  },
  "agent_stats": {
    "total_memories": 28,
    "by_kind": {"observation": 10, "action": 8, "thought": 10},
    "api_calls": 15
  },
  "final_observation": {
    "url": "https://store.com/headphones",
    "has_content": true
  }
}
```

## Development

### Project Structure
```
uxsim/
├── core/                    # Core types and exceptions
├── agent.py                 # Central agent implementation
├── simulation.py            # Main simulation runner
├── simulators/              # Decision-making components
│   ├── policies/           # High-level decision policies
│   ├── components/         # Individual components
│   └── cognitive_loop/     # Cognitive cycle modules
├── environments/           # Environment implementations
├── personas/               # Persona management
├── configs/                # Example configurations
└── cli.py                  # Command-line interface
```

### Adding New Components

1. **New Query Generator**:
```python
from uxsim.simulators.components.query_generators import BaseQueryGenerator

class MyQueryGenerator(BaseQueryGenerator):
    async def generate_query(self, context):
        # Your implementation
        return query
```

2. **New Environment**:
```python
from uxsim.environments.base_env import BaseEnvironment

class MyEnvironment(BaseEnvironment):
    async def observe(self):
        # Return Observation
    
    async def step(self, action):
        # Execute action, return new Observation
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=uxsim

# Test specific component
pytest tests/test_agent.py
```
