## File import feedback (items 7–8 patch)

Native file-upload forms (map import, image replacement, backup inspection and
restore) now immediately show “Uploading and processing files… Please wait” and
mark their submit controls busy. Repeated clicks and Enter/requestSubmit events
on the same pending form are blocked. File fields, CSRF tokens and named submitter
values remain included in the request. Returning through browser history clears
the pending UI so the form can be used again.

JavaScript-managed imports keep their own lifecycle: batch imports retain per-file
counts and filenames; saved wall sources show uploading/processing feedback; room
note imports show an immediate importing message and restore the submit control
on completion/error. Status regions expose busy feedback to assistive technology.
This is indeterminate activity feedback, not a byte-progress percentage or an
estimate of server processing time.

Wait for completion rather than reloading. If the connection fails and the result
is uncertain, inspect the campaign before retrying. This is browser-side repeat
submission protection, not server-side idempotency: another tab, a reload, direct
API requests, disabled JavaScript or direct form.submit() can still issue requests.

