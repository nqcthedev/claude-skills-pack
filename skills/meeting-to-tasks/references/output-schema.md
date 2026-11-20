# Output schema and tracker formats

## tasks.json

```json
{
  "meeting": {
    "title": "Weekly product sync",
    "date": "2026-11-16",
    "attendees": [
      { "name": "Linh Pham", "email": "linh@example.com", "role": "PM" }
    ],
    "source": "transcript"
  },
  "summary": "One paragraph, plain language.",
  "decisions": [
    { "id": "D1", "decision": "Launch the beta on 1 Dec to existing customers only.", "rationale": "Support capacity.", "source_quote": "let's keep the beta to existing customers" }
  ],
  "action_items": [
    {
      "id": "A1",
      "title": "Draft beta invitation email",
      "description": "Why and acceptance notes.",
      "owner": "Linh Pham",
      "due_date": "2026-11-20",
      "due_basis": "explicit",
      "priority": "high",
      "status": "todo",
      "depends_on": [],
      "labels": ["beta"],
      "source_quote": "Linh, can you draft the invite by Thursday? - Sure."
    }
  ],
  "open_questions": [
    { "id": "Q1", "question": "Who approves the pricing page copy?", "owner": "Unassigned" }
  ]
}
```

### Field rules

| Field | Rule |
|---|---|
| `meeting.date` | Required, `YYYY-MM-DD`. Due dates are resolved against it. |
| `meeting.attendees[].name` | Required. `email` is optional but needed for Asana/Jira assignee matching. |
| `meeting.source` | `transcript`, `notes` or `chat`. |
| ids | `D1, D2...`, `A1, A2...`, `Q1, Q2...`; unique within the file. |
| `action_items[].title` | Required, 3-80 characters, starts with a verb. |
| `owner` | An attendee name, or `"Unassigned"`. |
| `due_date` | `YYYY-MM-DD` or `null`. Must not be before the meeting date. |
| `due_basis` | `explicit`, `inferred` or `none`. `none` requires `due_date: null`. |
| `priority` | `high`, `medium` or `low`. |
| `status` | `todo` (default), `in_progress` or `done`. |
| `depends_on` | Array of existing action item ids, no self-reference. |
| `source_quote` | Required for decisions and action items. Verbatim, shortest proving span. |

## Export formats

`python scripts/tasks_tool.py export tasks.json --format <format> -o out.csv`

| Format | Columns | Import notes |
|---|---|---|
| `jira` | Summary, Description, Issue Type, Priority, Assignee, Due Date, Labels (repeated) | Jira CSV importer: map columns in the wizard; set the date format to `yyyy-MM-dd`. Priority maps high/medium/low to High/Medium/Low. Assignee uses the attendee email when present, otherwise the name. Each label gets its own `Labels` column (Jira maps repeated columns to a multi-value field); spaces inside a label become hyphens. |
| `asana` | Name, Description, Assignee, Due Date, Priority, Section | Asana CSV import: assignee must be an email of a workspace member; due date is written as `MM/DD/YYYY`. Priority becomes a custom field you can map or skip. Section groups by priority. |
| `notion` | Name, Assignee, Due, Priority, Status, Depends on, Source | Notion "Import CSV" creates a database; change Due to a Date property and Priority/Status to Select after import. |
| `generic` | id, title, owner, owner_email, due_date, due_basis, priority, status, depends_on, labels, description, source_quote | Lossless; good for spreadsheets. |

Descriptions in every export include the evidence quote and the meeting title and date, so the ticket makes sense without the recap.
