# AI Ops Assistant deployment troubleshooting — interview preparation

**Project:** Enterprise IT Operations Automation Platform  
**Repository:** [utkarshstudent75-gif/entreprise-IT-Operations-automation-platform](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform)

## The situation

I deployed an AI Ops Assistant built around a browser UI, backend API, Azure Functions, and a Microsoft Foundry agent. The infrastructure and services came up, but the first end-to-end production experience was not healthy: the public assistant page loaded while its live alert stream could not fetch data, and chat requests exposed integration mismatches between the backend and the configured Foundry agent. This was a layered integration problem, not one infrastructure outage.

## My troubleshooting approach

I traced the request from the user interface through the API to the model/tool layer, using the actual failing boundary and response as evidence. I avoided changing several layers at once.

### 1. UI could load, but browser API requests failed

**Symptom:** The deployed public UI was visible, but its live alert stream reported a fetch failure.

**Investigation:** Since the page itself loaded, I separated static hosting from browser-to-API connectivity. The assistant API's CORS allowlist did not contain the exact origin serving the deployed UI.

**Fix:** I added the reported Static Web Apps origin to the allowlist while retaining the previous origin for compatibility. This restored the browser's ability to call the API without broadly opening cross-origin access.

**Evidence:** [PR #22 — allow deployed assistant site origin](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/22) says the UI loaded and its alert stream failed due to the missing origin. It was merged on October 2, 2026.

### 2. Foundry rejected the chat input

**Symptom:** Production chat returned a Foundry HTTP 400 invalid input item error.

**Investigation:** Azure identity and agent permissions had already been verified, so I narrowed the fault to request shape rather than credentials or RBAC. The Responses API input items sent to the named Foundry agent were missing the required message type discriminator.

**Fix:** I added the required message type to the developer and conversation items. The PR records that runtime verification would occur after the normal backend build and deployment, so I would describe the code fix as merged, while confirming the post-deploy result separately if asked.

**Evidence:** [PR #25 — fix Foundry Responses message input types](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/25).

### 3. Function tools were configured at the wrong layer

**Symptom:** The named Foundry agent's function-tool flow did not match the request-level tool configuration being sent by the backend.

**Investigation:** I checked how the named agent endpoint obtains its tools. Its function schemas belong to the persisted agent version; sending tools and tool_choice with each request was the wrong configuration boundary.

**Fix:** I removed the request-level tools fields and added a Cloud Shell script to preserve the existing model and instructions, attach the backend's five function schemas to a new agent version, and verify that version. This made the deployment steps explicit: deploy the backend change, configure/version the Foundry agent, verify the tool list, then retry chat.

**Evidence:** [PR #24 — fix Foundry assistant function tool calls](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/24). Its description says no tests were run; avoid claiming that this specific fix was proven by automated tests.

## Result and how to state it accurately

The deployment issues were isolated and addressed at the layer where each failure occurred: exact browser origin in CORS, request schema for Foundry messages, and persistent agent-version configuration for function tools. The project history shows these fixes were merged and records a successful deployment before the CORS-origin issue was reported. For the Foundry fixes, the PR descriptions note that live runtime verification followed the normal deployment; verify the current live behavior yourself before claiming a fully successful end-to-end outcome or quoting metrics.

The assistant's tools are designed to be read-only diagnostics. The repository documentation describes inventory, health, metrics, and bounded Log Analytics queries. That constrained tool design is relevant: troubleshooting the deployment did not require granting the assistant write access to production resources.

## 90-second interview answer

> “I deployed an AI Ops Assistant with a static web UI, an API, Azure Functions, and a Microsoft Foundry agent. The infrastructure was running, but the end-to-end experience failed in more than one place: the UI loaded but its alert stream could not reach the API, and chat requests were rejected or could not invoke the expected functions.
>
> “I debugged it hop by hop. First I used the fact that the page itself loaded to separate frontend hosting from API access. The browser error pointed to cross-origin access, and I found that the API allowlist was missing the exact deployed Static Web Apps origin. I added that origin while preserving the earlier one.
>
> “Then I investigated the Foundry 400 separately. We had already verified identity and permissions, so I focused on the request contract and found that message inputs were missing the required type field. I also found that the named agent's function schemas had to be configured on its persisted version, not attached to each request. I corrected the input shape and made agent version setup an explicit, verifiable deployment step.
>
> “My general method was to identify the failing boundary, use logs and response codes to distinguish networking, authentication, and API-contract problems, verify which system owns each configuration, and change one layer at a time. I also kept the assistant's Azure tools read-only. I would close by checking the deployed version end to end rather than assuming a merged fix alone proves production recovery.”

## Explain your line of thought

- Start at the observed failure: did the page fail to load, did the browser request fail, did the API return an error, or did the model/tool call fail?
- Use the exact response and logs to narrow the layer. A loaded page plus a failed fetch points away from static hosting; HTTP 400 suggests request contract; 401/403 would direct attention to auth and permissions.
- Verify what has already been ruled out. In the Foundry input incident, identity and permissions were already checked, so the next useful test was request shape.
- Identify the owning configuration boundary. Browser origins belong in API CORS policy; named-agent tools belong on the persisted agent version; message item types belong in the request payload.
- Make the smallest scoped fix, preserving prior valid configuration and least privilege.
- Verify after deployment at the same boundary that failed, and distinguish a merged change from a confirmed live recovery.

## Follow-up questions

**How did you know it was CORS and not an API outage?**  
The deployed page loaded, while the browser's alert-stream fetch failed. The deployment report identified the missing deployed site origin in the API allowlist. I fixed that exact origin and retained the earlier one.

**Why did you check permissions before changing the Foundry request?**  
Because a 400 invalid-input response points to a malformed request, and the PR records that identity and permissions had already been verified. I used that evidence to avoid changing RBAC unnecessarily.

**What did you learn about Foundry tool configuration?**  
For this named-agent endpoint, tools are part of the persisted agent version. The backend should invoke that configured agent instead of trying to redefine its tools on every request.

**How did you avoid overstating the result?**  
I would say the fixes were merged and cite the deployment evidence. Where the PR says runtime verification was still pending after deployment, I would confirm the live result before claiming complete recovery or an uptime improvement.

## Source links

- [PR #22 — deployed assistant site origin / CORS](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/22)
- [PR #25 — Foundry message input schema](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/25)
- [PR #24 — Foundry persisted function tools](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/24)
- [PR #17 — AI Ops Assistant tools and deployment notes](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/pull/17)
- [Project README — AI Ops Assistant architecture and setup](https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform/blob/master/README.md)
