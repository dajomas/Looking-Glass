DBID=$(gh run list --repo dajomas/Looking-Glass --workflow integration-tests.yml --branch features/perplexity --limit 1 --json databaseId,headSha,status,conclusion,url | jq ".[].databaseId")

gh run download ${DBID} \
  --repo dajomas/Looking-Glass \
  --dir ci-results-${DBID}

git add ci-results-${DBID}
git commit -m "Add CI results for run ${DBID}"
git push origin features/perplexity