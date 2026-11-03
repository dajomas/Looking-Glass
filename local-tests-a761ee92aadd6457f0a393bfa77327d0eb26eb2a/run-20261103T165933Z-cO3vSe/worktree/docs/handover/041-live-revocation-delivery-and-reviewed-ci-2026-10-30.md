## Live revocation delivery and reviewed CI (2026-10-30)

Increment 4 was delivered at ac8a77f5396531e6cf7a7b1db48ec39baf848344.
It adds four real Chromium/live-server cases for shared-session logout, campaign
assignment removal, deactivation and role change. Affected sockets must close
4403; independent old-cookie state/image requests must receive 401 or 404, while
an unaffected session/account receives pixel-verified hide/undo updates. Extra
synthetic accounts preserve existing fixture IDs, and extra revocation contexts
collect errors/failure traces/screenshots plus token-free status observations.
No runtime authorization, workflow or collector changes were made. The original
approved write omitted HANDOVER despite its summary; this section records that
previously missing handover rather than claiming it was included at delivery.

Run 41029015169 tested that implementation commit; evidence was reviewed at
97e5a628f136b2ff1102f074009bbc6f530f0c3c. All 11 live cases, including the four new
revocation cases, passed. Python / HTTP, JavaScript and Recovery jobs were green;
Browser / mocked HTTP reported 161 passed and one wall-width NaN failure. This
validates the specified live scenarios, not the whole workflow, idle/multi-worker
revocation or every race. Previously delivered pixels cannot be recalled and no
new blank-screen product requirement was introduced. The post-image-store DB
failure/orphan gap and broader backlog remain open. Earlier preparation-time
pending statements above are historical and do not override these reviewed results.

