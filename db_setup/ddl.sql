
CREATE TABLE projects (
	id INTEGER NOT NULL, 
	name VARCHAR, 
	description VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id)
)

;

CREATE TABLE messages (
	id INTEGER NOT NULL, 
	project_id INTEGER, 
	role VARCHAR, 
	content TEXT, 
	timestamp DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

CREATE TABLE tasks (
	id INTEGER NOT NULL, 
	project_id INTEGER, 
	title VARCHAR, 
	description TEXT, 
	status VARCHAR, 
	assigned_to VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

CREATE TABLE team_members (
	id INTEGER NOT NULL, 
	role VARCHAR, 
	description TEXT, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (role)
)

;

CREATE TABLE task_comments (
	id INTEGER NOT NULL, 
	task_id INTEGER, 
	author VARCHAR, 
	content TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
)

;