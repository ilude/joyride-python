---
mode: agent
model: GPT-4.1
tools: ["terminal", "file", "context7"]
description: "Complete Step 1: Foundation Types and Interfaces - Create basic types and minimal interfaces needed for the lifecycle system"
---

# Lifecycle Refactoring - Step 1: Foundation Types and Interfaces

You are implementing **Step 1** of the simplified lifecycle refactoring procedure that focuses on **real implementation first** with passing tests.

## YOUR TASK

Implement **Step 1: Foundation Types and Interfaces** from the Simplified Lifecycle Refactoring Procedure completely.

Refer to the [LIFECYCLE_REFACTORING_PROCEDURE.md](../.chat_planning/LIFECYCLE_REFACTORING_PROCEDURE.md) file for complete step details, code examples, and implementation requirements.

## CORE PRINCIPLES

1. **Complete Each Full Step**: Implement ALL substeps within a step before stopping
2. **Test-Driven**: Run `make test` after completing - tests MUST pass
3. **Real Implementation**: Build actual working components, avoid throwaway mocks
4. **Incremental Value**: Each step adds genuine working functionality
5. **Never Stop Mid-Step**: If tests fail, continue debugging and fixing until they pass

## STEP COMPLETION CRITERIA

A step is only complete when:
- ✅ All files specified in the step are created
- ✅ All code is implemented as documented
- ✅ All tests are written and functional
- ✅ `make test` runs successfully with no failures
- ✅ The implemented functionality works as intended

## COMMUNICATION PROTOCOL

After completing the step:
1. **Confirm completion**: "Step 1 completed successfully"
2. **Show test results**: Paste the `make test` output
3. **Ask for continuation**: "Should I proceed to Step 2?"

Begin implementation now. Do not stop until Step 1 is completely finished and `make test` passes.
