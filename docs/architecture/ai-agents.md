# AI agent definitions

> **Implementation status:** the system described below is real and tested
> as of Step 3 — see `services/backend/app/ai/`. Two differences from this
> original design: agents run understand → plan → execute → output (no
> execute↔review loop-back — an LLM-judged "is this acceptable?" gate is
> exactly the kind of condition that can silently never trigger and loop
> forever, so it was cut in favor of a bounded, finite pass), and a 10th
> agent, `ComponentRecommendationAgent`, was added
> (`app/ai/agents/definitions.py`). Tool names in code are close but not
> always identical to the catalog below — `app/ai/tools/*_tools.py` is
> authoritative.

## Agent catalog

### PlannerAgent
- Responsibility: understand the user intent and decompose requests into subtasks.
- Inputs: user prompt, project context, chat history.
- Outputs: ordered subtasks, target agent, required tools.
- State graph nodes: understand, plan, route, review.

### MechanicalCADAgent
- Responsibility: create or modify CAD geometry from natural language.
- Tools: create_sketch, extrude, fillet, mirror, pattern, export_step.
- Memory: stores previous design choices and parameter defaults.

### PCBDesignAgent
- Responsibility: place components, suggest routing, and critique layouts.
- Tools: place_component, route_trace, run_drc, generate_bom.
- Memory: stores placement conventions and project-specific constraints.

### ElectronicsAgent
- Responsibility: review circuits and suggest compatible components.
- Tools: search_datasheets, search_standards, compare_components.

### SimulationAgent
- Responsibility: dispatch simulations for FEA, SPICE, or thermal analysis.
- Tools: run_simulation, fetch_results, publish_report.

### FirmwareAgent
- Responsibility: generate board support packages, firmware stubs, and embedded code.
- Tools: generate_code, validate_build, fetch_hal_examples.

### ManufacturingAgent
- Responsibility: evaluate cost, material, and fabrication feasibility.
- Tools: estimate_cost, check_manufacturability, create_mfg_notes.

### DesignReviewAgent
- Responsibility: assess quality, safety, compliance, and design completeness.
- Tools: run_checks, compare_to_template, summarize_findings.

### DocumentationAgent
- Responsibility: create release notes, BOM summaries, and design rationale.
- Tools: generate_docs, summarize_changes, create_export_bundle.

## Agent execution model

Each agent is implemented as a LangGraph state graph with the following standard stages:
1. understand the request
2. plan the execution
3. execute tools
4. review results
5. emit a structured artifact or response
