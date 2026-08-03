# Service layer

## Core backend services

### AuthService
- register(email, password, name)
- login(email, password)
- refresh_token(refresh_token)
- logout(user_id)
- verify_credentials()

### ProjectService
- create_project(payload, user)
- update_project(project_id, payload, user)
- share_project(project_id, user_ids, role)
- archive_project(project_id, user)

### CADService
- create_sketch(project_id, payload, user)
- update_sketch(sketch_id, payload, user)
- extrude_sketch(sketch_id, payload, user)
- export_model(body_id, format, user)

### PCBService
- create_board(project_id, payload, user)
- place_component(board_id, payload, user)
- run_drc(board_id, user)
- generate_bom(board_id, user)

### FileService
- upload_file(project_id, file, user)
- download_file(file_id, user)
- delete_file(file_id, user)
- version_file(file_id, user)

### AIOrchestratorService
- process_user_request(request, user, project_context)
- classify_intent(request)
- invoke_agent(agent_name, task, context)
- stream_response(chat_id, message)

## Error handling contract

- Validation errors return 400 and a problem detail payload.
- Permission failures return 403.
- Missing resources return 404.
- Infrastructure failures return 502 or 503 with a correlation ID.
- All services emit audit events for state changes.

## Background job pattern

- CPU-bound work is handled by Celery workers.
- APIs create jobs and return task ids.
- Workers update status in Redis and publish result events.
