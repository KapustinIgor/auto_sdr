CREATE TABLE IF NOT EXISTS accounts (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT UNIQUE NOT NULL,
  industry TEXT,
  geo TEXT,
  employee_range TEXT,
  revenue_range TEXT,
  icp_fit BOOLEAN DEFAULT FALSE,
  score FLOAT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contacts (
  id SERIAL PRIMARY KEY,
  account_id INT REFERENCES accounts(id),
  name TEXT,
  title TEXT,
  email TEXT UNIQUE,
  linkedin_url TEXT,
  persona TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS signals (
  id SERIAL PRIMARY KEY,
  account_id INT REFERENCES accounts(id),
  feature_key TEXT,
  feature_value TEXT,
  score_delta FLOAT,
  evidence_url TEXT,
  evidence_snippet TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_briefs (
  id SERIAL PRIMARY KEY,
  account_id INT REFERENCES accounts(id),
  brief_json JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
  id SERIAL PRIMARY KEY,
  contact_id INT REFERENCES contacts(id),
  account_id INT REFERENCES accounts(id),
  channel TEXT,
  step TEXT,
  subject TEXT,
  body TEXT,
  status TEXT,
  version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approvals (
  id SERIAL PRIMARY KEY,
  message_id INT REFERENCES messages(id),
  reviewer TEXT,
  status TEXT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS touches (
  id SERIAL PRIMARY KEY,
  message_id INT REFERENCES messages(id),
  sent_at TIMESTAMP DEFAULT NOW(),
  provider_msg_id TEXT,
  status TEXT,
  bounce_reason TEXT
);

CREATE TABLE IF NOT EXISTS replies (
  id SERIAL PRIMARY KEY,
  contact_id INT REFERENCES contacts(id),
  account_id INT REFERENCES accounts(id),
  received_at TIMESTAMP DEFAULT NOW(),
  raw_body TEXT,
  classification_json JSONB
);

CREATE TABLE IF NOT EXISTS workflows (
  id SERIAL PRIMARY KEY,
  account_id INT REFERENCES accounts(id),
  contact_id INT REFERENCES contacts(id),
  state TEXT,
  next_action_at TIMESTAMP,
  metadata_json JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppression_list (
  email_or_domain TEXT PRIMARY KEY,
  reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  actor TEXT,
  action TEXT,
  entity_type TEXT,
  entity_id TEXT,
  payload_json JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
