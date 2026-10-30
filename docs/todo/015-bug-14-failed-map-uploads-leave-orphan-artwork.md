### 14. Failed map uploads leave orphan artwork
- [ ] Open; static rollback finding in `web/admin/campaigns.py`, upload_map().
- Problem: later upload/DB failures lack cleanup after storing artwork; oversized
  accompanying walls are one trigger.
- Solution: track created files, clean failure/cancellation and recheck permission
  at commit; preserve documented partial-wall-import behavior.
- Test: oversized walls/injected DB failures leave neither map rows nor orphan
  files; successful imports retain their artwork.

