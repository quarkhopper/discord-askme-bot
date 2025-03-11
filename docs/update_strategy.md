# Document Update Strategy for COML-Based Guidelines

## 1. **Ensuring a Complete Memory Refresh**
To prevent discrepancies when updating documents, we must implement a **strict process** for refreshing cached content. The following steps must be followed **every time a document is uploaded**:

### **1.1 Full Memory Refresh on Upload**
- Immediately discard all cached knowledge about previous versions of the document.
- Fully reload the **latest uploaded document** before performing any modifications.
- Extract and verify the document’s **section headers** to ensure completeness.

### **1.2 Hard Verification of Canvas Content**
- After applying an update, the **entire document must be checked against the uploaded version**.
- Compare all section headers between the **uploaded file** and the **canvas document** before confirming success.
- If any discrepancies exist, halt all modifications and **restore missing content first**.


## 2. **Handling Missing Sections and Data Drift**
One of the most severe issues we've encountered is the **gradual loss of sections** as edits are made. This can happen due to unintended truncation during partial updates. To prevent this, the following rules apply:

### **2.1 Always Verify the Full Structure Before Editing**
- Extract a **full list of section headers** before making any modifications.
- Ensure that **all major sections and subsections** are present before proceeding.
- If any sections are missing, halt modifications and **restore the missing data first**.

### **2.2 Preventing Partial Loss of Sections**
- **Edits must always be scoped to specific sections.**
  - If modifying a section, only update that section **without affecting others**.
  - Do not overwrite the entire document unless performing a full refresh.
- **Compare against the previous structure before saving updates.**
- Ensure that **updates are non-destructive**—if a section was there before, it must still be there after.


## 3. **Verification Before and After Any Modification**
A rigorous **pre-edit and post-edit verification** process is required to prevent repeated loss of sections.

### **3.1 Pre-Edit Checklist**
Before modifying any document:
1. **Extract all section headers** and compare them with the latest uploaded version.
2. Ensure that all expected sections are present.
3. Verify if any sections were **partially truncated** in previous edits.

### **3.2 Post-Edit Checklist**
After making modifications:
1. **Re-check section headers** to confirm that no sections were lost.
2. Compare the document structure **before and after** the update.
3. Ensure that no unintended modifications were made outside the intended section.
4. If discrepancies exist, **immediately restore missing sections** before continuing.


## 4. **Addressing Specific Problems Encountered**
### **4.1 Case Study: Section 5 Was Missing, Now Sections 3 and 4 Are Gone**
- **Cause:** The update unintentionally replaced too large a portion of the document, removing sections that should have remained.
- **Fix:** Implement **section-by-section updates** rather than overwriting large portions of the document.
- **Prevention:** Apply the pre-edit and post-edit **verification steps** to catch these issues immediately.


## 5. **Final Best Practices**
- **Always work from the most recent uploaded document.**
- **Do not assume previous modifications were successful—verify them every time.**
- **Updates must be precise—modify only what is necessary, and never overwrite other sections.**
- **Any time a section is missing, stop and restore before proceeding.**

By following this strategy, we ensure that updates are **accurate, lossless, and structured**, preventing errors from accumulating over multiple iterations.

