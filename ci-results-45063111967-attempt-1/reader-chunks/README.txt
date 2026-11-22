CI evidence reading copy, format 1
Maximum file size: 4000 bytes. Original evidence is unchanged.
Read index-*.jsonl.txt in numeric order. Index pages may split a JSON line; concatenate before parsing.
Each file-NNNNNN/metadata.json names the original relative path, encoding, byte count, SHA-256 and part count.
Read part-NNNNNN.txt files in numeric order. Concatenate bytes without adding or removing newlines.
UTF-8 parts never split a code point; lines/XML elements may span parts. Parts are fragments, not standalone XML.
For base64 encoding, concatenate all parts, then base64-decode to recover the original bytes.
Empty originals have zero parts and reconstruct to empty bytes.
Concatenate hashes-*.txt in numeric order for part filename, byte count and SHA-256 records.
Verify reconstructed bytes against metadata.json.
Local verification: python3 tools/chunk_ci_evidence.py --verify EVIDENCE_DIRECTORY
The connector threshold is unknown; 4000 bytes is a conservative target, not a guaranteed connector contract.
