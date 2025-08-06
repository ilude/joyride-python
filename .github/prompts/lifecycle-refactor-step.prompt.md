---
mode: agent
model: gpt-4
tools: ["terminal", "file"]
description: "Complete lifecycle refactoring steps using convention over configuration"
---

# Lifecycle Refactoring Step Implementation

You are implementing a simplified lifecycle refactoring procedure for the **Joyride DNS Service lifecycle management system** that focuses on **real implementation first** with passing tests at every step.

## CRITICAL: UNDERSTAND THE CONTEXT

This is NOT about creating a Flask app. This is about refactoring the lifecycle management system for the Joyride DNS Service project. You are implementing the components that manage the startup, shutdown, and health monitoring of DNS service components.

## CONVENTION OVER CONFIGURATION

This prompt automatically determines the step number from commands like:
- "complete lifecycle refactoring step 1"
- "complete lifecycle refactoring step 4" 
- "complete lifecycle refactoring step 9"

The prompt will:
1. Extract the step number from the user's command
2. Reference the appropriate procedure file: `.chat_planning/LIFECYCLE_REFACTORING_PROCEDURE.md`
3. Implement the specified step completely
4. Create lifecycle management components under `app/joyride/injection/lifecycle/`

## CORE PRINCIPLES

1. **Complete Each Full Step**: Implement ALL substeps within a step before stopping
2. **Test-Driven**: Run `make test` after completing each full step - tests MUST pass
3. **Real Implementation**: Build actual working lifecycle components, avoid throwaway mocks
4. **Incremental Value**: Each step adds genuine working lifecycle functionality
5. **Never Stop Mid-Step**: If tests fail, continue debugging and fixing until they pass

## YOUR TASK

Based on the user's command, determine which step to implement from the Simplified Lifecycle Refactoring Procedure.

**MANDATORY**: Read the LIFECYCLE_REFACTORING_PROCEDURE.md file from .chat_planning/ directory FIRST to understand what you're implementing.

The procedure creates a new lifecycle management system with these components:
- `app/joyride/injection/lifecycle/types.py` - Core enums and exceptions
- `app/joyride/injection/lifecycle/interfaces.py` - Protocol definitions
- `app/joyride/injection/lifecycle/component.py` - Base component classes
- `app/joyride/injection/lifecycle/registry.py` - Component registry
- `app/joyride/injection/lifecycle/orchestrator.py` - Startup/shutdown coordination
- `tests/lifecycle/` - Comprehensive test suite

## STEP COMPLETION CRITERIA

A step is only complete when:
- ✅ All files specified in the step are created with EXACT code from procedure
- ✅ All code is implemented exactly as documented in LIFECYCLE_REFACTORING_PROCEDURE.md
- ✅ All tests are written and functional as specified
- ✅ `make test` runs successfully with no failures
- ✅ The implemented lifecycle functionality works as intended

## DEBUGGING GUIDELINES

If tests fail:
1. **Analyze the error** - understand what's broken
2. **Fix the implementation** - don't change test expectations unless clearly wrong
3. **Re-run tests** - verify the fix works
4. **Continue until green** - don't stop until `make test` passes

**COMMON MISTAKES TO AVOID:**
- Creating Flask app files instead of lifecycle components
- Misunderstanding the target directory structure
- Implementing wrong functionality (web app vs lifecycle management)
- Not following the exact code examples from the procedure
- Creating files in wrong locations

If you get stuck:
- Review the step requirements carefully in LIFECYCLE_REFACTORING_PROCEDURE.md
- Check for typos, import errors, or missing dependencies
- Ensure file paths and module structures match the procedure exactly
- Verify test isolation and proper setup/teardown
- Remember: you're building lifecycle management, not a web application

## IMPLEMENTATION CHECKLIST

Before starting, verify you understand:
- [ ] This is lifecycle management system refactoring
- [ ] Target directory is `app/joyride/injection/lifecycle/`
- [ ] Tests go in `tests/lifecycle/` directory  
- [ ] You are implementing component lifecycle management
- [ ] Step 1 creates `types.py`, `interfaces.py`, and `test_types.py`

## COMMUNICATION PROTOCOL

After completing each full step:
1. **Confirm completion**: "Step [X] completed successfully" 
2. **Show test results**: Paste the `make test` output
3. **Ask for continuation**: "Should I proceed to the next step?"

Do NOT ask for permission to continue within a step - complete it fully first.

## AUTOMATIC STEP DETECTION

Parse the user's command to extract the step number:
- Extract number from phrases like "step 1", "step 4", "step 9"
- If no step number found, ask the user to specify which step
- Validate step number is between 1-9
- Reference the corresponding section in LIFECYCLE_REFACTORING_PROCEDURE.md

## FINAL REMINDERS

- **This is NOT a Flask app** - you're building lifecycle management components
- **Read the procedure file first** - understand what you're implementing
- **Follow exact code examples** - don't improvise or create different functionality
- **Test directory structure** - create `tests/lifecycle/` subdirectory  
- **Complete steps fully** - don't stop until tests pass for the current step

Begin implementation now. Parse the user's command, determine the step number, read the LIFECYCLE_REFACTORING_PROCEDURE.md file, and implement that step completely until `make test` passes.
