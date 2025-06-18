# SearchSim: A Unified Framework for Search Behavior Simulation

SearchSim is a modular, extensible framework for simulating search behaviors using different decision policies and environments. It enables researchers and developers to study search patterns, test UX designs, and evaluate search systems through agent-based simulation.

## 🌟 Key Features

- **Unified Architecture**: Single simulation runner with pluggable components
- **Multiple Decision Policies**: From simple component-based to sophisticated cognitive loops
- **Flexible Environments**: Mock, web browser, abstract search, and API environments
- **Rich Agent Memory**: Embedding-based memory with importance scoring
- **Persona-Driven**: Realistic user personas guide agent behavior
- **Extensible Design**: Easy to add new components and environments

## 🏗️ Architecture

SearchSim follows a **Unified Modularity** design with these core components:

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

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install searchsim

# With web browser support
pip install searchsim[web]

# With LLM support
pip install searchsim[llm]

# Full installation
pip install searchsim[all]
```

### Environment Setup

SearchSim requires API keys for LLM providers and supports various environment variables:

#### 🔧 Quick Setup
```bash
# Create environment template
searchsim setup-env

# Edit .env file with your actual keys
nano .env
```

#### 🔑 Required API Keys
- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **AWS Bedrock** (optional): Configure [AWS credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

#### 📝 Environment Variables
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

#### 🌐 Browser Setup
For web browser simulations, ensure Chrome is installed:
- **macOS**: `brew install google-chrome`
- **Ubuntu**: `sudo apt install google-chrome-stable`
- **Windows**: Download from [Google Chrome](https://www.google.com/chrome/)

### Basic Usage

1. **Create a persona**:
```bash
searchsim create-persona --name "Sarah" --intent "buy wireless headphones" --age 28
```

2. **Run a mock simulation** (fast, no API keys needed):
```bash
searchsim run -p sarah_persona.json --policy component --environment mock
```

3. **Run a web browser simulation** (requires API key):
```bash
# Set up environment variables first
export OPENAI_API_KEY="sk-proj-your-actual-key"
export HEADLESS=false  # Show browser GUI

# Run with cognitive loop policy
searchsim run -p sarah_persona.json --policy cognitive_loop --environment web_browser
```

4. **View results**:
```bash
ls output/
# simulation_results.json, agent_memory.json, step_trace.json
```

### Python API

```python
import asyncio
from searchsim import SimulationConfig, run_simulation

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

## 📋 Example Scenarios

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

## 🧠 Decision Policies

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

## 🎭 Personas

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

## 🔧 Configuration

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

## 📊 Output and Analysis

SearchSim generates comprehensive results:

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

## 🛠️ Development

### Project Structure
```
searchsim/
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
from searchsim.simulators.components.query_generators import BaseQueryGenerator

class MyQueryGenerator(BaseQueryGenerator):
    async def generate_query(self, context):
        # Your implementation
        return query
```

2. **New Environment**:
```python
from searchsim.environments.base_env import BaseEnvironment

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
pytest --cov=searchsim

# Test specific component
pytest tests/test_agent.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

SearchSim builds upon research in:
- Agent-based modeling
- Search behavior analysis
- Cognitive architectures
- Web automation

Special thanks to the UXAgent project for inspiration and foundational concepts.

## 📚 Citation

If you use SearchSim in your research, please cite:

```bibtex
@software{searchsim2024,
  title={SearchSim: A Unified Framework for Search Behavior Simulation},
  author={SearchSim Team},
  year={2024},
  url={https://github.com/searchsim/searchsim}
}
``` 