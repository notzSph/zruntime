# Routine coding

Use this path for a predictable, localized change with a known implementation and a cheap way to verify it. Examples include correcting a label, fixing a contained conditional, or updating a small helper with clear existing tests.

## Keep it root-only by default

Before editing, check the working tree, locate the behavior and its nearest caller, and identify the expected result. Keep ownership in the root session when implementation and verification are one short, serial workstream. Delegation is justified only when a separate read-only lookup, independent file change, or check can return useful work without sharing the same edit surface.

If delegating, use one worker with an exact file boundary, acceptance condition, and concise deliverable. Do not send a child merely to restate the requested change. Avoid an Astra review for a low-risk contained edit; escalate when inspection reveals security, compatibility, data integrity, or broader architectural impact.

## Complete the change

1. Read the target code and the nearest established pattern. Confirm whether the working tree already contains user changes in the same area.
2. Make the smallest complete change. Keep formatting consistent and avoid unrelated cleanup.
3. Run the narrowest check that exercises the altered behavior. If no suitable check exists, inspect the changed path manually and state that automated verification was unavailable.
4. Review the diff for accidental scope, changed interfaces, and error paths. Do not report success based only on a command starting; confirm its exit status and relevant output.
5. Summarize the change and exact verification result. Call out any follow-up that became necessary.

Do not use this workflow for schema changes, cross-service work, unclear bugs, security boundaries, or irreversible external effects. Move those tasks to [complex repository work](complex-repo-work.md).

Keep model choices local to the session. The Plus package defaults to maximum root thinking, but a lower supported session-level setting may be appropriate for a genuinely routine task. Do not change shared Gateway defaults for one task, and do not assume an override persists or resets without checking the active runtime.
