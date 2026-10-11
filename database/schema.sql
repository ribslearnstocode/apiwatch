-- APIWatch PostgreSQL schema. Generated from the SQLAlchemy models.
BEGIN;


CREATE TABLE monitors (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	url VARCHAR(2048) NOT NULL, 
	check_interval INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (check_interval BETWEEN 30 AND 86400), 
	UNIQUE (url)
)

;


CREATE TABLE incidents (
	id SERIAL NOT NULL, 
	monitor_id INTEGER NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	description VARCHAR(500) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (resolved_at IS NULL OR resolved_at >= started_at), 
	FOREIGN KEY(monitor_id) REFERENCES monitors (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_incidents_monitor_time ON incidents (monitor_id, started_at);

CREATE UNIQUE INDEX uq_open_incident ON incidents (monitor_id) WHERE resolved_at IS NULL;


CREATE TABLE monitor_results (
	id SERIAL NOT NULL, 
	monitor_id INTEGER NOT NULL, 
	status_code INTEGER, 
	response_time_ms FLOAT NOT NULL, 
	is_success BOOLEAN NOT NULL, 
	error_message VARCHAR(500), 
	checked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (response_time_ms >= 0), 
	FOREIGN KEY(monitor_id) REFERENCES monitors (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_results_monitor_time ON monitor_results (monitor_id, checked_at);

COMMIT;