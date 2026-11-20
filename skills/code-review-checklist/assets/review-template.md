# Code review: {{branch or PR title}}

**Verdict: {{Request changes | Approve with comments | Approve}}**

{{2-3 sentences: what the change does, the overall assessment, and the most important thing to fix.}}

| | |
|---|---|
| Scope | {{n}} files, +{{additions}} / -{{deletions}}, {{n}} commits against `{{base}}` |
| Checklist | `{{checklist path}}` |
| Findings | {{n}} blocker · {{n}} major · {{n}} minor · {{n}} nit |

## Findings

### 1. [{{severity}}] {{short title}} - `{{path}}:{{line}}` ({{CHECK-ID}})

{{What is wrong.}} **Why it matters:** {{concrete consequence}}.

**Suggested fix:**

```{{language}}
{{code}}
```

## Checklist coverage

| Item | Status | Notes |
|---|---|---|
| {{SEC-1}} | {{pass / issue #n / n/a / not verifiable}} | {{short note}} |

## Automated risk flags

| Flag | Location | Outcome |
|---|---|---|
| {{flag}} | `{{path}}:{{line}}` | {{confirmed as #n / dismissed: reason}} |

## What's good

- {{specific positive point}}
