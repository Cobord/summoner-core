# Agent SDK · Summoner Platform

<p align="center">
<img width="200px" src="img/92a3447d-6925-431e-a2d0-a1ee671cd9bd.png" />
</p>

> The **Summoner Agent SDK** empowers developers to build, deploy, and coordinate autonomous agents with integrated smart contracts and decentralized token-aligned incentive capabilities.

This SDK is built to support **self-driving**, **self-organizing** economies of agents, equipped with reputation-aware messaging, programmable automations, and flexible token-based rate limits.

## 📚 Documentation

Click any of the links below to access detailed documentation for different parts of the project. Each document contains focused guidance depending on what you want to work on or learn about.

- ✅ **[Installation Guide](docs/doc_installation.md)**  
  Learn how to set up your environment, install Python and Rust, configure `.env` variables, and run the `setup.sh` script to prepare your system for development.

- ✅ **[Creating an Agent](docs/doc_make_an_agent.md)**  
  Learn how to build and configure a custom agent using the SDK.  
  This guide walks you through setting up a basic agent, defining send and receive routes with decorators, and connecting to a server. It also includes a full example with two agents — a QuestionAgent and an AnswerBot — showing how to coordinate message passing and design conversational behaviors. You will also discover how to model agent workflows as state transitions using route paths.

- ✅ **[Contributing to the Rust Server Codebase](docs/doc_contribute_to_server.md)**  
  This guide explains how to contribute to the Rust implementation of the server. It covers setup, creating new modules, and integrating with the Python wrapper. Ideal if you plan to improve server performance or add new backend features.

- ✅ **[Development Guidelines](docs/doc_development.md)**  
  Learn the overall development practices and collaboration standards for the `Summoner-Network/agent-sdk` repository.  
  This guide covers coding conventions, pull request workflows, branch protection rules, and code scanning requirements. It explains how to work with the `dev` and `main` branches, how to pass reviews and security checks, and how to ensure that your contributions are clean, secure, and aligned with project quality standards.
