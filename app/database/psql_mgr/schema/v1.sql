create type access_levels as enum('ADMIN', 'USER');
create type storage_status as enum('AVAILABLE', 'DELETED', 'NEVER_EXISTED');
create type account_type as enum('ASSET', 'EXPENSE', 'INCOME', 'EQUITY', 'LIABILITY', 'DIVIDEND', 'INCOME_SUMMARY');
create type account_actions as enum('DEBIT', 'CREDIT');

create table person (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp(),
  created_by VARCHAR(32) DEFAULT current_user(),
  email TEXT NOT NULL,
  hashed_password CHAR(88),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  level access_levels DEFAULT 'USER',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  confirmed BOOLEAN NOT NULL DEFAULT FALSE
);

create table entity(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp(),
  created_by VARCHAR(32) DEFAULT current_user(),
  name TEXT UNIQUE NOT NULL
);

create table person_entity_junction(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES person(id),
  entity_id UUID REFERENCES entity(id),
  UNIQUE(user_id, entity_id)
);

create table account(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp() NOT NULL,
  created_by VARCHAR(32) DEFAULT current_user(),
  entity_id UUID REFERENCES entity(id),
  name TEXT UNIQUE NOT NULL,
  parent_account_id UUID,
  type account_type,
  archived BOOLEAN DEFAULT 'FALSE',
  UNIQUE(id, type)
);
ALTER TABLE account ADD CONSTRAINT loop_back_fkey FOREIGN KEY(parent_account_id) REFERENCES account(id);

create table journal(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp() NOT NULL,
  timestamp DATE NOT NULL,
  created_by UUID REFERENCES person(id),
  entity_id UUID REFERENCES entity(id),
  vendor TEXT,
  description TEXT NOT NULL,
  closing_entry BOOLEAN DEFAULT FALSE,
  receipt_status storage_status NOT NULL DEFAULT 'NEVER_EXISTED',
  valid BOOLEAN NOT NULL DEFAULT FALSE
 );

create table ledger(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp() NOT NULL,
  created_by VARCHAR(32) DEFAULT current_user(),
  journal_id UUID REFERENCES journal(id),
  account_id UUID NOT NULL REFERENCES account(id),
  amount NUMERIC(11,2) NOT NULL,
  direction account_actions NOT NULL,
  reconciled BOOLEAN NOT NULL DEFAULT 'FALSE'
);

create table prepaid(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_on TIMESTAMP DEFAULT localtimestamp() NOT NULL,
  created_by VARCHAR(32) DEFAULT current_user(),
  amount NUMERIC(2) NOT NULL,
  receive_month DATE NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT 'FALSE',
  original_journal_id UUID REFERENCES journal(id),
  asset_account_id UUID NOT NULL,
  expense_account_id UUID NOT NULL,
  asset_account_type account_type NOT NULL,
  expense_account_type account_type NOT NULL,
  FOREIGN KEY (asset_account_id, asset_account_type) REFERENCES account(id, type),
  FOREIGN KEY (expense_account_id, expense_account_type) REFERENCES account(id, type),
  CHECK (asset_account_type = 'ASSET'),
  CHECK (expense_account_type = 'EXPENSE')
);
