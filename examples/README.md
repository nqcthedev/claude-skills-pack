# Examples

Real inputs and the outputs produced by following each skill's `SKILL.md`, including the helper scripts' actual output. All people, businesses and websites are fictional.

| Skill | Input | Output | Scripts run |
|---|---|---|---|
| [client-proposal](client-proposal) | Client email brief | Proposal with 3 priced options, cover email, internal open questions | - (table sums verified) |
| [meeting-to-tasks](meeting-to-tasks) | 11-minute kickoff call transcript | Recap, `tasks.json`, Jira/Asana/Notion/generic CSV | `tasks_tool.py validate --transcript` and `export` |
| [code-review-checklist](code-review-checklist) | Base Flask app + PR patch | `REVIEW.md` with 13 findings and checklist coverage | `gather_diff.py` (via `reproduce.sh`) |
| [brand-voice-writer](brand-voice-writer) | Voice guide + launch brief | LinkedIn post, Instagram caption, email, voice check | `check_draft.py` (first run failed 2 drafts; revised) |
| [seo-page-brief](seo-page-brief) | Keyword + 3 competitor pages + our page | Content brief with outline, gaps, schema, research log | 12 web-insights MCP tool calls (`research/collect.py`) |

The stories connect: Northbeam Studio proposes a booking assistant to BrightSmile Dental, then runs the kickoff call, then reviews a pull request from the project. Lumen Coffee Co. is the brand for the voice and SEO examples.

Reproduce the script outputs:

```bash
python3 skills/meeting-to-tasks/scripts/tasks_tool.py validate examples/meeting-to-tasks/output/tasks.json \
  --transcript examples/meeting-to-tasks/input/transcript.txt
bash examples/code-review-checklist/reproduce.sh
python3 skills/brand-voice-writer/scripts/check_draft.py --guide examples/brand-voice-writer/input/voice-guide.md \
  --channel email examples/brand-voice-writer/output/email.md
WEB_INSIGHTS_CLI=/path/to/web-insights-mcp/dist/cli.js python3 examples/seo-page-brief/research/collect.py
```
