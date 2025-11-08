# c2c - Claude Code to Claude Code MCP server

> Self-organising agents, parallel agents tasks, recursive agents — all managed by the `c2c` MCP

## What is it?

`c2c` is a [FastMCP](https://getfastmcp.com) server that wraps Anthropic's [Claude Agent SDK] to give Claude Code — though, truly to any other agents too — the ability to spawn agents. Leveraging these models abilities to write plans, systems prompts, etc it's easy to see how a single Agent equipped with `c2c` can have many applications:

- Embarrasingly parallel tasks: If Claude Code suggests trying 3 options for a given problem, why not explore the 3 of them? In parallel? Asynchronously?
- Orthogonal tasks: Let's say you (or the agent) is working on well planned tasks that don't overlap with each other. No need to spawn several claude code sessions in different `tmux` sessions or terminal tabs. Let your main agent spawn these sessions for you, iterate with the sub-agents and report back to you once the work is ready.
- Self-organising agents: You can start with a mission and let agents go wild, letting them self-organise as they see fit. One entry point agent can spawn two agents, e.g. backend and frontend engineer, maybe a tech lead as well that coordinates them. Maybe each of the backend and front end engineers have lots of tasks and need more help, they can spawn more agents too as they see fit, let them decide!

## Installation

```
git clone https://github.com/lucharo/c2c
cd c2c
claude mcp add c2c -- uv run c2c
```

## Concepts

Conversations refer to the entire exchange of messages between agents, including the full conversation history. Conversations can be created, messaged, and ended.

## Tools

`c2c` exposes 4 core tools:

- `create_conversation(task_name, task_description)`: creates a new conversation and returns a `conversation_id`
- `send_message_and_receive_response(conversation_id, message)`: sends a message to a conversation and returns the agent's response
- `end_conversation(conversation_id)`: ends a conversation and cleans up resources
- `list_conversations()`: lists all active conversations with their status and message counts

## Authenticaton & environment variables

Whatever agent you spawn from within a Claude Code session will you use the authetication method set for the parent.

Claude Code seems to set up a few environment variables when it starts, among them:

```sh
CLAUDECODE=1
CLAUDE_CODE_ENTRYPOINT=cli
```

`claude-agent-sdk` can pick these up and use the Claude Code authentication mode (e.g. login via subscription) if `ANTHROPIC_API_KEY` is missing.

More over, if any environment variables are defined in `~/.claude/settings.json` such as:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<<ZAI_API_KEY>>",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.6",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.6"
  },
  "alwaysThinkingEnabled": true
}
```

for z.ai authentication, they will be picked up too.

## Development

`c2c_dev.py` is a completely vibecoded version that uses `c2c.conversation_storage.py` (also vibecoded) that seems to do the job, as it can spawn several sub-agents (all using main claude code) without blocking the main agent.

you can install the `c2c-dev` mcp by running:

```sh
claude mcp add c2c -- uv run c2c_dev.py
```

## Requirements/goals

- [ ] Claude Code can spawn other Claude Code subagents via `claude-agent-sdk`+ MCP
- [ ] agent parent-child conversations used same logging system as main claude code, i.e. `~/.claude/projects/...`
- [ ] lineage of sub agents is tracked (parent_id, depth...)
- [ ] subagents can spawn subagents
- [ ] UI to visualise graph of agents
- [ ] UI to jump into any conversation, if we can leverage `claude --resume session_id` better
- [ ] permission handling upon agent creation or mid-conversation
- [ ] model specification handling upon agent creation or mid-conversation
