## Assistant workflow and user preferences

The user prefers direct technical explanations, complete working changes, reproducible commands, incremental validation and candid limitations. Use the live features/perplexity branch as the target unless the user changes that instruction.

In this Perplexity environment the GitHub connector exposed file reads, single-file create/update and multi-file commits. Tool availability and authentication can change in a new session; rediscover them rather than assuming access.

Before an external write, resolve the repository, branch and current file contents, prepare exact file contents and commit message, and obtain the required action confirmation. For an existing single-file update, obtain its blob SHA from the target branch. Execute only the approved write. Do not assume a general branch instruction authorizes arbitrary future changes.

After a successful commit, report its actual SHA and changed paths. Do not claim a push succeeded merely because a draft or confirmation was prepared. Test code changes where execution is available; otherwise explicitly distinguish review from execution.

