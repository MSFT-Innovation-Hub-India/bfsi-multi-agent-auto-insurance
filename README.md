# Vehicle Insurance Claims Processing System

AI-powered auto insurance claims processing system with multi-agent architecture built on Azure.

## 🎯 Features

- **Multi-Agent Architecture**: 5 specialized AI agents for policy lookup, coverage analysis, inspection, bill validation, and synthesis
- **Real-time Processing**: Streaming API with live updates
- **Memory Persistence**: Cosmos DB for context sharing between agents
- **Modern UI**: Next.js frontend with real-time visualization
- **Audit Trail**: Complete logging of all processing steps

## 🚀 Quick Start

See [SETUP.md](SETUP.md) for detailed setup instructions.

## 📁 Project Structure

```
├── api_server.py              # Batch processing API
├── api_server_realtime.py     # Real-time streaming API  
├── orchestrator.py            # Main orchestrator wrapper
├── config.py                  # Configuration management
├── tinsurance.py              # Document indexing script
├── orchestrator/              # Core orchestration logic
├── agents/                    # Standalone agent implementations
├── instructions/              # AI agent prompts
├── analyzer_templates/        # Azure AI analyzer configs
└── frontend/                  # Next.js application
```

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Azure OpenAI (GPT-4o)
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **Azure Services**: OpenAI, Cosmos DB, Blob Storage, AI Search

## 📄 License

MIT License - see [LICENSE](LICENSE) for details
