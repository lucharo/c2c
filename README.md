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

The following concepts are useful to understand how `c2c` works.

- Conversations: refer to the entire exchange of messages between two agents. This includes the conversation history. Conversations can be created and resumed.
- Sessions: are created from conversations, they can be started from a conversation, ended and messages can be sent to a session. Note, messages are not sent to a conversation, they are sent to a session which is itself "connected" to a conversation.

## Tools

`c2c` exposes 8 core tools:

- `create_conversation(task_name, task_description)`: this returns a `conversation_id` and generates some metadata to link the parent agent to the child agent
- `start_session(conversation_id)`: this returns a `session_id` that `send_message` and `end_session` can leverage and creates an agent client in the background.
- `create_conversation_and_start_session(task_name, task_description)`: combines `create_conversation` and `start_session`
- `send_message(session_id, "rewrite in rust following best practices")`: sends a message to an agent asynchronously for a given `session_id` and returns immediately. The agent processes the message in the background.
- `receive_response(session_id)`: waits for and collects the agent's response from a session. Use this after `send_message` to get what the agent said back.
- `end_session(session_id)`: disconnect agent, conversation history is maintained.
- `list_conversations()`: lists all conversations
- `list_sessions()`: lists all sessions

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
