---
name: figma-code-workflows
description: Use this skill to bring an existing local project, HTML file, or GitHub repo into Figma as code, or to pull GitHub updates into linked Figma code. It covers editable Design layers, runnable Code Layers, standalone Code/Make files, and fixing imported previews. Use it when the user says which Figma output they want, either by naming the type or by describing it. Wanting to run, click through, or interact with the imported app in Figma counts as asking for runnable code. Also use it when they give a Figma file link or key as the destination. Don't use it when the main goal is to publish or share to Figma Gallery; the gallery-sharing skill handles that. Also skip it for writing new code components, building local projects, or vague requests to "make a code project" that don't say where the code should go in Figma. In those cases, ask about the output first.
disable-model-invocation: false
---

# Import a project into Figma

Only use this workflow for an explicitly requested Figma output (standalone Code/Make, runnable Code Layer, or editable Design layers), or a Figma file key/link given as its destination. Generic “make a code project” or “create a code component” requests, and Figma Code/Make names alone, do not specify that output. If output intent is unclear, ask whether the user wants local code or a Figma output, then wait before starting this workflow.

Preserve the user's project. Use each tool's current description and schema for prerequisites and parameters.

If the request includes publishing to Gallery, load `share-to-figma-gallery` first. When the current tool schema offers upfront review, complete it before any import or sync; otherwise follow that skill’s legacy publishing flow.

Keep the user updated at the main stages: preparing and validating the project, uploading the archive, and completing the import in Figma. Report pending imports, recovery work and blockers as they occur; do not describe an unconfirmed stage as complete.

## 1. Choose the output and destination

Identify the user's intended output, then load the appropriate skill according to the table below. If the output is unclear, ask the user before proceeding.

| Input | User's requested output | Next action |
| --- | --- | --- |
| Running app or static HTML | Unspecified — just put/import it in Figma | Ask **"Editable design layers or a code layer?" and end your turn.** Wait for the answer. |
| Running app | Editable Design layers | Load `figma-generate-design`, then call `generate_figma_design` in a Design file. |
| Static HTML | Editable Design layers | Call `html_to_figma` in a Design file. |
| Running app | Runnable Code Layer or standalone Code/Make | Continue with this skill and call `send_code_to_figma`. |
| Static HTML | Runnable Code Layer or standalone Code/Make | Continue with this skill and call `send_code_to_figma`. |

An HTML project with working buttons is still ambiguous when the user has not chosen the output. A Design link only chooses the destination, not the output.

Before choosing a runnable destination, call `whoami`. Only choose or import a Design Code Layer when `whoami.code_layers_enabled` is true; otherwise use standalone Code/Make, or explain the limitation and ask before changing an explicitly supplied Design destination.

Honor an explicit code-layer or standalone request before applying the screen-count heuristic. For runnable code with a Design link, use a Code Layer. For a standalone Code link, use standalone. With no destination or explicit code-layer/standalone choice, estimate screens: fewer than 10 or unknown → Code Layer; 10 or more → standalone. Never ask Code Layer versus standalone or ask the user to count screens. Explicit destinations and links take precedence after the output choice.

Before creating a runnable destination, reuse the selected original source's `.figma/entity_refs.json` mapping when available, unless the user supplied another explicit destination. Match the correct project/loose-file source and retain its fileKey, componentGuid and canvas nodeId; ask if several destinations remain. The file is local memory, not proof of current Gallery state. A missing/stale artifact ID or a web-created target does not establish that it is unpublished. Do not require local metadata for an existing Figma target or a GitHub-only workflow.

Use the supplied file URL. If a new file is needed, use `create_new_file` with the selected destination type and the user's chosen plan.

Create a Design file for a requested code layer when no destination is provided.

Keep the confirmed output choice fixed; do not ask the user to choose again after creating the file.

For editable Design layers, follow the selected tool's instructions: `generate_figma_design` captures the running app's rendered page; `html_to_figma` converts a self-contained static HTML document. Inspect the resulting layers and share the Design link. Continue below only for runnable code output.

## Check Gallery before sending updates

Resolve the selected source/transport and finish the requested local app changes and known import/deploy files before generating review content. If the user explicitly requests code sync without Gallery work, honor that scope and skip the Gallery check and continuation. Otherwise, do the check below before any outgoing code push or sync.

For an existing runnable target whose owning plan has Gallery M2 enabled, when publish_to_gallery offers upfrontReview, call it with `action: "prepare"` and `upfrontReview: "if_published"` before any git push or GitHub sync. Use the exact file and Code Layer canvas nodeId; standalone Makes omit nodeId. This checks authoritative Gallery state without opting an unlinked import into Gallery. If the response returns an upfront review for an active Gallery target, load share-to-figma-gallery, generate the changelog from the known local changes, and finish its changelog approval before sending code. Explain that approval authorizes automatic publishing; honor an upfront draft request without asking a separate mode question. Assume the local code is what GitHub sync will deliver; no remote comparison is needed. Keep the approved galleryPublishStatusId within the Gallery workflow; never add Gallery-specific arguments to send_code_to_figma or its continuations. The backend can resolve an active approved preparation for an existing target. After code is saved, follow a returned Gallery continuation, or continue publish_to_gallery with the preparation ID retained by the Gallery workflow. No additional publishing approval follows successful preparation.

For not_in_gallery or ineligible/non-M2 targets, continue the normal import/sync workflow without Gallery publication or new preparation fields. Do not recreate deleted Gallery posts automatically. Honor refusal/cancellation before sending code. Existing connections that do not offer upfrontReview keep their current behavior. If upfront review is unavailable or its lookup fails, continue the requested import/sync under its existing permissions without new preparation inputs. Preserve explicit Gallery intent through the existing publish flow, but never infer Gallery intent for an unlinked sync. Do not turn a Gallery lookup failure into a failed import.

## Choose the source: GitHub, git or upload

`send_code_to_figma` can take code three ways, depending on which inputs its schema offers: `github` (Figma reads the repository and keeps the code linked for later pulls), `git` (you push a local project to a short-lived Figma remote), and `upload` (an archive of a local folder). For a local project, first run `git remote get-url origin` and `git status -sb` to tell which of two flows the user is in, and keep to that flow:

- **Working from GitHub**: the user gives a GitHub repository URL, asks to sync, pull, update or switch a Make or code layer from GitHub or a branch, or points at a local checkout whose `origin` is on GitHub with nothing uncommitted or unpushed. Use `github` (owner and name from the URL or `origin`), not `git`: only `github` keeps the code linked for later pulls. Before the first import from a local checkout, follow **First GitHub import from a local checkout** under GitHub below. If the checkout has uncommitted or unpushed changes, ask whether to import from GitHub, which keeps the code linked, or send the local copy, which keeps those changes, and send it with `git` when offered. If Figma cannot read the repository, see below.
- **Prototyping without GitHub**: the project has no GitHub remote, such as a prototype in a local folder. When `git` is offered, send it with `git`, even if the folder is not a git repository yet: run `git init`, then commit it. Also use `git` to update a Make or code layer you sent with git before. Do not upload instead, and do not ask the user to choose between git and upload. Do not mention GitHub, repositories or git details; tell the user you are sending their project to Figma. Only when the user wants to work on the code with others, share or back it up, or move it to GitHub, suggest connecting the Make to GitHub (https://help.figma.com/hc/en-us/articles/44220165255063). Do not create a GitHub repository or push to GitHub yourself.

Use `upload` only when `git` is not offered. Without a `github` input, GitHub import is unavailable: work from a local copy of the repository (clone it, or ask the user for one). Never put a GitHub URL in `upload`.

### GitHub

Take owner and name from the URL; without one, read the local checkout's `git remote get-url origin`, or ask.

**First GitHub import from a local checkout.** When you import a branch of a local checkout with `github` for the first time, check the checkout's `.figma/make`. If the scripts are missing and the project is not plain static HTML:

For Gallery-bound work when the current `publish_to_gallery` schema offers `upfrontReview`, finish preparation-only instruction lookup and obtain any required consent for local setup-file edits before reviewing the publication content. Defer every push in the following steps until the upfront content approval has been saved.


1. Call `send_code_to_figma` with only `fileKey`, and no `github`, `git` or `upload`, to get `nextStep.preparationInstructions`. This call only returns instructions; use them for the files in step 3.
2. Ask the user once whether you may add these setup files to their GitHub repository, explaining that they let Figma run the app.
3. If they agree, create the files those instructions describe, commit only those files and push them to the branch you will import on `origin`: the branch the user named, or else the checkout's current branch.
4. Import that branch with `github`. If the user declined or the push failed, Figma's agent adds the setup scripts after the import.

- Set `ref` when the user names a branch, tag or commit. When importing a local checkout, also set `ref` to its current branch if that is not the repository's default branch (`git ls-remote --symref origin HEAD`), so the import matches the pushed local code. Otherwise leave `ref` out.
- A standalone Code/Make takes neither `createLayer` nor `nodeId`.
- A Design file needs `github.createLayer: true` for a new code layer, or `github.nodeId` for an existing one, not a top-level `nodeId`. Take it from the link's `node-id`, replacing `-` with `:` (`38-6` becomes `"38:6"`).
- Calling again on a linked layer pulls `ref` (default: its current branch); a different `ref` switches the layer to that branch.
- Follow recovery instructions exactly, including waiting before a retry, and share the returned link.
- If GitHub import fails because Figma cannot read the repository (GitHub not connected, or the repository not found or not accessible) and a local checkout exists, do not stop at the connect or access recovery. When `git` is offered, ask in the same message whether to connect GitHub or grant access, which keeps the code linked, or send the local checkout with `git` now.

### git

1. Call `send_code_to_figma` with `git: { action: "open" }`. A standalone Code/Make takes neither `createLayer` nor `nodeId`; a Design file needs `git.createLayer: true` for a new code layer or `git.nodeId` for an existing one.
2. Run `git remote add figma <remote_url>` with `remote_url` exactly as returned; keep `origin`. Every command that talks to the `figma` remote, both `fetch` and `push`, needs the credential. Give it to each such command only, through a temporary credential helper: `git -c credential.helper= -c credential.helper='!f() { echo username=<username>; echo password=<password>; }; f' fetch figma`, and the same prefix for `push`. Never put the credential in a remote URL (`https://<username>:<password>@...`), git config, a file or a message to the user.
3. Commit the work to send. On a first push (no `base_sha`), first create the setup scripts that `nextStep.preparationInstructions` from `open` describes, so Figma can run the app. When `base_sha` is set, fetch `base_branch` and merge it into your branch: it holds Figma edits and setup fixes. Never force-push or rewrite it away.
4. Push to `push_branch` (for example `git push figma HEAD:main` with the credential helper), then call `nextStep.thenCall` to ingest. Ingest only after a successful push.
5. If ingest is rejected, follow its recovery: push first, or open again, fetch, merge and push. The credential expires at `expires_at`; open again to renew it. Share the returned link.

## 2. Follow the import response

Call `send_code_to_figma` with the selected local source and destination using its current schema. Follow the returned preparation and archive instructions; preserve the app and validate locally before uploading when instructed.

Follow each response's instructions and returned `nextStep` exactly for preparation, validation, upload, pending imports and setup recovery. Complete the returned prerequisites before advancing and pass complete continuation arguments unchanged. Do not invent a missing recovery step. When no `nextStep` is present, follow the response's instructions and the tool's current description.

If there is an approved Gallery continuation, finish it for the same preparation and report the confirmed published or draft outcome. Otherwise finish with the returned file/layer link and report only the import and preview outcomes established by the result. Report code-sync success separately if the later Gallery step fails.
