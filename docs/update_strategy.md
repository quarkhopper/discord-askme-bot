# Definitive Strategy for Document Edits (Improved)

## 1. Absolute Memory Refresh
- Immediately discard **all previously stored information** related to any document whenever it is newly uploaded.
- Always fully reload and explicitly verify the contents of the uploaded file before modifications.

## 2. Explicitly Scoped Edits
- Edits must target only one clearly defined section or subsection at a time.
- Do not regenerate the entire document unless explicitly required and verified against the latest upload.
- Always explicitly refer to the uploaded source file; never rely solely on memory.

### Example of Correct Scoped Edit:
```json
{"updates":[{"pattern":"@SUBSECTION\[2\.1\] File Structure.*?@END","multiple":false,"replacement":"@SUBSECTION[2.1] File Structure\n@PRE\n<updated file structure here>\n@ENDPRE\n@END"}]}
```

### What to Avoid (Incorrect Example):
```json
{"updates":[{"pattern":".*","multiple":true,"replacement":"<regenerated entire document>"}]}
```

## 3. Explicit Section Verification
- Before modification:
  - Explicitly verify and enumerate every section and subsection present in the uploaded document.
- After modification, immediately re-verify:
  - All sections and subsections still exist.
  - No unintended edits have occurred.

## 3. Recovery and Correction Procedure
- If any section or subsection is discovered missing after an edit:
  - Halt all editing immediately.
  - Fully restore the original content from the uploaded document.
  - Re-verify the document explicitly against the original uploaded document.

## 4. Continuous Integrity Checks
- Perform explicit integrity checks between each step of the modification process.
- Always explicitly compare the current state to the uploaded original.

## 4. Final Checks
- Before confirming any completed edits:
  - Explicitly list all major sections and subsections.
  - Confirm their presence and integrity against the source document.

Adopting this strict approach ensures document integrity, prevents accidental data loss, and maintains editing accuracy.
## Explicit Handling of Regex Patterns (Lessons Learned)

### Issue Encountered:
- Regex pattern matching during document updates occasionally failed or led to unintended document modifications.

### Lessons Learned:
- Always explicitly test and confirm regex patterns on smaller text samples before applying them to entire documents.
- Explicitly specify regex boundaries clearly to match exactly the intended sections/subsections only.
- Avoid overly broad or greedy patterns (e.g., .* without proper limits), as these can unintentionally remove or alter large portions of text.

### Recommended Best Practices:
- Explicitly use non-greedy quantifiers (.*?), when matching section/subsection content.
- Explicitly anchor patterns clearly with lookahead assertions such as (?=@SECTION|\@SUBSECTION|\Z) to precisely limit matches.
- After applying regex substitutions, explicitly verify immediately that the intended changes occurred without side effects.

### Explicitly Verified Example Pattern:
```regex
(@SUBSECTION\[2\.1\] File Structure).*?(?=@SUBSECTION|@SECTION|\Z)
```

Applying these explicit lessons learned improves reliability and accuracy during updates.
