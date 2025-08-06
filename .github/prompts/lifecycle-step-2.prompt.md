---
mode: edit
model: clude sonnet 4
tools: ["terminal", "file", "context7", "code", "chat_planning", "chat", 'runTests']
description: "Complete Step 2: Simple Component Implementation - Create working component classes that can be used immediately"
---

# Lifecycle Refactoring - Step 2: Simple Component Implementation

You are implementing **Step 2** of the simplified lifecycle refactoring procedure that focuses on **real implementation first** with passing tests.

## YOUR TASK

Implement **Step 2: Simple Component Implementation** from the Simplified Lifecycle Refactoring Procedure completely.

Refer to the [LIFECYCLE_REFACTORING_PROCEDURE.md](../.chat_planning/LIFECYCLE_REFACTORING_PROCEDURE.md) file for complete step details, code examples, and implementation requirements.

## STEP 2 OVERVIEW

**Goal**: Create a working component class that can be used immediately. Please continue working until you have completed the work specified.
DO NOT STOP TO TELL ME WHAT YOU ARE GOING TO DO!!! ** JUST DO IT!!! **

**Files to create**:
- `app/joyride/injection/lifecycle/component.py` - Base component implementation with Component, StartableComponent, and HealthCheckableComponent classes
- `tests/lifecycle/test_component.py` - Comprehensive tests for all component classes

**Key Requirements**:
- Implement Component base class with dependency management
- Implement StartableComponent with start/stop lifecycle
- Implement HealthCheckableComponent with health checking
- All components must use state transitions with validation
- Include timing metrics for startup/shutdown
- Support custom start/stop logic via _do_start/_do_stop methods
- Include comprehensive async tests

## CORE PRINCIPLES

1. **Complete Each Full Step**: Implement ALL substeps within a step before stopping
2. **Test-Driven**: Run `make test` after completing - tests MUST pass
3. **Real Implementation**: Build actual working components, avoid throwaway mocks
4. **Incremental Value**: Each step adds genuine working functionality
5. **Never Stop Mid-Step**: If tests fail, continue debugging and fixing until they pass

## STEP COMPLETION CRITERIA

A step is only complete when:
- ✅ All files specified in the step are created
- ✅ All code is implemented as documented in the procedure
- ✅ All tests are written and functional
- ✅ `make test` runs successfully with no failures
- ✅ The implemented functionality works as intended
- ✅ The step is marked complete in LIFECYCLE_REFACTORING_PROCEDURE.md

## COMMUNICATION PROTOCOL

After completing the step:
1. **Confirm completion**: "Step 2 completed successfully"
2. **Show test results**: Paste the `make test` output
3. **Update procedure**: Mark Step 2 as completed in the procedure document
4. **Ask for continuation**: "Should I proceed to Step 3?"

Begin implementation now. Do not stop until Step 2 is completely finished and `make test` passes.
