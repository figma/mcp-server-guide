# Scorecard

Use this scorecard for each eval task. Score 0-2 for every category.

| Category | 0 | 1 | 2 |
|---|---|---|---|
| Setup clarity | User cannot complete setup | Setup works with extra clarification | Setup is copy-pasteable and complete |
| Tool selection | Wrong or missing MCP tools | Correct tools after recovery | Correct tools selected immediately |
| Figma targeting | Wrong file, page, or node | Correct target after user correction | Correct file, page, and node first try |
| Token/component fidelity | Invents tokens/components | Mixes real and invented system details | Uses real Figma/codebase context |
| Error recovery | Stalls or repeats failures | Explains blocker but needs help | Recovers or gives exact next step |
| Validation | No verification | Text-only verification | Screenshot, structural readback, or clear artifact URL |
| User clarity | Jargon-heavy or vague | Understandable but incomplete | Designer-friendly and actionable |

## Result Template

```markdown
## Eval Result

- Task:
- Date:
- Agent client/build version:
- Figma account plan/seat:
- Figma file URL:
- Prompt used:
- Final artifact URL or screenshot:
- Setup clarity:
- Tool selection:
- Figma targeting:
- Token/component fidelity:
- Error recovery:
- Validation:
- User clarity:
- Total:
- Notes:
- Access blockers:
```

## Interpreting Scores

- `12-14`: strong
- `9-11`: usable but needs tightening
- `5-8`: unreliable
- `0-4`: failing

If a task is blocked because the account lacks access, write `blocked-by-access` in the notes and score only the categories that can be observed.
